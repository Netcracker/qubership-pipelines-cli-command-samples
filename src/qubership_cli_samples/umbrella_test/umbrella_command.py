import os
import shutil
import tempfile
import zipfile
from pathlib import Path

from qubership_pipelines_common_library.v1.execution.exec_command import ExecutionCommand
from qubership_pipelines_common_library.v1.execution.exec_info import ExecutionInfo
from qubership_pipelines_common_library.v1.gitlab_client import GitlabClient


class UmbrellaCommand(ExecutionCommand):

    def _validate(self):
        names = ["paths.input.params",
                 "paths.output.params",
                 "paths.output.files",
                 "systems.gitlab.url",
                 ]
        return self.context.validate(names)

    def _execute(self):
        self.context.logger.info("Running UmbrellaCommand - executing few child ExecutionCommands and collecting their output...")
        input_params_for_gitlab = {
            "params": {
                "pipeline": "quber-test/quber-pipeline",
                "pipeline_params": {
                    "TEST_FILE_NAME": "name_from_first_job.txt"
                },
            },
            "systems": {
                "gitlab": {
                    "password": os.getenv('GITLAB_QUBER_TOKEN', "UNKNOWN")
                }
            }
        }

        # Run one child
        self.context.logger.info("Running first RunGitlabPipelineCommand...")
        cmd1 = RunGitlabPipelineCommand(input_params=input_params_for_gitlab, parent_context_to_reuse=self.context)
        try:
            cmd1.run()
        except SystemExit as e:
            # we need this because we forced exit codes into ExecutionCommand.run(), and they will end our CLI process
            self.context.logger.info(f"first cmd exited with code={e}")

        # Run another child
        # self.context.logger.info("Running second RunGitlabPipelineCommand...")
        # input_params_for_gitlab["params"]["pipeline_params"]["TEST_FILE_NAME"] = "name_from_second.txt"
        # cmd2 = RunGitlabPipelineCommand(input_params=input_params_for_gitlab, parent_context_to_reuse=self.context)
        # try:
        #     cmd2.run()
        # except SystemExit as e:
        #     self.context.logger.info(f"second cmd exited with code={e}")

        # Collect output files from child processes into our folder
        self.context.logger.info("Fetching results from children...")
        shutil.copytree(Path(cmd1.context.input_param_get("paths.output.files")), Path(self.context.input_param_get("paths.output.files")).joinpath("run1_result"), dirs_exist_ok=True)
        # shutil.copytree(Path(cmd2.context.input_param_get("paths.output.files")), Path(self.context.input_param_get("paths.output.files")).joinpath("run2_result"), dirs_exist_ok=True)
        self.context.logger.info(f"cmd1 output: {cmd1.context.output_params.content}")
        # self.context.logger.info(f"cmd2 output: {cmd2.context.output_params.content}")


class RunGitlabPipelineCommand(ExecutionCommand):

    def _validate(self):
        names = ["paths.input.params",
                 "paths.output.params",
                 "paths.output.files",
                 "params.pipeline",
                 "params.pipeline_params",
                 "systems.gitlab.url",
                 "systems.gitlab.password",
                 ]
        return self.context.validate(names)

    def _execute(self):
        self.context.logger.info("RunGitlabPipelineCommand - executing GitLab pipeline and fetching results...")
        gitlab_client = GitlabClient(host=self.context.input_param_get("systems.gitlab.url"), username=None,
                            password=self.context.input_param_get("systems.gitlab.password"))
        pipeline_path = self.context.input_param_get("params.pipeline")
        pipeline_params = {
            'ref': gitlab_client.gl.projects.get(pipeline_path).default_branch,
            'variables': [{'key': k, 'value': v} for k, v in self.context.input_param_get("params.pipeline_params", {}).items()],
        }
        execution = gitlab_client.trigger_pipeline(project_id=pipeline_path, pipeline_params=pipeline_params)
        self.context.logger.info(f"Triggered pipeline {execution.get_id()}, status: {execution.get_status()}")
        execution = gitlab_client.wait_pipeline_execution(
            execution=execution,
            timeout_seconds=60,
            wait_seconds=5,
        )
        self.context.logger.info(f"Pipeline status after waiting: {execution.get_status()}")
        self._save_execution_info(execution)
        if execution.get_status() == "SUCCESS":
            try:
                project = gitlab_client.gl.projects.get(pipeline_path, lazy=True)
                pipeline = project.pipelines.get(execution.get_id(), lazy=True)
                job = project.jobs.get(pipeline.jobs.list(get_all=True)[0].id, lazy=True)

                with tempfile.TemporaryDirectory() as temp_dirname:
                    local_file = Path(temp_dirname, f"{job.id}.zip")
                    with local_file.open('wb') as f:
                        job.artifacts(streamed=True, action=f.write)
                    with zipfile.ZipFile(local_file) as zf:
                        self.context.logger.info(f"Extracting {job.id} to: {self.context.input_param_get('paths.output.files')}")
                        zf.extractall(self.context.input_param_get("paths.output.files"))
            except Exception as e:
                self.context.logger.error(f"Something went wrong when downloading pipeline artifacts - {e}")

    def _save_execution_info(self, execution: ExecutionInfo):
        self.context.logger.info(f"Writing GitLab pipeline execution status")
        self.context.output_param_set("params.build.url", execution.get_url())
        self.context.output_param_set("params.build.id", execution.get_id())
        self.context.output_param_set("params.build.status", execution.get_status())
        self.context.output_param_set("params.build.date", execution.get_time_start().isoformat())
        self.context.output_param_set("params.build.duration", execution.get_duration_str())
        self.context.output_param_set("params.build.name", execution.get_name())
        self.context.output_params_save()
