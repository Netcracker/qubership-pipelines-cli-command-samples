import tempfile
import zipfile
from pathlib import Path

from qubership_pipelines_common_library.v1.execution.exec_command import ExecutionCommand
from qubership_pipelines_common_library.v1.execution.exec_info import ExecutionInfo
from qubership_pipelines_common_library.v1.github_client import GithubClient


class GithubRunPipeline(ExecutionCommand):

    WORKFLOW_QUEUE_TIMEOUT = 60
    WAIT_TIMEOUT = 1800 # default value how many seconds to wait for workflow execution
    WAIT_INTERVAL = 5  # default value how many seconds to wait between pipeline checks

    def _validate(self):
        names = [
            "paths.input.params",
            "paths.output.params",
            "paths.output.params_secure",
            "paths.output.files",
            # "systems.github.url", # optional, API URL for self-hosted GitHub Enterprise
            "systems.github.password",
            "params.pipeline_owner",
            "params.pipeline_repo_name",
            "params.pipeline_workflow_file_name",
            # "params.pipeline_branch", # string, optional, default is default branch of github repo
            # "params.pipeline_params", # optional dict, since the job may have no params of can be executed with default values
            # "params.import_artifacts",  # bool, optional, default is 'false'
            # "params.use_existing_pipeline",  # optional, for debug, value is workflow run ID
            # "params.timeout_seconds": 1800,  # optional
            # "params.wait_interval": 5  # optional
            # "params.success_statuses": 'SUCCESS, UNSTABLE' # default value is 'SUCCESS'
        ]
        if not self.context.validate(names):
            return False
        self.timeout_seconds = max(0, int(self.context.input_param_get("params.timeout_seconds", GithubRunPipeline.WAIT_TIMEOUT)))
        self.wait_seconds = max(1, int(self.context.input_param_get("params.wait_interval", GithubRunPipeline.WAIT_INTERVAL)))
        if self.timeout_seconds == 0:
            self.context.logger.info(f"Timeout is set to: {self.timeout_seconds}. This means that pipeline will be started asynchronously")
        self.pipeline_owner = self.context.input_param_get("params.pipeline_owner")
        self.pipeline_repo_name = self.context.input_param_get("params.pipeline_repo_name")
        self.pipeline_workflow_file_name = self.context.input_param_get("params.pipeline_workflow_file_name")
        self.pipeline_branch = self.context.input_param_get("params.pipeline_branch")
        self.pipeline_params = self.context.input_param_get("params.pipeline_params", {})
        if not self.pipeline_params:
            self.context.logger.info(f"Pipeline parameters was not specified. This means that pipeline will be started with its default values")
        if not isinstance(self.pipeline_params, dict):
            self.context.logger.error(f"Pipeline parameters was not loaded correctly. Probably mistake in the params definition")
            return False
        self.import_artifacts = self.context.input_param_get("params.import_artifacts", False)
        self.success_statuses = [x.strip() for x in self.context.input_param_get("params.success_statuses", ExecutionInfo.STATUS_SUCCESS).split(",")]
        self.use_existing_pipeline = self.context.input_param_get("params.use_existing_pipeline")
        return True

    def _execute(self):
        self.context.logger.info("GithubRunPipeline - triggering GitHub workflow run and fetching results...")
        self.github_client = GithubClient(api_url=self.context.input_param_get("systems.github.url"),
                                          token=self.context.input_param_get("systems.github.password"))

        if self.use_existing_pipeline: # for debug
            pipeline_id = self.use_existing_pipeline
            self.context.logger.info(f"Using existing pipeline {pipeline_id}")
            execution = (ExecutionInfo()
                         .with_url(f"https://github.com/{self.pipeline_owner}/{self.pipeline_repo_name}/")
                         .with_name(self.pipeline_workflow_file_name).with_id(int(pipeline_id))
                         .with_status(ExecutionInfo.STATUS_UNKNOWN))
            execution.start()
        else:
            branch = self.pipeline_branch
            if not branch:
                branch = self.github_client.get_repo_default_branch(self.pipeline_owner, self.pipeline_repo_name)
            execution = self.github_client.trigger_workflow(owner=self.pipeline_owner, repo_name=self.pipeline_repo_name,
                                                            workflow_file_name=self.pipeline_workflow_file_name,
                                                            branch=branch, pipeline_params=self.pipeline_params
                                                            )
            self.context.logger.info(f"Triggered pipeline {execution.get_id()}, status: {execution.get_status()}, url: {execution.get_url()}")

        if execution.get_status() != ExecutionInfo.STATUS_IN_PROGRESS:
            self._exit(False, f"Pipeline was not started. Status {execution.get_status()}")
        elif self.timeout_seconds < 1:
            self.context.logger.info("Pipeline was started in asynchronous mode. Pipeline status and artifacts will not be processed")
            self._exit(True, f"Status: {execution.get_status()}")

        execution = self.github_client.wait_workflow_run_execution(execution=execution,
                                                                   timeout_seconds=self.timeout_seconds,
                                                                   wait_seconds=self.wait_seconds)
        self.context.logger.info(f"Pipeline status: {execution.get_status()}")

        if self.import_artifacts and execution.get_status() in ExecutionInfo.STATUSES_COMPLETE:
            # self.import_pipeline_data(execution)
            self.context.output_params.load(self.context.input_param_get("paths.output.params"))
            self.context.output_params_secure.load(self.context.input_param_get("paths.output.params_secure"))
        self._save_execution_info(execution)
        self._exit(execution.get_status() in self.success_statuses, f"Status: {execution.get_status()}")

    def _save_execution_info(self, execution: ExecutionInfo):
        self.context.logger.info(f"Writing GitHub workflow execution status")
        self.context.output_param_set("params.build.url", execution.get_url())
        self.context.output_param_set("params.build.id", execution.get_id())
        self.context.output_param_set("params.build.status", execution.get_status())
        self.context.output_param_set("params.build.date", execution.get_time_start().isoformat())
        self.context.output_param_set("params.build.duration", execution.get_duration_str())
        self.context.output_param_set("params.build.name", execution.get_name())
        self.context.output_params_save()
