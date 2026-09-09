import re

from qubership_pipelines_common_library.v1.execution.exec_command import ExecutionCommand


class SemverBumpCommand(ExecutionCommand):

    SEMVER_PATTERN = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
    PARTS = ("major", "minor", "patch")

    def _validate(self):
        names = ["paths.input.params",
                 "paths.output.params",
                 "params.version"]
        if not self.context.validate(names):
            return False
        self.version = str(self.context.input_param_get("params.version"))
        if not self.SEMVER_PATTERN.match(self.version):
            self.context.logger.error(f"Invalid 'params.version': '{self.version}' - expected format is 'X.Y.Z' (e.g. '1.4.2')")
            return False
        self.part = str(self.context.input_param_get("params.part", "patch")).lower()
        if self.part not in self.PARTS:
            self.context.logger.error(f"Invalid 'params.part': '{self.part}' - expected one of: {', '.join(self.PARTS)}")
            return False
        self.result_name = self.context.input_param_get("params.result_name", "new_version")
        return True

    def _execute(self):
        self.context.logger.info(f"Running SemverBumpCommand - bumping '{self.part}' part of version '{self.version}'...")
        major, minor, patch = (int(group) for group in self.SEMVER_PATTERN.match(self.version).groups())
        match self.part:
            case "major":
                major, minor, patch = major + 1, 0, 0
            case "minor":
                minor, patch = minor + 1, 0
            case "patch":
                patch += 1
        new_version = f"{major}.{minor}.{patch}"
        self.context.output_param_set(f"params.{self.result_name}", new_version)
        self.context.output_params_save()
        self.context.logger.info(f"Finished SemverBumpCommand - bumped version: {self.version} -> {new_version} (saved as 'params.{self.result_name}')")
