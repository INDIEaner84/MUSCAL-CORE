import os
import subprocess
import yaml
import config


class TestContainerDeployment:
    def test_config_env_injection(self):
        assert config.RUNTIME_FLASK_PORT == 5001
        assert config.OLLAMA_BASE is not None
        assert config.DB_PATH is not None

    def test_containerfile_exists_with_from(self):
        result = subprocess.run(
            ["head", "-1", "Containerfile"],
            capture_output=True, text=True
        )
        assert result.returncode == 0 and "FROM" in result.stdout

    def test_containerfile_is_multi_stage(self):
        with open("Containerfile") as f:
            content = f.read()
        assert "AS builder" in content
        assert "COPY --from=builder" in content

    def test_containerfile_cmd_contains_supervisor(self):
        with open("Containerfile") as f:
            content = f.read()
        assert "supervisor.py" in content

    def test_supervisor_imports_cleanly(self):
        import supervisor as _sup_mod
        assert hasattr(_sup_mod, "start")

    def test_compose_yml_exists_with_valid_yaml(self):
        with open("compose.yml") as f:
            compose = yaml.safe_load(f)
        assert "services" in compose
        assert "muscal" in compose["services"]
        muscal = compose["services"]["muscal"]
        assert "healthcheck" in muscal
        assert "ports" in muscal

    def test_compose_yml_security_hardening(self):
        with open("compose.yml") as f:
            compose = yaml.safe_load(f)
        muscal = compose["services"]["muscal"]
        assert muscal.get("user") == "1000:1000"
        assert muscal.get("init") is True
        assert muscal.get("read_only") is True
        assert "tmpfs" in muscal
        assert muscal.get("cap_drop") == ["ALL"]
        assert "no-new-privileges" in str(muscal.get("security_opt", []))
        assert muscal.get("restart") == "unless-stopped"
        assert muscal.get("stop_grace_period") == "30s"

    def test_api_has_ready_and_live_endpoints(self):
        from runtime.api import create_app, set_server_ready, _rate_limiter
        _rate_limiter._windows.clear()
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        resp_live = client.get("/api/live")
        assert resp_live.status_code == 200
        assert resp_live.json["status"] == "alive"

        set_server_ready(False)
        resp_ready_not = client.get("/api/ready")
        assert resp_ready_not.status_code == 503

        set_server_ready(True)
        resp_ready_ok = client.get("/api/ready")
        assert resp_ready_ok.status_code == 200
        assert resp_ready_ok.json["status"] == "ready"

    def test_env_example_has_required_keys(self):
        required_keys = ["MUSCAL_ENV", "MUSCAL_MODE", "OLLAMA_BASE", "RUNTIME_FLASK_PORT"]
        with open(".env.example") as f:
            content = f.read()
        for key in required_keys:
            assert key in content

    def test_containerignore_exists(self):
        assert os.path.isfile(".containerignore")
        assert os.path.isfile(".dockerignore")

    def test_docker_files_removed(self):
        assert not os.path.isfile("Dockerfile")
        assert not os.path.isfile("docker-compose.yml")
