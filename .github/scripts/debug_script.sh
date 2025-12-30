set -e
unzip -q ./qubership_cli_samples.pyz -d ./debug_cli

# disable rich logs:
# export NO_RICH="true"
# export NO_COLOR=1


python debug_cli spam -p params__just_param=qwe
python debug_cli spam-files -p params__just_param=qwe
