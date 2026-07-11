import pytest


class TestContainerBuild:
    def test_build_succeeds(self, build_image):
        assert build_image
