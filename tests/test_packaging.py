from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_runtime_files_exist() -> None:
    required_files = [
        ROOT / ".env.example",
        ROOT / "Dockerfile",
        ROOT / "compose.yaml",
        ROOT / "scripts" / "build.sh",
        ROOT / "scripts" / "run.sh",
        ROOT / "scripts" / "dev.sh",
    ]

    missing = [str(path.relative_to(ROOT)) for path in required_files if not path.is_file()]
    assert missing == []


def test_shell_scripts_have_valid_syntax() -> None:
    for script in ("build.sh", "run.sh", "dev.sh"):
        result = subprocess.run(
            ["bash", "-n", str(ROOT / "scripts" / script)],
            capture_output=True,
            check=False,
            text=True,
        )
        assert result.returncode == 0, result.stderr


def test_native_scripts_keep_virtualenv_outside_noexec_project_mount() -> None:
    for script in ("run.sh", "dev.sh"):
        content = (ROOT / "scripts" / script).read_text(encoding="utf-8")
        assert "POLAR_APP_VENV" in content
        assert "XDG_CACHE_HOME" in content
        assert "UV_PROJECT_ENVIRONMENT" in content


def test_native_scripts_support_user_local_uv_installation() -> None:
    for script in ("run.sh", "dev.sh"):
        content = (ROOT / "scripts" / script).read_text(encoding="utf-8")
        assert "UV_BIN" in content
        assert '$HOME/.hermes/bin/uv' in content
        assert '$HOME/.local/bin/uv' in content


def test_frontend_scripts_use_external_cache_on_noexec_mount() -> None:
    build_script = (ROOT / "scripts" / "build.sh").read_text(encoding="utf-8")
    dev_script = (ROOT / "scripts" / "dev.sh").read_text(encoding="utf-8")

    for content in (build_script, dev_script):
        assert "XDG_CACHE_HOME" in content
        assert "POLAR_FRONTEND_WORKSPACE" in content
    assert 'npm ci --prefix "$FRONTEND_DIR"' not in build_script


def test_runtime_paths_use_prepared_src_directory() -> None:
    build_script = (ROOT / "scripts" / "build.sh").read_text(encoding="utf-8")
    run_script = (ROOT / "scripts" / "run.sh").read_text(encoding="utf-8")
    dev_script = (ROOT / "scripts" / "dev.sh").read_text(encoding="utf-8")
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert '$ROOT_DIR/src/frontend' in build_script
    assert '$ROOT_DIR/src/backend' in build_script
    assert '$ROOT_DIR/src/backend' in run_script
    assert '$ROOT_DIR/src/frontend' in dev_script
    assert '$ROOT_DIR/src/backend' in dev_script
    assert "COPY src/frontend/" in dockerfile
    assert "COPY src/backend/" in dockerfile


def test_compose_configuration_is_valid_and_persists_database() -> None:
    result = subprocess.run(
        ["docker", "compose", "config"],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert str(ROOT / "database") in result.stdout
    assert "/app/database" in result.stdout


def test_dockerfile_builds_frontend_before_python_runtime() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    node_stage = dockerfile.index("FROM node:")
    python_stage = dockerfile.index("FROM python:")
    frontend_build = dockerfile.index("npm run build")

    assert node_stage < frontend_build < python_stage
    assert "COPY --from=frontend-build" in dockerfile


def test_example_environment_contains_no_assigned_secret() -> None:
    env_lines = (ROOT / ".env.example").read_text(encoding="utf-8").splitlines()
    secret_names = ("SECRET", "TOKEN", "PASSWORD", "CLIENT_ID")

    for line in env_lines:
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        if any(secret_name in name.upper() for secret_name in secret_names):
            assert value.strip() == ""
