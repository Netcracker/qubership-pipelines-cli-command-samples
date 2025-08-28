set -e
python -m venv .venv

poetry build
pip install -q --target pack --no-compile --upgrade dist/*.whl
./.github/scripts/reduce_botocore.sh
python -m zipapp pack -o ./qubership_cli_samples.pyz --main=qubership_cli_samples.__main__:cli --compress
export QUBERSHIP_VERSION="$(pip freeze --path pack | grep qubership-pipelines-common-library)"
echo Build done!
