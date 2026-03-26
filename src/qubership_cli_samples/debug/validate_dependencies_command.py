import time, traceback
from qubership_pipelines_common_library.v1.execution.exec_command import ExecutionCommand


class ValidateDependenciesCommand(ExecutionCommand):
    """Command to validate integrity of common-lib dependencies (especially binary ones)"""

    def _validate(self):
        return True

    def _execute(self):
        self.context.logger.info("Running ValidateDependenciesCommand")
        try:
            self.context.logger.info("-- Validating existing execution commands...")
            self._validate_execution_commands()
            self.context.logger.info("-- Validating existing clients...")
            self._validate_clients()
        except Exception as e:
            self.context.logger.error(f"Error validating dependencies: [{type(e)} - {str(e)}]")
            self.context.logger.error("Full traceback: %s", traceback.format_exc())
            self._exit(False, f"Exception: {str(e)}")

        self.context.logger.info("Finished ValidateDependenciesCommand")

    def _validate_execution_commands(self):
        start_cmd = time.perf_counter()
        from qubership_cli_samples.file_processing.file_commands import DownloadFileExecutionCommand
        from qubership_cli_samples.file_processing.file_commands import AnalyzeFileExecutionCommand
        from qubership_cli_samples.umbrella_test.umbrella_command import UmbrellaCommand
        from qubership_cli_samples.file_processing.file_commands import GenerateContextFromEnv
        from qubership_cli_samples.report.report_command import BuildReport
        from qubership_cli_samples.minio_commands import ListMinioBucketObjectsCommand
        from qubership_cli_samples.debug.system_load_commands import SystemLoadTestCommand
        from qubership_cli_samples.sample_command import GenerateTestModuleReportCommand
        from qubership_cli_samples.sample_command import GenerateTestOutputFilesCommand
        from qubership_cli_samples.sample_command import GenerateTestOutputParamsCommand
        from qubership_cli_samples.sample_command import CalcCommand
        from qubership_cli_samples.sample_command import SampleStandaloneExecutionCommand

        from qubership_pipelines_common_library.v2.github.github_run_pipeline_command import GithubRunPipeline
        from qubership_pipelines_common_library.v2.gitlab.gitlab_run_pipeline_command import GitlabRunPipeline
        from qubership_pipelines_common_library.v2.gitlab.custom_extensions import GitlabModulesOpsPipelineDataImporter, GitlabDOBPParamsPreExt
        from qubership_pipelines_common_library.v2.jenkins.jenkins_run_pipeline_command import JenkinsRunPipeline
        from qubership_pipelines_common_library.v2.podman.podman_command import PodmanRunImage
        from qubership_pipelines_common_library.v2.pipelines.prepare_pyz_module_command import PreparePyzModule
        from qubership_pipelines_common_library.v2.notifications.send_webex_message_command import SendWebexMessage
        self.context.logger.info(f"ExecutionCommands import time: {(time.perf_counter() - start_cmd) * 1_000} ms")

    def _validate_clients(self):
        start_cmd = time.perf_counter()
        from qubership_pipelines_common_library.v1.artifactory_client import ArtifactoryClient
        from qubership_pipelines_common_library.v1.git_client import GitClient
        from qubership_pipelines_common_library.v1.github_client import GithubClient
        from qubership_pipelines_common_library.v1.gitlab_client import GitlabClient
        from qubership_pipelines_common_library.v1.jenkins_client import JenkinsClient
        from qubership_pipelines_common_library.v1.kube_client import KubeClient
        from qubership_pipelines_common_library.v1.log_client import LogClient
        from qubership_pipelines_common_library.v1.maven_client import MavenArtifactSearcher
        from qubership_pipelines_common_library.v1.minio_client import MinioClient
        from qubership_pipelines_common_library.v1.webex_client import WebexClient

        from qubership_pipelines_common_library.v2.artifacts_finder.auth.aws_credentials import AwsCredentialsProvider
        from qubership_pipelines_common_library.v2.artifacts_finder.auth.azure_credentials import AzureCredentialsProvider
        from qubership_pipelines_common_library.v2.artifacts_finder.auth.gcp_credentials import GcpCredentialsProvider
        from qubership_pipelines_common_library.v2.artifacts_finder.providers.aws_code_artifact import AwsCodeArtifactProvider
        from qubership_pipelines_common_library.v2.artifacts_finder.providers.gcp_artifact_registry import GcpArtifactRegistryProvider
        from qubership_pipelines_common_library.v2.secret_manager.providers.gcp_secret_manager import GcpSecretManagerProvider
        from qubership_pipelines_common_library.v2.secret_manager.providers.hashicorp_vault import HashicorpVaultProvider
        self.context.logger.info(f"Clients import time: {(time.perf_counter() - start_cmd) * 1_000} ms")
