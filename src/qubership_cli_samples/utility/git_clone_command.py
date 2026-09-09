import os
import subprocess
from pathlib import Path
from urllib.parse import quote

from qubership_pipelines_common_library.v1.execution.exec_command import ExecutionCommand


class GitCloneCommand(ExecutionCommand):

    def _validate(self):
        names = ["paths.input.params",
                 "paths.output.params",
                 "paths.output.files",
                 "params.url"]
        if not self.context.validate(names):
            return False
        self.url = self.context.input_param_get("params.url")
        self.branch = self.context.input_param_get("params.branch") or None
        self.depth = int(self.context.input_param_get("params.depth", 1))
        if self.depth < 1:
            self.context.logger.error(f"Invalid 'params.depth': {self.depth} - must be >= 1")
            return False
        self.target_dir = self.context.input_param_get("params.target_dir", "repo")
        if os.path.isabs(self.target_dir) or ".." in Path(self.target_dir).parts:
            self.context.logger.error(f"Invalid 'params.target_dir': '{self.target_dir}' - must be a relative path inside output files folder")
            return False
        self.username = self.context.input_param_get("systems.git.username")
        self.password = self.context.input_param_get("systems.git.password")
        return True

    def _execute(self):
        target_path = Path(self.context.input_param_get("paths.output.files")).joinpath(self.target_dir)
        self.context.logger.info(f"Running GitCloneCommand - cloning '{self.url}' "
                                 f"(branch={self.branch or '<default>'}, depth={self.depth}) into '{target_path}'...")
        cmd = ["git", "clone", "--quiet", "--depth", str(self.depth), "--single-branch"]
        if self.branch:
            cmd += ["--branch", self.branch]
        cmd += [self._url_with_credentials(), str(target_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            self.context.logger.error(f"'git clone' failed: {self._sanitize(result.stderr)}")
            self._exit(False, f"'git clone' failed with exit code {result.returncode}")

        commit_sha = self._git(target_path, "rev-parse", "HEAD")
        resolved_branch = self.branch or self._git(target_path, "rev-parse", "--abbrev-ref", "HEAD")
        self.context.output_param_set("params.commit_sha", commit_sha)
        self.context.output_param_set("params.branch", resolved_branch)
        self.context.output_param_set("params.repo_dir", self.target_dir)
        self.context.output_params_save()
        self.context.logger.info(f"Finished GitCloneCommand - cloned '{self.url}' @ {resolved_branch} ({commit_sha})")

    def _url_with_credentials(self):
        """Inserts basic-auth credentials into https URLs. Never log the returned value!"""
        if not (self.username and self.password):
            return self.url
        if not self.url.startswith("https://"):
            self.context.logger.warning("'systems.git.username/password' are set, but 'params.url' is not an https URL - credentials will be ignored")
            return self.url
        credentials = f"{quote(str(self.username), safe='')}:{quote(str(self.password), safe='')}"
        return self.url.replace("https://", f"{credentials}@", 1)

    def _sanitize(self, text):
        """Removes credentials from git output before logging it."""
        if self.password:
            text = text.replace(str(self.password), "***")
        if self.username:
            text = text.replace(str(self.username), "***")
        return text

    def _git(self, repo_path, *args):
        result = subprocess.run(["git", "-C", str(repo_path), *args], capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"'git {' '.join(args)}' failed: {result.stderr}")
        return result.stdout.strip()
