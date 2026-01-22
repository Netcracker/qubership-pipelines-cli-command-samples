from qubership_pipelines_common_library.v1.execution.exec_command import ExecutionCommand
from qubership_pipelines_common_library.v1.utils.utils_string import UtilsString

WORD_LIST = [
    "apple", "happy", "sunshine", "book", "mountain",
    "ocean", "guitar", "laughter", "butterfly", "coffee",
    "rainbow", "adventure", "breeze", "chocolate", "dolphin",
    "elephant", "firefly", "garden", "harmony", "island",
    "jellybean", "kitten", "lighthouse", "moonlight", "notebook",
    "orange", "penguin", "quilt", "river", "sunflower",
    "telescope", "umbrella", "violin", "waterfall", "xylophone",
    "yogurt", "zeppelin", "autumn", "blossom", "cinnamon",
    "daisy", "echo", "flamingo", "giraffe", "horizon",
    "iceberg", "jazz", "kiwi", "lullaby", "meadow"
]


class SampleStandaloneExecutionCommand(ExecutionCommand):

    def _validate(self):
        names = ["paths.input.params",
                 "paths.output.params",
                 "params.param_1",
                 "params.param_2"]
        return self.context.validate(names)

    def _execute(self):
        self.context.logger.info("Running SampleExecutionCommand - calculating sum of 'param_1' and 'param_2'...")
        result_sum = int(self.context.input_param_get("params.param_1")) + int(self.context.input_param_get("params.param_2"))
        self.context.output_param_set("params.result", result_sum)
        self.context.output_params_save()


class CalcCommand(ExecutionCommand):

    def _validate(self):
        names = ["paths.input.params",
                 "paths.output.params",
                 "params.param_1",
                 "params.param_2",
                 "params.operation",
                 "params.result_name"]
        return self.context.validate(names)

    def _execute(self):
        self.context.logger.info("Running CalcCommand - calculating operation on 'param_1' and 'param_2'...")
        param1 = int(self.context.input_param_get("params.param_1"))
        param2 = int(self.context.input_param_get("params.param_2"))
        match self.context.input_param_get("params.operation"):
            case "add":
                result = param1 + param2
            case "subtract":
                result = param1 - param2
            case "multiply":
                result = param1 * param2
            case "divide":
                result = param1 / param2
            case _:
                raise Exception(f"Invalid operation: {self.context.input_param_get('params.operation')}")
        self.context.output_param_set(f"params.{self.context.input_param_get('params.result_name')}", result)
        self.context.output_params_save()


class GenerateTestOutputParamsCommand(ExecutionCommand):

    def _validate(self):
        names = [
            "paths.input.params",
            "paths.output.params"
        ]
        if not self.context.validate(names):
            return False
        self.param_count = int(self.context.input_param_get("params.param_count", 5))
        self.sleep_time = float(self.context.input_param_get("params.sleep_time", 0))
        self.sleep_period = float(self.context.input_param_get("params.sleep_period", 1))
        self.random_sleep = UtilsString.convert_to_bool(self.context.input_param_get("params.random_sleep", False))
        self.print_all_level_logs = UtilsString.convert_to_bool(self.context.input_param_get("params.print_all_level_logs", False))
        return True

    def _execute(self):
        import random, time
        self.context.logger.info("Running GenerateTestOutputParamsCommand - generating params into output_params and output_params_secure...")
        self.context.logger.warning("This command should only be used for debugging pipelines!")

        if self.param_count > 0:
            for i in range(self.param_count):
                self.context.output_param_set(f"params.some_insecure_param_{i}",
                                              f"{random.choice(WORD_LIST)}_{random.choice(WORD_LIST)}_{random.choice(WORD_LIST)}")
                self.context.output_param_secure_set(f"params.secure_param_{i}",
                                              f"{random.choice(WORD_LIST)}_{random.choice(WORD_LIST)}_{random.choice(WORD_LIST)}")
            self.context.output_param_set("params.nested_system.its_key", f"{random.choice(WORD_LIST)}")
            self.context.output_param_set("params.nested_system.its_secret", f"{random.choice(WORD_LIST)}")
        else:
            self.context.logger.info(f"Not generating any params (param_count={self.param_count})")

        if self.sleep_time > 0:
            if self.random_sleep:
                actual_sleep_time = random.uniform(0.1, self.sleep_time)
            else:
                actual_sleep_time = self.sleep_time
            self.context.logger.info(f"Will sleep for {actual_sleep_time:.2f} seconds")
            total_time = 0
            while total_time < actual_sleep_time:
                self.context.logger.debug(f"Sleeping for {self.sleep_period:.2f} second(s). Total: {total_time:.2f}/{actual_sleep_time:.2f}")
                time.sleep(self.sleep_period)
                total_time += self.sleep_period
            self.context.logger.info(f"Finished sleeping for {total_time:.2f} seconds")

        if self.print_all_level_logs:
            self.context.logger.debug("Sample DEBUG log")
            self.context.logger.info("Sample INFO log")
            self.context.logger.warning("Sample WARNING log")
            self.context.logger.error("Sample ERROR log")
            self.context.logger.critical("Sample CRITICAL log")

        self.context.output_params_save()
        self.context.logger.info("Finished GenerateTestOutputParamsCommand")


class GenerateTestOutputFilesCommand(ExecutionCommand):

    def _validate(self):
        names = ["paths.input.params", "paths.output.files"]
        return self.context.validate(names)

    def _execute(self):
        import random
        from pathlib import Path
        files_count = int(self.context.input_param_get("params.files_count", 1))
        self.context.logger.info(f"Running GenerateTestOutputFilesCommand - creating {files_count} different file(s) in output_files directory... (files_count={files_count})")

        for i in range(files_count):
            target_path = Path(self.context.input_param_get("paths.output.files")).joinpath(f"file_{i}.txt")
            with open(target_path, 'w') as fs:
                fs.write(f"File words spam: {random.choice(WORD_LIST)}_{random.choice(WORD_LIST)}_{random.choice(WORD_LIST)}\nAnd even {random.choice(WORD_LIST)}!")

        self.context.logger.info("Finished GenerateTestOutputFilesCommand")


class GenerateTestModuleReportCommand(ExecutionCommand):

    MODULE_REPORT_NAME = "module_report"

    def _validate(self):
        names = ["paths.input.params",
                 "paths.output.params"]
        return self.context.validate(names)

    def _execute(self):
        import random
        from pathlib import Path
        params_count = int(self.context.input_param_get("params.params_count", 3))
        report_extension = self.context.input_param_get("params.extension", "json")
        self.context.logger.info(f"Running GenerateTestModuleReportCommand - generating params into moduleReport file..."
                                 f" (params_count={params_count}, name={self.MODULE_REPORT_NAME}, extension={report_extension})")

        report = {
            "kind": "AtlasModuleReport",
            "apiVersion": "v1",
            "reportedParams": {}
        }
        for i in range(params_count):
            report["reportedParams"][f"param_{i}"] = f"{random.choice(WORD_LIST)}_{random.choice(WORD_LIST)}_{random.choice(WORD_LIST)}"

        report_extension_lower = report_extension.lower()
        if report_extension_lower not in ["json", "yaml"]:
            self.context.logger.warning(f"Unknown requested extension: {report_extension}! Falling back to \"json\"")
            report_extension_lower = "json"

        if report_extension_lower == "json":
            import json
            with open(Path(self.context.path_logs).joinpath(f"{self.MODULE_REPORT_NAME}.json"), 'w') as fs:
                fs.write(json.dumps(report))
        elif report_extension_lower == "yaml":
            from qubership_pipelines_common_library.v1.utils.utils_file import UtilsFile
            UtilsFile.write_yaml(Path(self.context.path_logs).joinpath(f"{self.MODULE_REPORT_NAME}.yaml"), report)

        self.context.logger.info("Finished GenerateTestModuleReportCommand")
