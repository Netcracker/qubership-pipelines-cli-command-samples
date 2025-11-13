import os, subprocess, time, logging, uuid

from pathlib import Path
from qubership_pipelines_common_library.v1.execution.exec_command import ExecutionCommand
from qubership_pipelines_common_library.v1.utils.utils_string import UtilsString

logging.basicConfig(level=logging.INFO)


class PodmanRunImage(ExecutionCommand):

    def _validate(self):
        names = [
            "paths.input.params",
            "paths.output.params",
            "paths.output.files",
            "params.image",
            # "params.command", - optional
            # "params.working_dir", - optional
            # "params.timeout", - optional
            # "params.copy_timeout", - optional
            # "params.mounts", - optional (dict)
            # "params.env_vars", - optional (dict)
            # "params.copy", - optional (dict)
            # "params.remove_container", - optional (bool)
            # "params.save_container_output_to_files", - optional (bool)
            # "params.save_container_output_to_params", - optional (bool)
            # "params.expected_return_codes", - optional (str) - comma separated codes
        ]
        if not self.context.validate(names):
            return False

        # Check if podman is available
        try:
            subprocess.run(["podman", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.context.logger.error("Podman is not available on this system. Please install podman to use this command.")
            return False

        # Setup defaults & convert values
        self.image = self.context.input_param_get("params.image")
        self.mounts_config = self.context.input_param_get("params.mounts", {})
        self.env_vars_config = self.context.input_param_get("params.env_vars", {})
        self.copy_config = self.context.input_param_get("params.copy", {})
        self.timeout = float(self.context.input_param_get("params.timeout", 60))
        self.copy_timeout = float(self.context.input_param_get("params.copy_timeout", 15))
        self.command = self.context.input_param_get("params.command")
        self.working_dir = self.context.input_param_get("params.working_dir")
        self.remove_container = UtilsString.convert_to_bool(self.context.input_param_get("params.remove_container", True))
        self.save_container_output_to_files = UtilsString.convert_to_bool(self.context.input_param_get("params.save_container_output_to_files", True))
        self.save_container_output_to_params = UtilsString.convert_to_bool(self.context.input_param_get("params.save_container_output_to_params", False))
        self.expected_return_codes = [int(num) for num in self.context.input_param_get("params.expected_return_codes", "0").split(',')]

        # Get base paths
        self.context_dir_path = Path(os.path.dirname(self.context.context_path))
        self.input_params_path = Path(self.context.input_param_get("paths.input.params"))
        self.output_params_path = Path(self.context.input_param_get("paths.output.params"))
        self.output_files_path = Path(self.context.input_param_get("paths.output.files"))

        return True

    def _build_podman_command(self, container_name: str) -> list[str]:
        cmd = ["podman", "run"]

        cmd.extend(["--name", container_name])

        if self.working_dir:
            cmd.extend(["--workdir", self.working_dir])

        if self.env_vars_config:
            for key, value in self.env_vars_config.get("explicit", {}).items():
                cmd.extend(["--env", f"{key}={value}"])

            for env_file in self.env_vars_config.get("env_files", []):
                cmd.extend(["--env-file", f"{env_file}"])

            for prefix in self.env_vars_config.get("host_prefixes", []):
                cmd.extend(["--env", f"{prefix}"])

            if self.env_vars_config.get("pass_via_file"):
                env_file_path = self.context_dir_path.joinpath("temp").joinpath("temp.env")
                env_file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(env_file_path, 'w') as f:
                    for key, value in self.env_vars_config["pass_via_file"].items():
                        f.write(f"{key}={value}\n")
                cmd.extend(["--env-file", str(env_file_path)])

        for host_path, container_path in self.mounts_config.items():
            # Allow read-only mount with "ro" suffix
            if isinstance(container_path, str) and container_path.endswith(":ro"):
                target_path = container_path[:-3]
                cmd.extend(["--mount", f"type=bind,source={host_path},target={target_path},readonly"])
            else:
                cmd.extend(["--mount", f"type=bind,source={host_path},target={container_path}"])

        cmd.append(self.image)

        if self.command:
            if isinstance(self.command, str):
                import shlex
                cmd.extend(shlex.split(self.command))
            elif isinstance(self.command, list):
                cmd.extend(self.command)

        return cmd

    def _copy_files_from_container(self, container_name: str):
        for host_path, container_path in self.copy_config.items():
            full_host_path = self.context_dir_path.joinpath(host_path)
            full_host_path.parent.mkdir(parents=True, exist_ok=True)

            copy_command = ["podman", "cp", f"{container_name}:{container_path}", str(full_host_path)]
            try:
                result = subprocess.run(
                    copy_command,
                    capture_output=True,
                    text=True,
                    timeout=self.copy_timeout,
                    cwd=self.context_dir_path
                )
                if result.returncode != 0:
                    self.context.logger.warning(f"Failed to copy {container_path} to {host_path}: {result.stderr}")
                else:
                    self.context.logger.info(f"Copied {container_path} to {host_path}")
            except subprocess.TimeoutExpired:
                self.context.logger.warning(f"Copy command timed out after {self.copy_timeout} seconds")

    def _write_output_files(self, stdout: str, stderr: str):
        if self.save_container_output_to_files:
            stdout_file = self.output_files_path / "container_stdout.txt"
            stdout_file.write_text(stdout, encoding='utf-8')
            stderr_file = self.output_files_path / "container_stderr.txt"
            stderr_file.write_text(stderr, encoding='utf-8')

    def _execute(self):
        self.context.logger.info(f"Running podman image \"{self.image}\"...")

        container_name = f"podman_run_{str(uuid.uuid4())}"
        podman_cmd = self._build_podman_command(container_name)

        start = time.perf_counter()
        try:
            output = subprocess.run(
                podman_cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=self.context_dir_path
            )

            end = time.perf_counter()
            execution_time = end - start

            self._write_output_files(output.stdout, output.stderr)

            if self.copy_config:
                self._copy_files_from_container(container_name)

            self.context.logger.info(
                f"Container finished with code: {output.returncode}"
                f"\nExecution time: {execution_time:0.3f}s"
            )

            if output.stdout:
                self.context.logger.debug(f"Container stdout:\n{output.stdout}")
            if output.stderr:
                self.context.logger.debug(f"Container stderr:\n{output.stderr}")

            self.context.output_param_set("params.execution_time", f"{execution_time:0.3f}s")
            self.context.output_param_set("params.return_code", output.returncode)

            if self.save_container_output_to_params:
                self.context.output_param_set("params.stdout", output.stdout)
                self.context.output_param_set("params.stderr", output.stderr)

            if output.returncode not in self.expected_return_codes:
                raise PodmanException(output.stderr)

        except subprocess.TimeoutExpired as e:
            end = time.perf_counter()
            stdout = e.stdout.decode('utf-8') if e.stdout else ""
            stderr = e.stderr.decode('utf-8') if e.stderr else ""
            self._write_output_files(stdout, stderr)
            self.context.logger.error(f"Container execution timed out after {self.timeout} seconds")
            self.context.output_param_set("params.execution_time", f"{end - start:0.3f}s")
            self.context.output_param_set("params.timeout", True)
            self.context.output_param_set("params.return_code", -1)
            raise

        except PodmanException:
            raise

        except Exception as e:
            end = time.perf_counter()
            self.context.logger.error(f"Container execution failed: {e}")
            self.context.output_param_set("params.execution_time", f"{end - start:0.3f}s")
            self.context.output_param_set("params.error", str(e))
            self.context.output_param_set("params.return_code", -1)
            raise

        finally:
            if self.remove_container:
                remove_output = subprocess.run(["podman", "rm", "-f", container_name], capture_output=True)
                if remove_output.returncode != 0:
                    self.context.logger.warning(f"Failed to remove container {container_name}: {remove_output.stdout}")
            self.context.output_params_save()


class PodmanException(Exception):
    pass
