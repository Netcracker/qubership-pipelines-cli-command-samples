import json
import os
import re
import signal
import subprocess
from pathlib import Path

from qubership_pipelines_common_library.v1.execution.exec_command import ExecutionCommand

ENVGENE_PYTHON = "/module/venv/bin/python"
ENVGENE_ORCHESTRATOR = "/module/scripts/pipeline/orchestrator.py"


class EnvGeneRunCommand(ExecutionCommand):

    def _validate(self):
        names = [
            "paths.input.params",
            "paths.output.params",
            "paths.input.files",
            "params.env_names",
            "params.git.host",
            "params.git.repository",
            "params.git.ref_name",
            "git_token",
        ]
        if not self.context.validate(names):
            return False

        try:
            self.repo_path = self._resolve_repo_path()
            self.sha = self._head_sha()
        except Exception as exc:
            self.context.logger.error(str(exc))
            return False

        self.envgene_vars = self.context.input_param_get("params.envgene_vars", {}) or {}
        self.git_params = self.context.input_param_get("params.git", {}) or {}
        self.env_names = str(self.context.input_param_get("params.env_names")).strip()
        self.git_host = str(self.git_params.get("host"))
        self.git_protocol = str(self.git_params.get("protocol") or "https")
        self.repository = re.sub(r"\.git$", "", str(self.git_params.get("repository")).strip("/"))
        self.ref_name = str(self.git_params.get("ref_name"))
        self.git_user_name = str(self.git_params.get("user_name") or "envgene")
        self.git_user_email = str(self.git_params.get("user_email") or "envgene@localhost")
        self.token = str(self.context.input_param_get("git_token"))

        if not Path(ENVGENE_PYTHON).is_file():
            self.context.logger.error(f"EnvGene Python interpreter not found: {ENVGENE_PYTHON}")
            return False
        if not Path(ENVGENE_ORCHESTRATOR).is_file():
            self.context.logger.error(f"EnvGene orchestrator not found: {ENVGENE_ORCHESTRATOR}")
            return False

        return True

    def _execute(self):
        self.context.logger.info(f"Running EnvGene for '{self.env_names}' in '{self.repo_path}' (git_host={self.git_host})")
        env = self._build_env()
        try:
            self._run_envgene(env)
        finally:
            self._sanitize_remote()
        self._store_outputs()

    def _resolve_repo_path(self) -> Path:
        path = Path(str(self.context.input_param_get("paths.input.files"))) / "repo"
        if not path.is_dir():
            raise ValueError(f"Instance repository directory not found: {path}")
        return path.resolve()

    def _head_sha(self) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.repo_path), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        sha = result.stdout.strip()
        if result.returncode != 0 or not sha:
            raise ValueError("Cannot determine the HEAD commit of the instance repository")
        return sha

    def _build_env(self) -> dict:
        env = os.environ.copy()
        for key, value in self.envgene_vars.items():
            if value is not None:
                env[str(key)] = _env_value(value)

        pipeline_type = str(env.get("PIPELINE_TYPE", "")).strip().upper()
        if pipeline_type in ("", "LEGACY"):
            env.pop("PIPELINE_TYPE", None)
        else:
            env["PIPELINE_TYPE"] = pipeline_type

        operation_type = str(env.get("OPERATION_TYPE", "")).strip().upper()
        if operation_type:
            env["OPERATION_TYPE"] = operation_type
        else:
            env.pop("OPERATION_TYPE", None)

        env["CI_PROJECT_DIR"] = str(self.repo_path)
        env["ENV_NAMES"] = self.env_names
        env["PYTHONPATH"] = "/module/scripts"
        env["JAVA_HOME"] = "/opt/jre"
        env["PATH"] = f"/opt/jre/bin:/module/venv/bin:{env.get('PATH', '')}"
        env.setdefault("PYTHONUNBUFFERED", "1")
        env.setdefault("ENVGENE_LOG_LEVEL", "INFO")

        age_private_key = self.context.input_param_get("envgene_age_private_key")
        public_age_keys = self.context.input_param_get("public_age_keys")
        if age_private_key:
            env["ENVGENE_AGE_PRIVATE_KEY"] = str(age_private_key)
        if public_age_keys:
            env["PUBLIC_AGE_KEYS"] = str(public_age_keys)

        # EnvGene's SOPS subprocess prefers an existing SOPS_AGE_KEY over ENVGENE_AGE_PRIVATE_KEY.
        if env.get("ENVGENE_AGE_PRIVATE_KEY"):
            env["SOPS_AGE_KEY"] = env["ENVGENE_AGE_PRIVATE_KEY"]
        elif env.get("SOPS_AGE_KEY"):
            env["ENVGENE_AGE_PRIVATE_KEY"] = env["SOPS_AGE_KEY"]
        if env.get("PUBLIC_AGE_KEYS"):
            env["SOPS_AGE_RECIPIENTS"] = env["PUBLIC_AGE_KEYS"]
        elif env.get("SOPS_AGE_RECIPIENTS"):
            env["PUBLIC_AGE_KEYS"] = env["SOPS_AGE_RECIPIENTS"]

        env.pop("GITHUB_ACTIONS", None)
        env.pop("IS_LOCAL_DEV_TEST_ENVGENE", None)
        env.update({
            "GITLAB_CI": "true",
            "CI_SERVER_HOST": self.git_host,
            "CI_SERVER_PROTOCOL": self.git_protocol,
            "CI_PROJECT_PATH": self.repository,
            "CI_COMMIT_REF_NAME": self.ref_name,
            "CI_COMMIT_SHA": self.sha,
            "GITLAB_USER_LOGIN": self.git_user_name,
            "GITLAB_USER_EMAIL": self.git_user_email,
            "GITLAB_TOKEN": self.token,
            "GITHUB_USER_NAME": self.git_user_name,
            "GITHUB_USER_EMAIL": self.git_user_email,
            "GITHUB_TOKEN": self.token,
        })
        return env

    def _run_envgene(self, env: dict) -> None:
        process = subprocess.Popen(
            [ENVGENE_PYTHON, ENVGENE_ORCHESTRATOR],
            cwd=str(self.repo_path),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        previous_handlers = {}

        def forward_signal(signum, _frame):
            if process.poll() is None:
                process.send_signal(signum)

        for sig in (signal.SIGINT, signal.SIGTERM):
            previous_handlers[sig] = signal.getsignal(sig)
            signal.signal(sig, forward_signal)

        try:
            output_lines = [line.rstrip("\n") for line in process.stdout] if process.stdout else []
            return_code = process.wait()
        finally:
            for sig, handler in previous_handlers.items():
                signal.signal(sig, handler)

        if output_lines:
            self.context.logger.info("\n".join(output_lines))
        if return_code != 0:
            raise RuntimeError(f"EnvGene failed with exit code {return_code}")

    def _sanitize_remote(self) -> None:
        remote_url = f"{self.git_protocol}://{self.git_host}/{self.repository}.git"
        subprocess.run(
            ["git", "-C", str(self.repo_path), "remote", "set-url", "origin", remote_url],
            capture_output=True,
            text=True,
            check=False,
        )

    def _store_outputs(self) -> None:
        full_env_name = re.split(r"[,;\s]+", self.env_names)[0]
        cluster_name, _, environment_name = full_env_name.partition("/")
        env_dir = self.repo_path / "environments" / cluster_name / environment_name

        self.context.output_param_set("params.env_names", self.env_names)
        self.context.output_param_set("params.full_env_name", full_env_name)
        self.context.output_param_set("params.cluster_name", cluster_name)
        self.context.output_param_set("params.environment_name", environment_name)

        effective_set_dir = env_dir / "effective-set"
        if effective_set_dir.is_dir():
            self.context.output_param_set("params.effective_set_dir", str(effective_set_dir))

        deploy_plan_path = env_dir / "Inventory" / "deploy-plan.yml"
        if deploy_plan_path.is_file():
            self.context.output_param_set("params.deploy_plan_path", str(deploy_plan_path))

        envgene_vars_path = self.repo_path / "envgene-vars.env"
        if envgene_vars_path.is_file():
            self.context.output_param_set("params.envgene_vars_path", str(envgene_vars_path))

        self.context.output_params_save()


def _env_value(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value, separators=(",", ":"), default=str)
    return str(value)
