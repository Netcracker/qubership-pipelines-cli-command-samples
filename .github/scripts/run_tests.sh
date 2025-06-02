python -m venv .venv

unzip -q ./qubership_cli_samples.pyz -d ./tests/qubership_cli_samples
pip install -q -r ./.github/scripts/requirements.txt
python ./tests/run_test_suite.py