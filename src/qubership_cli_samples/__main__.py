import time
start_time = time.perf_counter()
import os, sys, click, logging
from qubership_pipelines_common_library.v1.utils.utils_cli import utils_cli


@click.group(chain=True)
def cli():
    current_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_path)


@cli.command("run-sample")
@utils_cli
def __run_sample(**kwargs):
    from qubership_cli_samples.sample_command import SampleStandaloneExecutionCommand
    command = SampleStandaloneExecutionCommand(**kwargs)
    command.run()


@cli.command("calc")
@utils_cli
def __calc(**kwargs):
    from qubership_cli_samples.sample_command import CalcCommand
    command = CalcCommand(**kwargs)
    command.run()


@cli.command("spam")
@utils_cli
def __spam(**kwargs):
    logging.info(f"Common imports: {(time.perf_counter() - start_time) * 1_000} ms")
    start_cmd_import = time.perf_counter()
    from qubership_cli_samples.sample_command import GenerateTestOutputParamsCommand
    logging.info(f"Cmd import: {(time.perf_counter() - start_cmd_import) * 1_000} ms")
    start_cmd = time.perf_counter()
    try:
        command = GenerateTestOutputParamsCommand(**kwargs)
        command.run()
    finally:
        logging.info(f"Cmd run time: {(time.perf_counter() - start_cmd) * 1_000} ms")


@cli.command("spam-files")
@utils_cli
def __spam_files(**kwargs):
    logging.info(f"Common imports: {(time.perf_counter() - start_time) * 1_000} ms")
    start_cmd_import = time.perf_counter()
    from qubership_cli_samples.sample_command import GenerateTestOutputFilesCommand
    logging.info(f"Cmd import: {(time.perf_counter() - start_cmd_import) * 1_000} ms")
    start_cmd = time.perf_counter()
    try:
        command = GenerateTestOutputFilesCommand(**kwargs)
        command.run()
    finally:
        logging.info(f"Cmd run time: {(time.perf_counter() - start_cmd) * 1_000} ms")


@cli.command("spam-module-report")
@utils_cli
def __spam_module_report(**kwargs):
    logging.info(f"Common imports: {(time.perf_counter() - start_time) * 1_000} ms")
    start_cmd_import = time.perf_counter()
    from qubership_cli_samples.sample_command import GenerateTestModuleReportCommand
    logging.info(f"Cmd import: {(time.perf_counter() - start_cmd_import) * 1_000} ms")
    start_cmd = time.perf_counter()
    try:
        command = GenerateTestModuleReportCommand(**kwargs)
        command.run()
    finally:
        logging.info(f"Cmd run time: {(time.perf_counter() - start_cmd) * 1_000} ms")


@cli.command("list-minio-files")
@utils_cli
def __list_minio_files(**kwargs):
    from qubership_cli_samples.minio_commands import ListMinioBucketObjectsCommand
    command = ListMinioBucketObjectsCommand(**kwargs)
    command.run()


@cli.command("umbrella-test")
@utils_cli
def __umbrella_test(**kwargs):
    from qubership_cli_samples.umbrella_test.umbrella_command import UmbrellaCommand
    command = UmbrellaCommand(folder_path="./RESULTS_FOLDER", input_params={"systems": {"gitlab": {"url": "https://gitlab.com"}}})
    command.run()


@cli.command("download-file")
@utils_cli
def __download_file(**kwargs):
    from qubership_cli_samples.file_processing.file_commands import DownloadFileExecutionCommand
    command = DownloadFileExecutionCommand(**kwargs)
    command.run()


@cli.command("analyze-file")
@utils_cli
def __analyze_file(**kwargs):
    from qubership_cli_samples.file_processing.file_commands import AnalyzeFileExecutionCommand
    command = AnalyzeFileExecutionCommand(**kwargs)
    command.run()


@cli.command("generate-context-from-env")
@click.option('--context_folder', required=True, type=str, help="Path to context folder to create")
@utils_cli
def __generate_context_from_env(context_folder, **kwargs):
    from qubership_cli_samples.file_processing.file_commands import GenerateContextFromEnv
    command = GenerateContextFromEnv(input_params={"params": {"context_folder": context_folder}})
    command.run()


@cli.command("github-run-pipeline")
@utils_cli
def __trigger_github_pipeline(**kwargs):
    from qubership_cli_samples.github.github_command import GithubRunPipeline
    command = GithubRunPipeline(**kwargs)
    command.run()


@cli.command("generate-html-report")
@utils_cli
def __generate_html_report(**kwargs):
    from qubership_cli_samples.report.report_command import BuildReport
    command = BuildReport(**kwargs)
    command.run()
