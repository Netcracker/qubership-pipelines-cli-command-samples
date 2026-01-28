import time
import random
import urllib.request
import os

from pathlib import Path

from qubership_pipelines_common_library.v1.execution.exec_command import ExecutionCommand
from qubership_pipelines_common_library.v1.utils.utils_string import UtilsString


class SystemLoadTestCommand(ExecutionCommand):
    """Command to create system resource load for performance testing/debugging."""

    def _validate(self):
        names = ["paths.input.params", "paths.output.params"]
        if not self.context.validate(names):
            return False

        self.run_cpu_test = UtilsString.convert_to_bool(self.context.input_param_get("params.cpu.run_test", False))
        self.cpu_duration = float(self.context.input_param_get("params.cpu.duration", 10))
        self.cpu_load = min(max(0.1, float(self.context.input_param_get("params.cpu.load", 0.8))), 1.0)

        self.run_ram_test = UtilsString.convert_to_bool(self.context.input_param_get("params.ram.run_test", False))
        self.ram_size_mb = float(self.context.input_param_get("params.ram.size_mb", 100))
        self.ram_duration = float(self.context.input_param_get("params.ram.duration", 10))
        self.ram_chunks = int(self.context.input_param_get("params.ram.chunks", 1))
        self.ram_catch_memory_error = UtilsString.convert_to_bool(self.context.input_param_get("params.ram.catch_memory_error", True))

        self.run_network_test = UtilsString.convert_to_bool(self.context.input_param_get("params.network.run_test", False))
        self.network_url = self.context.input_param_get("params.network.url", "http://speedtest.ftp.otenet.gr/files/test100Mb.db")
        self.network_download_times = int(self.context.input_param_get("params.network.download_times", 1))

        self.sleep_between_tests = float(self.context.input_param_get("params.sleep_between_tests", 1))
        return True

    def _execute(self):
        self.context.logger.info("Running SystemLoadTestCommand")

        if not self.run_cpu_test and not self.run_ram_test and not self.run_network_test:
            self.context.logger.info("No tests enabled")
            return

        self.results = {}

        if self.run_cpu_test:
            self.context.logger.info(f"Starting CPU test: {self.cpu_duration}s, {self.cpu_load * 100:.0f}% target load")
            cpu_result = self._cpu_load_test()
            self.results.update(cpu_result)

            if self.sleep_between_tests > 0:
                self.context.logger.info(f"Sleeping {self.sleep_between_tests}s between tests")
                time.sleep(self.sleep_between_tests)

        if self.run_ram_test:
            self.context.logger.info(f"Starting RAM test: {self.ram_size_mb}MB for {self.ram_duration}s")
            ram_result = self._ram_load_test()
            self.results.update(ram_result)

            if self.sleep_between_tests > 0:
                self.context.logger.info(f"Sleeping {self.sleep_between_tests}s between tests")
                time.sleep(self.sleep_between_tests)

        if self.run_network_test:
            self.context.logger.info(f"Starting Network test: {self.network_download_times} download(s) of {self.network_url}")
            network_result = self._network_load_test()
            self.results.update(network_result)

        for key, value in self.results.items():
            self.context.output_param_set(f"params.test_results.{key}", value)
        self.context.output_params_save()

        self.context.logger.info("Finished SystemLoadTestCommand, results are stored in output params")

    def _cpu_load_test(self):
        results = {}
        try:
            start_time = time.time()
            end_time = start_time + self.cpu_duration
            iteration = 0
            while time.time() < end_time:
                busy_end = time.time() + 0.01
                while time.time() < busy_end:
                    iteration += 1
                    _ = (iteration * 3.14159) ** 0.5
                if self.cpu_load < 1.0:
                    elapsed = time.time() - start_time
                    target_busy_time = elapsed * self.cpu_load
                    actual_busy_time = elapsed - (elapsed * (1 - self.cpu_load))
                    sleep_needed = max(0, (target_busy_time - actual_busy_time) / self.cpu_load)
                    if sleep_needed > 0:
                        time.sleep(min(sleep_needed, 0.05))

            elapsed = time.time() - start_time
            results["cpu.elapsed_seconds"] = f"{elapsed:.2f}"
            results["cpu.iterations"] = iteration
            results["cpu.target_load_percent"] = f"{self.cpu_load * 100:.1f}"
            self.context.logger.info(f"CPU test completed: {elapsed:.2f}s, {iteration} iterations")
        except Exception as e:
            self.context.logger.error(f"CPU test failed: {e}")
            results["cpu.error"] = str(e)
        return results

    def _ram_load_test(self):
        results = {}
        allocated_memory = []
        try:
            chunk_size = int((self.ram_size_mb * 1024 * 1024) / self.ram_chunks)
            self.context.logger.info(f"Allocating {self.ram_size_mb}MB RAM in {self.ram_chunks} chunk(s)")

            for i in range(self.ram_chunks):
                chunk = bytearray(chunk_size)
                for j in range(0, len(chunk), 4096):
                    chunk[j] = random.randint(0, 255)
                allocated_memory.append(chunk)
                current_mb = (i + 1) * chunk_size / (1024 * 1024)
                self.context.logger.debug(f"Allocated {current_mb:.1f}MB so far")

            start_time = time.time()
            time.sleep(self.ram_duration)
            elapsed = time.time() - start_time

            results["ram.elapsed_seconds"] = f"{elapsed:.2f}"
            results["ram.requested_mb"] = f"{self.ram_size_mb:.1f}"
            results["ram.chunks"] = self.ram_chunks
            self.context.logger.info(f"RAM test completed: {self.ram_size_mb}MB held for {elapsed:.2f}s")

        except MemoryError:
            self.context.logger.error(f"MemoryError: Could not allocate {self.ram_size_mb}MB")
            results["ram.error"] = "MemoryError - allocation failed"
            if not self.ram_catch_memory_error:
                raise
        except Exception as e:
            self.context.logger.error(f"RAM test failed: {e}")
            results["ram.error"] = str(e)
        finally:
            allocated_memory.clear()
            import gc
            gc.collect()

        return results

    def _network_load_test(self):
        results = {}
        download_times = []
        files_to_cleanup = []

        try:
            output_dir = Path(self.context.input_param_get("paths.output.files", "."))
            output_dir.mkdir(parents=True, exist_ok=True)
            total_bytes = 0

            for i in range(self.network_download_times):
                filename = f"download_{i}_{int(time.time())}.tmp"
                filepath = output_dir / filename
                files_to_cleanup.append(filepath)

                self.context.logger.info(f"Downloading {self.network_url} to {filename}")

                start_time = time.time()
                urllib.request.urlretrieve(self.network_url, filepath)
                elapsed = time.time() - start_time

                file_size = os.path.getsize(filepath)
                total_bytes += file_size
                download_times.append(elapsed)

            if download_times:
                results["network.downloads"] = len(download_times)
                results["network.total_mb"] = f"{total_bytes / 1024 / 1024:.2f}"
                results["network.avg_time"] = f"{sum(download_times) / len(download_times):.2f}"
                results["network.avg_speed_mbps"] = f"{(total_bytes * 8) / (sum(download_times) * 1_000_000):.2f}"

        except Exception as e:
            results["network.error"] = str(e)
            self.context.logger.error(f"Network test failed: {e}")

        finally:
            for filepath in files_to_cleanup:
                try:
                    if filepath.exists():
                        filepath.unlink()
                        self.context.logger.debug(f"Deleted {filepath.name}")
                except Exception:
                    pass

        return results
