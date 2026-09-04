import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def support():
    spec = importlib.util.spec_from_file_location("eca_colab_support", ROOT / "scripts/eca_colab_support.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_no_automatic_hosted_workflow():
    assert not list((ROOT / ".github/workflows").glob("*.yml"))
    assert not list((ROOT / ".github/workflows").glob("*.yaml"))
    assert (ROOT / "docs/workflows/eca-confirmatory.yml.example").is_file()
    assert "actions/workflows/eca-confirmatory.yml/badge.svg" not in (ROOT / "README.md").read_text()


def test_notebook_kernel_does_not_import_scientific_sdks():
    notebook = json.loads(next(ROOT.glob("COMPARAÇÃO*.ipynb")).read_text())
    code = "\n".join("".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code")
    for forbidden in ("import numpy", "import tensorflow", "from eca_qca_lab", "import pennylane", "import qiskit", "import cirq"):
        assert forbidden not in code
    assert "ensure_environment" in code and "RUN_ID" in code


def test_author_and_progressive_learning_contract():
    text = (ROOT / "scripts/build_eca_colab.py").read_text()
    for value in ("MARCELO CLARO LARANJEIRA", "0000-0001-8996-2887", "Como interpretar", "Gabarito", "Bonferroni", "AUTO_DOWNLOAD"):
        assert value in text
    assert (ROOT / "assets/eca-cover.png").is_file()


def test_dashboard_does_not_claim_smoke_confirmation():
    html = support().report_html({"profile": "smoke", "technical_gate_passed": True, "hypotheses": {"H3_H4_evaluated": False}, "counts": {}, "numerics": {}})
    assert "NÃO AVALIADAS" in html
    assert "APROVADAS" not in html


def test_dashboard_escapes_untrusted_values():
    html = support().table_html([{"dado": "<script>alert(1)</script>"}])
    assert "<script>" not in html and "&lt;script&gt;" in html


def test_cpu_environment_limits_threads():
    env = support().cpu_environment()
    assert env["CUDA_VISIBLE_DEVICES"] == "-1"
    assert env["TF_USE_LEGACY_KERAS"] == "1"
    assert env["OPENBLAS_NUM_THREADS"] == "1"


def test_pin_reader_matches_requirements():
    pins = support().read_pins(ROOT / "requirements-eca-colab.txt")
    assert pins["tensorflow-quantum"] == "0.7.6"
    assert pins["qiskit"] == "2.5.2"


def test_json_step_resolves_scripts_directory(tmp_path):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "step.py").write_text('print(\'{"ok": true}\')', encoding="utf-8")
    assert support().run_json(sys.executable, tmp_path, "step.py") == {"ok": True}


def test_python_313_falls_back_to_managed_python(monkeypatch, tmp_path):
    module = support()
    monkeypatch.setattr(module, "compatible_python", lambda: (_ for _ in ()).throw(RuntimeError("3.13")))
    monkeypatch.setattr(module, "install_managed_python", lambda directory: str(directory / "python3.12"))
    assert module.resolve_base_python(tmp_path) == str(tmp_path / "python3.12")


def test_managed_python_bootstrap_is_pinned_and_isolated():
    text = (ROOT / "scripts/eca_colab_support.py").read_text()
    assert 'UV_VERSION = "0.12.9"' in text
    assert 'PYTHON_REQUEST = "3.12"' in text
    assert '"-m", "venv"' not in text
    assert "wheel_digest" in text and "sha256(wheel_bytes)" in text
    assert '"--managed-python"' in text
    assert "curl" not in text and "sudo" not in text


def test_notebook_uses_new_checkout_for_hotfix():
    text = (ROOT / "scripts/build_eca_colab.py").read_text()
    assert "/content/eca-qca-lab-v322" in text
    assert "Python 3.13" in text and "Python 3.12 gerenciado" in text


def test_managed_python_install_command_and_result(monkeypatch, tmp_path):
    module = support()
    managed_python = tmp_path / ".eca-python-v322" / "cpython-3.12" / "bin" / "python3.12"
    managed_python.parent.mkdir(parents=True)
    managed_python.write_bytes(b"test executable")
    calls = []
    monkeypatch.setattr(module, "_bootstrap_uv", lambda parent: "/isolated/uv")
    answers = iter(("", str(managed_python) + "\n", "[3, 12]\n"))
    def run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, stdout=next(answers), stderr="")
    monkeypatch.setattr(module.subprocess, "run", run)
    assert module.install_managed_python(tmp_path) == str(managed_python)
    assert calls[0][0] == ["/isolated/uv", "python", "install", "3.12", "--no-bin", "--no-progress", "--no-config"]
    assert calls[0][1]["env"]["UV_PYTHON_INSTALL_DIR"] == str(tmp_path / ".eca-python-v322")
