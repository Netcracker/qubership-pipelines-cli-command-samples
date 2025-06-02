import logging
import os
import subprocess
import unittest
import yaml
from pathlib import Path

QUBER_CLI = "qubership_cli_samples"


class TestSampleCLICommands(unittest.TestCase):

    def setUp(self):
        logging.info(os.getcwd())

    def test_help(self):
        output = subprocess.run(["python", QUBER_CLI, "--help"], capture_output = True, text = True)
        self.assertTrue("Commands:" in output.stdout + output.stderr)

    def test_run_sample(self):
        output = subprocess.run(["python", QUBER_CLI, "run-sample", "--context_path=./data/context.yaml"], capture_output = True, text = True)
        with open('./data/result.yaml', 'r', encoding='utf-8') as file:
            result = yaml.safe_load(file)
            self.assertEqual(19,  result['params']['result'])

    def test_calc_sample(self):
        output = subprocess.run(["python", QUBER_CLI, "calc", "--context_path=./data/context2.yaml"], capture_output = True, text = True)
        with open('./data/result_calc.yaml', 'r', encoding='utf-8') as file:
            result = yaml.safe_load(file)
            self.assertEqual(0.9,  result['params']['result_divide'])

    # def test_umbrella(self):
    #     subprocess.run(["python", QUBER_CLI, "umbrella-test"])
    #     result_files = [p.as_posix() for p in list(Path("./RESULTS_FOLDER").rglob("*/response_data/*"))]
    #     self.assertTrue("RESULTS_FOLDER/output/files/run1_result/response_data/name_from_first_job.txt" in result_files)


if __name__ == '__main__':
    unittest.main()
