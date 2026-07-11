import subprocess
import time

import pytest


class TestContainerRun:
    def test_health_endpoint_reachable(self, runtime, build_image, container_name, data_dir):
        subprocess.run(
            [runtime, "run", "--rm", "--name", container_name,
             "-p", "8000:8000",
             "-v", f"{data_dir}:/app/data:Z",
             "-d", build_image],
            check=True, capture_output=True, text=True,
        )
        time.sleep(5)
        try:
            result = subprocess.run(
                [runtime, "exec", container_name,
                 "python", "-c",
                 "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health').read().decode())"],
                capture_output=True, text=True, timeout=10,
            )
            assert result.returncode == 0
            assert '"status": "ok"' in result.stdout
        finally:
            subprocess.run([runtime, "stop", "--time", "5", container_name], capture_output=True)
            subprocess.run([runtime, "wait", container_name], capture_output=True)
            subprocess.run([runtime, "rm", "--force", container_name], capture_output=True)

    def test_sigterm_shutdown(self, runtime, build_image, container_name, data_dir):
        subprocess.run(
            [runtime, "run", "--rm", "--name", container_name,
             "-p", "8001:8000",
             "-v", f"{data_dir}:/app/data:Z",
             "-d", build_image],
            check=True, capture_output=True, text=True,
        )
        time.sleep(3)
        try:
            subprocess.run([runtime, "stop", "--time", "10", container_name], check=True, capture_output=True, timeout=15)
            result = subprocess.run([runtime, "wait", container_name], capture_output=True, text=True, timeout=15)
            assert result.returncode == 0
        finally:
            subprocess.run([runtime, "rm", "--force", container_name], capture_output=True)

    def test_logs_available(self, runtime, build_image, container_name, data_dir):
        subprocess.run(
            [runtime, "run", "--rm", "--name", container_name,
             "-p", "8002:8000",
             "-v", f"{data_dir}:/app/data:Z",
             "-d", build_image],
            check=True, capture_output=True, text=True,
        )
        time.sleep(3)
        try:
            result = subprocess.run(
                [runtime, "logs", container_name],
                capture_output=True, text=True, timeout=10,
            )
            assert result.returncode == 0
            assert len(result.stdout) > 0 or len(result.stderr) > 0
        finally:
            subprocess.run([runtime, "stop", "--time", "5", container_name], capture_output=True)
            subprocess.run([runtime, "wait", container_name], capture_output=True)
            subprocess.run([runtime, "rm", "--force", container_name], capture_output=True)

    def test_volume_mounted(self, runtime, build_image, container_name, data_dir):
        subprocess.run(
            [runtime, "run", "--rm", "--name", container_name,
             "-p", "8003:8000",
             "-v", f"{data_dir}:/app/data:Z",
             "-d", build_image],
            check=True, capture_output=True, text=True,
        )
        time.sleep(3)
        try:
            result = subprocess.run(
                [runtime, "exec", container_name, "test", "-d", "/app/data"],
                capture_output=True, text=True, timeout=10,
            )
            assert result.returncode == 0
            assert data_dir.is_dir()
        finally:
            subprocess.run([runtime, "stop", "--time", "5", container_name], capture_output=True)
            subprocess.run([runtime, "wait", container_name], capture_output=True)
            subprocess.run([runtime, "rm", "--force", container_name], capture_output=True)
