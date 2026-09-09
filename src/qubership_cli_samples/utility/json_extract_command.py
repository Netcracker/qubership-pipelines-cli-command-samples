import json
from pathlib import Path

from qubership_pipelines_common_library.v1.execution.exec_command import ExecutionCommand

_MISSING = object()


class JsonExtractCommand(ExecutionCommand):

    def _validate(self):
        names = ["paths.input.params",
                 "paths.input.files",
                 "paths.output.params",
                 "params.filename",
                 "params.extract"]
        if not self.context.validate(names):
            return False
        self.filename = self.context.input_param_get("params.filename")
        self.extract = self.context.input_param_get("params.extract")
        if not isinstance(self.extract, dict) or not self.extract:
            self.context.logger.error("'params.extract' must be a non-empty map of 'output_name: dot.path.in.json'")
            return False
        return True

    def _execute(self):
        self.context.logger.info(f"Running JsonExtractCommand - extracting {len(self.extract)} value(s) from '{self.filename}'...")
        target_path = Path(self.context.input_param_get("paths.input.files")).joinpath(self.filename)
        try:
            with open(target_path, encoding="utf-8") as fs:
                data = json.load(fs)
        except FileNotFoundError:
            self._exit(False, f"File not found in input files folder: '{self.filename}'")
        except json.JSONDecodeError as e:
            self._exit(False, f"File '{self.filename}' is not a valid JSON: {e}")

        for output_name, dot_path in self.extract.items():
            value = self._extract_value(data, str(dot_path))
            if value is _MISSING:
                self._exit(False, f"Path '{dot_path}' not found in '{self.filename}'")
            string_value = self._stringify(value)
            self.context.output_param_set(f"params.{output_name}", string_value)
            self.context.logger.info(f"Extracted '{dot_path}' -> 'params.{output_name}' = {string_value}")
        self.context.output_params_save()
        self.context.logger.info("Finished JsonExtractCommand")

    @staticmethod
    def _extract_value(data, dot_path):
        current = data
        for segment in dot_path.split("."):
            if isinstance(current, dict):
                current = current.get(segment, _MISSING)
            elif isinstance(current, list) and segment.isdigit() and int(segment) < len(current):
                current = current[int(segment)]
            else:
                return _MISSING
        return current

    @staticmethod
    def _stringify(value):
        if value is None:
            return ""
        if isinstance(value, bool):
            return str(value).lower()
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return str(value)
