"""Regressões do instalador: não depender de pip/venv/ensurepip do kernel."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import types
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]


def support():
    spec = importlib.util.spec_from_file_location("bootstrap_under_test", ROOT / "scripts/eca_colab_support.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fake_wheel(module, monkeypatch, *, corrupt=False):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(f"uv-{module.UV_VERSION}.data/scripts/uv", b"fake uv executable")
        archive.writestr("../../must_not_extract", b"unexpected member")
    payload = buffer.getvalue()
    digest = "0" * 64 if corrupt else hashlib.sha256(payload).hexdigest()
    monkeypatch.setattr(module.platform, "system", lambda: "Linux")
    monkeypatch.setattr(module.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(module, "UV_WHEELS", {
        ("Linux", "x86_64"): ("https://files.pythonhosted.org/test.whl", digest)})
    monkeypatch.setattr(module, "urlopen", lambda *a, **kw: io.BytesIO(payload))
    return payload


def fake_uv_run(calls):
    def run(command, **kwargs):
        calls.append(command)
        # Reproduz a indisponibilidade de pip/venv/ensurepip no Python hospedeiro.
        assert "-m" not in command
        assert command[-1] == "--version"
        return subprocess.CompletedProcess(command, 0, stdout="uv 0.12.9\n", stderr="")
    return run


def test_bootstrap_works_without_host_venv_or_pip(monkeypatch, tmp_path):
    module = support()
    fake_wheel(module, monkeypatch)
    calls = []
    monkeypatch.setattr(module.subprocess, "run", fake_uv_run(calls))
    result = Path(module._bootstrap_uv(tmp_path))
    assert result.read_bytes() == b"fake uv executable"
    assert result.parent == tmp_path / ".eca-uv-bootstrap-v322"
    assert len(calls) == 1
    assert not (tmp_path / "must_not_extract").exists()


def test_bootstrap_bad_sha256_never_executes(monkeypatch, tmp_path):
    module = support()
    fake_wheel(module, monkeypatch, corrupt=True)
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **kw: pytest.fail("unverified executable"))
    with pytest.raises(RuntimeError, match="SHA-256"):
        module._bootstrap_uv(tmp_path)
    assert not (tmp_path / ".eca-uv-bootstrap-v322").exists()


def test_bootstrap_reentry_does_not_download(monkeypatch, tmp_path):
    module = support()
    fake_wheel(module, monkeypatch)
    monkeypatch.setattr(module.subprocess, "run", fake_uv_run([]))
    first = module._bootstrap_uv(tmp_path)
    monkeypatch.setattr(module, "urlopen", lambda *a, **kw: pytest.fail("re-download"))
    assert module._bootstrap_uv(tmp_path) == first


def test_modified_cached_binary_is_rejected(monkeypatch, tmp_path):
    module = support()
    fake_wheel(module, monkeypatch)
    monkeypatch.setattr(module.subprocess, "run", fake_uv_run([]))
    binary = Path(module._bootstrap_uv(tmp_path))
    binary.write_bytes(b"modified")
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **kw: pytest.fail("modified executable"))
    with pytest.raises(RuntimeError, match="integridade"):
        module._bootstrap_uv(tmp_path)


def test_bootstrap_preserves_foreign_directory(monkeypatch, tmp_path):
    module = support()
    fake_wheel(module, monkeypatch)
    destination = tmp_path / ".eca-uv-bootstrap-v322"
    destination.mkdir()
    note = destination / "research.txt"
    note.write_text("preserve")
    with pytest.raises(RuntimeError, match="sobrescrito"):
        module._bootstrap_uv(tmp_path)
    assert note.read_text() == "preserve"


def test_old_partial_bootstrap_is_not_reused(monkeypatch, tmp_path):
    module = support()
    fake_wheel(module, monkeypatch)
    monkeypatch.setattr(module.subprocess, "run", fake_uv_run([]))
    old = tmp_path / ".eca-uv-bootstrap-v321"
    old.mkdir()
    (old / "pyvenv.cfg").write_text("partial old environment")
    assert "v322" in module._bootstrap_uv(tmp_path)
    assert (old / "pyvenv.cfg").read_text() == "partial old environment"


def test_command_failure_shows_original_stderr(monkeypatch):
    module = support()
    def fail(command, **kwargs):
        raise subprocess.CalledProcessError(1, command, output="step output", stderr="ensurepip is not available")
    monkeypatch.setattr(module.subprocess, "run", fail)
    with pytest.raises(RuntimeError, match="ensurepip is not available"):
        module._run_checked(["example"], stage="Preparação", timeout=1)


def test_install_permission_is_checked_before_bootstrap(monkeypatch, tmp_path):
    module = support()
    monkeypatch.setattr(module, "_bootstrap_uv", lambda *a: pytest.fail("install without opt-in"))
    with pytest.raises(RuntimeError, match="Ambiente divergente"):
        module.ensure_environment(ROOT, tmp_path / "env", allow_install=False, reuse_current=False)


def test_foreign_environment_rejected_before_downloading(monkeypatch, tmp_path):
    module = support()
    destination = tmp_path / "env"
    destination.mkdir()
    (destination / "research.txt").write_text("preserve")
    monkeypatch.setattr(module, "resolve_base_python", lambda *a: pytest.fail("download before guard"))
    monkeypatch.setattr(module, "_bootstrap_uv", lambda *a: pytest.fail("download before guard"))
    with pytest.raises(RuntimeError, match="sobrescrito"):
        module.ensure_environment(ROOT, destination, allow_install=True, reuse_current=False)


def test_scientific_environment_created_by_uv_not_host_venv(monkeypatch, tmp_path):
    module = support()
    destination = tmp_path / "env"
    scientific_python = str(destination / "bin/python")
    monkeypatch.setattr(module, "read_pins", lambda path: {"example": "1.0"})
    monkeypatch.setattr(module, "resolve_base_python", lambda path: "/managed/python3.12")
    monkeypatch.setattr(module, "_bootstrap_uv", lambda path: "/isolated/uv")
    monkeypatch.setattr(module, "probe_versions", lambda python, pins: dict(pins))
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        assert command[:3] != [module.sys.executable, "-m", "venv"]
        if "venv" in command:
            destination.mkdir()
            (destination / "pyvenv.cfg").write_text("home = /managed")
            (destination / "bin").mkdir()
            (destination / "bin/python").write_bytes(b"managed python")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
    monkeypatch.setattr(module.subprocess, "run", run)
    assert module.ensure_environment(ROOT, destination, allow_install=True, reuse_current=False) == scientific_python
    create = next(command for command in calls if "venv" in command)
    assert create[:2] == ["/isolated/uv", "venv"]
    assert "--python" in create and "/managed/python3.12" in create
    assert "--no-python-downloads" in create


def test_notebook_loads_support_from_selected_checkout():
    notebook = json.loads(next(ROOT.glob("COMPARAÇÃO*.ipynb")).read_text())
    source = "".join(next(cell for cell in notebook["cells"] if cell["id"] == "source")["source"])
    assert "/content/eca-qca-lab-v322" in source
    assert "spec_from_file_location" in source
    assert 'sys.modules["eca_colab_support"]' in source


def test_source_cell_replaces_stale_module(monkeypatch, tmp_path):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "eca_colab_support.py").write_text('MARKER = "fresh checkout"\n')
    stale = types.ModuleType("eca_colab_support")
    stale.MARKER = "old checkout"
    monkeypatch.setitem(sys.modules, "eca_colab_support", stale)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **kw: "fake-commit\n")
    notebook = json.loads(next(ROOT.glob("COMPARAÇÃO*.ipynb")).read_text())
    source = "".join(next(cell for cell in notebook["cells"] if cell["id"] == "source")["source"])
    namespace = {"Path": Path, "sys": sys, "IN_COLAB": False}
    exec(compile(source, "source-cell", "exec"), namespace)
    assert sys.modules["eca_colab_support"].MARKER == "fresh checkout"
    assert namespace["PROJECT_ROOT"] == tmp_path


def test_oversized_wheel_never_executes(monkeypatch, tmp_path):
    module = support()
    fake_wheel(module, monkeypatch)
    monkeypatch.setattr(module, "MAX_WHEEL_BYTES", 8)
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **kw: pytest.fail("oversized download"))
    with pytest.raises(RuntimeError, match="tamanho"):
        module._bootstrap_uv(tmp_path)


def test_timeout_preserves_byte_diagnostics(monkeypatch):
    module = support()
    def timeout(command, **kwargs):
        raise subprocess.TimeoutExpired(command, 1, stderr=b"download stalled")
    monkeypatch.setattr(module.subprocess, "run", timeout)
    with pytest.raises(RuntimeError, match="download stalled"):
        module._run_checked(["example"], stage="Download", timeout=1)
