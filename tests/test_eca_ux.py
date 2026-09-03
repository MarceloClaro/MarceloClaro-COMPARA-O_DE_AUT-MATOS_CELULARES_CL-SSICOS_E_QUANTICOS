import importlib.util
import json
import sys
from pathlib import Path

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
