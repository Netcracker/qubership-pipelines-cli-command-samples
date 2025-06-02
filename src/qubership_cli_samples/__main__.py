import os, sys, logging, click

from qubership_cli_samples.file_processing.file_commands import DownloadFileExecutionCommand, AnalyzeFileExecutionCommand, GenerateContextFromEnv
from qubership_cli_samples.github.github_command import GithubRunPipeline
from qubership_cli_samples.minio_commands import ListMinioBucketObjectsCommand
from qubership_cli_samples.report.report_command import BuildReport
from qubership_cli_samples.sample_command import SampleStandaloneExecutionCommand, CalcCommand
from qubership_pipelines_common_library.v1.execution.exec_logger import ExecutionLogger
from qubership_cli_samples.umbrella_test.umbrella_command import UmbrellaCommand

DEFAULT_CONTEXT_FILE_PATH = 'context.yaml'


@click.group(chain=True)
def cli():
    logging.basicConfig(stream=sys.stdout, format=ExecutionLogger.DEFAULT_FORMAT, level=logging.INFO)
    current_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_path)
    #urllib3.disable_warnings()


@cli.command("run-sample")
@click.option('--context_path', required=True, default=DEFAULT_CONTEXT_FILE_PATH, type=str, help="Path to context")
def __run_sample(context_path):
    command = SampleStandaloneExecutionCommand(context_path)
    command.run()


@cli.command("calc")
@click.option('--context_path', required=True, default=DEFAULT_CONTEXT_FILE_PATH, type=str, help="Path to context")
def __calc(context_path):
    command = CalcCommand(context_path)
    command.run()


@cli.command("list-minio-files")
@click.option('--context_path', required=True, default=DEFAULT_CONTEXT_FILE_PATH, type=str, help="Path to context")
def __list(context_path):
    command = ListMinioBucketObjectsCommand(context_path)
    command.run()


@cli.command("umbrella-test")
def __devtest():
    command = UmbrellaCommand(folder_path="./RESULTS_FOLDER", input_params={"systems": {"gitlab": {"url": "https://gitlab.com"}}})
    command.run()


@cli.command("download-file")
@click.option('--context_path', required=True, default=DEFAULT_CONTEXT_FILE_PATH, type=str, help="Path to context")
def __download_file(context_path):
    command = DownloadFileExecutionCommand(context_path)
    command.run()


@cli.command("analyze-file")
@click.option('--context_path', required=True, default=DEFAULT_CONTEXT_FILE_PATH, type=str, help="Path to context")
def __download_file(context_path):
    command = AnalyzeFileExecutionCommand(context_path)
    command.run()


@cli.command("generate-context-from-env")
@click.option('--context_folder', required=True, type=str, help="Path to context folder to create")
def __generate_context_from_env(context_folder):
    command = GenerateContextFromEnv(input_params={"params": {"context_folder": context_folder}})
    command.run()


@cli.command("github-run-pipeline")
@click.option('--context_path', required=True, default=DEFAULT_CONTEXT_FILE_PATH, type=str, help="Path to context")
def __trigger_github_pipeline(context_path):
    command = GithubRunPipeline(context_path)
    command.run()


@cli.command("generate-html-report")
@click.option('--context_path', required=True, default=DEFAULT_CONTEXT_FILE_PATH, type=str, help="Path to context")
def __trigger_github_pipeline(context_path):
    command = BuildReport(context_path)
    command.run()
