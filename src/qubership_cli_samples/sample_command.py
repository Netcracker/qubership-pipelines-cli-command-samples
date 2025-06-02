from qubership_pipelines_common_library.v1.execution.exec_command import ExecutionCommand


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