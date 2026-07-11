import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


def _find_runtime():
    for exe in ("podman", "docker"):
        if shutil.which(exe):
            return exe
    return None


pytestmark = pytest.mark.skipif(
    _find_runtime() is None,
    reason="no container runtime (podman/docker) available",
)


@pytest.fixture(scope="session")
def runtime():
    r = _find_runtime()
    if r is None:
        pytest.skip("no container runtime")
    return r


@pytest.fixture(scope="session")
def project_root():
    return Path(__file__).resolve().parents[4]


@pytest.fixture(scope="session")
def image_tag():
    return "muscal-core-test:latest"


@pytest.fixture(scope="session")
def build_image(runtime, project_root, image_tag):
    subprocess.run(
        [runtime, "build", "-t", image_tag, "-f", str(project_root / "Dockerfile"), str(project_root)],
        check=True, capture_output=True, text=True,
    )
    yield image_tag
    subprocess.run([runtime, "rmi", "--force", image_tag], capture_output=True)


@pytest.fixture
def container_name():
    return "muscal-core-test-container"


@pytest.fixture
def data_dir():
    with tempfile.TemporaryDirectory(prefix="muscal-test-data-") as tmp:
        yield Path(tmp)
