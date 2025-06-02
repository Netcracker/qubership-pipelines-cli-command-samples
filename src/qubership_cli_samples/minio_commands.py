from qubership_pipelines_common_library.v1.execution.exec_command import ExecutionCommand
from qubership_pipelines_common_library.v1.minio_client import MinioClient


class ListMinioBucketObjectsCommand(ExecutionCommand):

    def _validate(self):
        names = ["paths.input.params",
                 "paths.output.params",
                 "systems.minio.endpoint",
                 "systems.minio.access_key",
                 "systems.minio.secret_key",
                 "params.bucket_name",
                 ]
        return self.context.validate(names)

    def _execute(self):
        self.context.logger.info("Running ListMinioBucketFileNamesCommand - listing files present in a certain MiniO bucket...")
        minio = MinioClient(self.context.input_param_get("systems.minio.endpoint"),
                            self.context.input_param_get("systems.minio.access_key"),
                            self.context.input_param_get("systems.minio.secret_key"))
        result = minio.list_objects(self.context.input_param_get("params.bucket_name"),
                                    self.context.input_param_get("params.path", ""))
        self.context.output_param_set("params.minio_objects", [vars(o) for o in result])
        self.context.output_params_save()
