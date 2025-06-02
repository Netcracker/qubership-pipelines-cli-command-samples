## Development Guide

<!-- TOC -->
  * [Development Guide](#development-guide)
    * [Adding new commands](#adding-new-commands)
    * [Working with external services](#working-with-external-services)
<!-- TOC -->


### Adding new commands

New commands should all extend `ExecutionCommand` class. This project provides several examples of commands that work via context files (and it's the intended way of using qubership-common-library, since it's made for using in devops pipelines)

Library itself provides methods of working with context and params files.

The most straightforward example is `SampleStandaloneExecutionCommand`, which is mapped to `@cli.command("run-sample")` CLI command.

It expects to receive location of [`context.yaml` file](../tests/data/context.yaml) (or looks for it in working directory), which points to locations of [input parameters](../tests/data/params.yaml) and where to put resulting report.

The usual `ExecutionCommand` lifecycle consists of
- validating required input parameters (that will be automatically parsed from context)
- performing work and logging its results per agreed contract
 
In our example - this sample command just sums up two integer parameters and writes them into `results.yaml`


### Working with external services
- [MiniO Guide](../docs/minio.md)
- TBD...
