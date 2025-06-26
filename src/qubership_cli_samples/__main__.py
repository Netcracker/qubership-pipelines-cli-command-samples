import os, sys, logging, click

from qubership_cli_samples.file_processing.file_commands import DownloadFileExecutionCommand, AnalyzeFileExecutionCommand, GenerateContextFromEnv
from qubership_cli_samples.github.github_command import GithubRunPipeline
from qubership_cli_samples.minio_commands import ListMinioBucketObjectsCommand
from qubership_cli_samples.report.report_command import BuildReport
from qubership_cli_samples.sample_command import SampleStandaloneExecutionCommand, CalcCommand
from qubership_pipelines_common_library.v1.execution.exec_logger import ExecutionLogger
from qubership_cli_samples.umbrella_test.umbrella_command import UmbrellaCommand
from qubership_pipelines_common_library.v1.utils.utils_cli import utils_cli


@click.group(chain=True)
def cli():
    #logging.basicConfig(stream=sys.stdout, format=ExecutionLogger.DEFAULT_FORMAT, level=logging.INFO)
    current_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_path)
    #urllib3.disable_warnings()


@cli.command("run-sample")
@utils_cli
def __run_sample(**kwargs):
    command = SampleStandaloneExecutionCommand(**kwargs)
    command.run()


@cli.command("calc")
@utils_cli
def __calc(**kwargs):
    command = CalcCommand(**kwargs)
    command.run()


@cli.command("list-minio-files")
@utils_cli
def __list(**kwargs):
    command = ListMinioBucketObjectsCommand(**kwargs)
    command.run()


@cli.command("umbrella-test")
@utils_cli
def __devtest(**kwargs):
    command = UmbrellaCommand(folder_path="./RESULTS_FOLDER", input_params={"systems": {"gitlab": {"url": "https://gitlab.com"}}})
    command.run()


@cli.command("download-file")
@utils_cli
def __download_file(**kwargs):
    command = DownloadFileExecutionCommand(**kwargs)
    command.run()


@cli.command("analyze-file")
@utils_cli
def __download_file(**kwargs):
    command = AnalyzeFileExecutionCommand(**kwargs)
    command.run()


@cli.command("generate-context-from-env")
@click.option('--context_folder', required=True, type=str, help="Path to context folder to create")
@utils_cli
def __generate_context_from_env(context_folder, **kwargs):
    command = GenerateContextFromEnv(input_params={"params": {"context_folder": context_folder}})
    command.run()


@cli.command("github-run-pipeline")
@utils_cli
def __trigger_github_pipeline(**kwargs):
    command = GithubRunPipeline(**kwargs)
    command.run()


@cli.command("generate-html-report")
@utils_cli
def __trigger_github_pipeline(**kwargs):
    command = BuildReport(**kwargs)
    command.run()
