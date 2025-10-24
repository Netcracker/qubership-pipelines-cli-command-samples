FROM bitnamilegacy/python:3.11.11-debian-12-r0
LABEL org.opencontainers.image.description Sample Image with Qubership Pipelines CLI samples inside

ADD https://github.com/Netcracker/qubership-pipelines-cli-command-samples/releases/latest/download/qubership_cli_samples.pyz /usr/quber/
RUN pip install cffi
RUN unzip -q /usr/quber/qubership_cli_samples.pyz -d /usr/quber/module_cli
RUN apt-get install -y git
