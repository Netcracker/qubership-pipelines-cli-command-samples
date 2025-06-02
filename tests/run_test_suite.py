import logging
import os, pytest
import sys
from _pytest.config import Config

ZIPAPP_PATH = "../qubership_cli_samples.pyz"


class ResultsCollector:
    def __init__(self):
        self.report = []

    def get_short_summary(self):
        if not self.report:
            return None
        index = len(self.report) - 1
        try:
            index = next(idx for idx, string in enumerate(self.report) if "short test summary info" in string)
        except:
            pass
        return "\n".join(self.report[index:])

    @pytest.hookimpl(trylast=True)
    def pytest_configure(self, config: Config):
        tr = config.pluginmanager.getplugin("terminalreporter")
        if tr is not None:
            oldwrite = tr._tw.write
            def tee_write(s, **kwargs):
                oldwrite(s, **kwargs)
                if isinstance(s, str) and s != "\n":
                    self.report.append(s)
            tr._tw.write = tee_write


def sizeof_fmt(num, suffix="B"):
    for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
        if abs(num) < 1024.0:
            return f"{num:3.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} Yi{suffix}"


def write_step_summary(text: str):
    print(text)
    with open(os.getenv('GITHUB_STEP_SUMMARY'), 'w') as summary_file:
        summary_file.write(text)


def report_execution_result(is_success: bool, error: Exception = None, test_report: str = None):
    zipapp_size = sizeof_fmt(os.path.getsize(ZIPAPP_PATH))
    message = f"""### Validate test results report:
- Result is {"SUCCESS :white_check_mark:" if is_success else "FAILURE :x:"}
- Resulting zipapp artifact size is **{zipapp_size}**
- Used version: {os.getenv('QUBERSHIP_VERSION', "UNKNOWN")}
    """
    if error:
        message += f"\n\nError message:\n```{type(error)} - {error}```"
    if test_report:
        message += f"\n```\n{test_report}\n```"
    write_step_summary(message)


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                        format=u'[%(asctime)s] [%(levelname)-s] [%(filename)s]: %(message)s')
    pytest_report_collector = ResultsCollector()
    try:
        os.chdir("./tests")
        res = pytest.main(args=["./cli"], plugins=[pytest_report_collector])
        if res != 0:
            raise Exception("Tests failed!")
        report_execution_result(True, test_report=pytest_report_collector.get_short_summary())
    except Exception as e:
        report_execution_result(False, e, test_report=pytest_report_collector.get_short_summary())
        exit(1984)
