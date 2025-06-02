import os
from pathlib import Path

import yaml
from qubership_pipelines_common_library.v1.execution.exec_command import ExecutionCommand
import urllib.request
import time

from qubership_pipelines_common_library.v1.utils.utils_context import create_execution_context


def sizeof_fmt(num, suffix="B"):
    for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
        if abs(num) < 1024.0:
            return f"{num:3.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} Yi{suffix}"


class DownloadFileExecutionCommand(ExecutionCommand):

    def _validate(self):
        names = ["paths.input.params",
                 "paths.output.params",
                 "paths.output.files",
                 "params.url",
                 "params.filename"]
        return self.context.validate(names)

    def _execute(self):
        url = self.context.input_param_get("params.url")
        filename = self.context.input_param_get("params.filename")
        self.context.logger.info(f"Downloading file from {url} and putting it as {filename} to output files folder...")
        target_path = Path(self.context.input_param_get("paths.output.files")).joinpath(filename)
        start = time.perf_counter()
        urllib.request.urlretrieve(url, target_path)
        end = time.perf_counter()
        self.context.output_param_set("params.filename", filename)
        self.context.output_param_set("params.filesize", sizeof_fmt(os.path.getsize(target_path)))
        self.context.output_param_set("params.download_time", f"{end - start:0.3f}s")
        self.context.output_params_save()


class AnalyzeFileExecutionCommand(ExecutionCommand):

    def _validate(self):
        names = ["paths.input.params",
                 "paths.input.files",
                 "paths.output.params",
                 "params.filename"]
        return self.context.validate(names)

    def _execute(self):
        filename = self.context.input_param_get("params.filename")
        self.context.logger.info(f"Analyzing data in {filename} and saving it to output params...")
        target_path = Path(self.context.input_param_get("paths.input.files")).joinpath(filename)
        self.context.output_param_set("params.filename", filename)
        self.context.output_param_set("params.filesize", sizeof_fmt(os.path.getsize(target_path)))
        self.context.output_params_save()


class GenerateContextFromEnv(ExecutionCommand):

    def _validate(self):
        names = ["params.context_folder"]
        return self.context.validate(names)

    def _execute(self):
        context_folder = self.context.input_param_get("params.context_folder")
        input_params = dict()
        if input_params_str := os.getenv("input_params"):
            input_params = yaml.safe_load(input_params_str)
        context_file = create_execution_context(folder_path=context_folder, input_params=input_params)
