import yaml

from pathlib import Path
from qubership_pipelines_common_library.v1.execution.exec_command import ExecutionCommand
from importlib import resources
from qubership_cli_samples import report


class BuildReport(ExecutionCommand):

    def _validate(self):
        return True

    def _execute(self):
        report_data_path = Path(self.context.input_param_get("paths.input.files")).joinpath("execution_report.yaml")
        with open(report_data_path, 'r') as rd:
            report_data = yaml.safe_load(rd.read())

        html_template_path = self.context.input_param_get("paths.input.params.report_template", None)
        html_template_str = self._load_template(html_template_path)

        html_content = self._generate_html(report_data, html_template_str)
        target_path = Path(self.context.input_param_get("paths.output.files")).joinpath("report.html")
        with open(target_path, 'w') as fs:
            fs.write(html_content)

        self.context.logger.info("HTML report generated successfully!")

    def _load_template(self, template_path):
        try:
            if not template_path:
                inp_file = resources.files(report) / 'default_report_template.html'
                with inp_file.open("r", encoding="utf-8") as f:
                    return f.read()
            with open(template_path, "r", encoding="utf-8") as template_file:
                return template_file.read()
        except FileNotFoundError:
            self.context.logger.error(f"Template file not found: {template_path}")
            raise
        except Exception as e:
            self.context.logger.error(f"Error loading template file: {template_path}. Error: {str(e)}")
            raise

    def _generate_html(self, report_data, template_str):
        # Extract execution details
        execution = report_data.get("execution", {})
        stages = report_data.get("stages", [])

        # Prepare stages HTML
        stages_html = ""
        for index, stage in enumerate(stages, start=1):
            stage_exec = stage.get("execution", {})  # Access execution directly
            result_class = "success" if stage_exec.get("result") == "SUCCESS" else "failed"
            stages_html += f"""
                <tr>
                    <td>{index}</td>
                    <td>{stage_exec.get("name", "N/A")}</td>
                    <td class="{result_class}">{stage_exec.get("result", "N/A")}</td>
                    <td>{stage_exec.get("time", "N/A")}</td>
                    <td><a href="{stage_exec.get("url", "#")}">{stage_exec.get("url", "N/A")}</a></td>
                </tr>
            """

        # Populate the template with data
        html_report = template_str.format(
            apiVersion=report_data.get("apiVersion", "N/A"),
            user=execution.get("user", "Unknown User"),
            email=execution.get("email", "unknown@example.com"),
            started=execution.get("started", "N/A"),
            time=execution.get("time", "N/A"),
            result=execution.get("result", "N/A"),
            url=execution.get("url", "#"),
            stages=stages_html
        )

        return html_report