from qubership_pipelines_common_library.v1.execution.exec_command import ExecutionCommand


class DebugCommand(ExecutionCommand):
    def _validate(self):
        names = ["paths.input.params", "paths.output.params"]
        if not self.context.validate(names):
            return False
        self.failure_chance = float(self.context.input_param_get("params.failure_chance", 0))
        self.output_params = self.context.input_param_get("params.output_params", {})
        self.output_params_secure = self.context.input_param_get("params.output_params_secure", {})
        return True

    def _execute(self):
        self.context.logger.info("Running DebugCommand")

        if self.output_params:
            for key, value in self.output_params.items():
                self.context.output_param_set(f"params.{key}", value)
            self.context.logger.info(f"Updated output params")

        if self.output_params_secure:
            for key, value in self.output_params_secure.items():
                self.context.output_param_secure_set(f"params.{key}", value)
            self.context.logger.info(f"Updated output params secure")

        self.context.output_params_save()

        import random
        if self.failure_chance > 0 and random.random() < self.failure_chance:
            self.context.logger.info(f"Failure chance triggered ({self.failure_chance} failure chance)")
            self._exit(False, "Simulated failure from DebugCommand")
        else:
            self.context.logger.info(f"No failure triggered ({self.failure_chance} failure chance)")

        self.context.logger.info("Finished DebugCommand")
