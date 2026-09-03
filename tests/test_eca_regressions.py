import importlib.util
import json
from pathlib import Path
import zipfile

import numpy as np
import pytest
from eca_qca_lab import core
from eca_qca_lab import experiment as exp
from eca_qca_lab import adapters

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("value", [0.9, -0.1, 1.1, "1", None, float("nan")])
def test_non_bits_are_not_silently_truncated(value):
    with pytest.raises(ValueError):
        core.eca_step((0, value, 1), 30)


@pytest.mark.parametrize("builder", [adapters.build_qiskit_circuit, adapters.build_pennylane_qnode, adapters.build_cirq_circuit])
@pytest.mark.parametrize("value", [0.9, -0.1, 1.1, "1", None, float("nan")])
def test_adapters_share_strict_bit_validation(builder, value):
    with pytest.raises(ValueError):
        builder(30, 3, initial=(0, value, 1))


def test_tfq_reference_really_uses_cirq(monkeypatch):
    cases = [{"rule": 30, "n_cells": 3, "mode": "basis", "state_id": 1, "initial": [0, 0, 1]}]
    calls = []
    def fake_statevector(backend, rule, n_cells, **kwargs):
        calls.append(backend)
        # Deliberately wrong Cirq state: TFQ equals the analytic oracle instead.
        v = np.zeros(64, dtype=complex)
        v[0] = 1
        return v
    expected = core.output_z_expectations(core.oracle_statevector(30, 3, initial=(0, 0, 1)), 3)
    monkeypatch.setattr(exp, "statevector", fake_statevector)
    monkeypatch.setattr(exp, "tfq_batch_expectations", lambda cases: [expected])
    rows, available, _ = exp._tfq(core.PROFILE_SPECS["smoke"], cases, True)
    assert available and calls == ["cirq"]
    assert not all(row["passed"] for row in rows)
    assert all(row["cirq_reference_z"] == 1 for row in rows)
    assert all(row["analytical_absolute_error"] == 0 for row in rows)


@pytest.fixture
def stubbed_run(monkeypatch, tmp_path):
    passed = {"passed": True, "fidelity": 1.0, "max_probability_error": 0.0, "max_phase_error": 0.0}
    monkeypatch.setattr(exp, "_basis_coherent", lambda spec: ([passed], [passed], [passed], []))
    monkeypatch.setattr(exp, "_tfq", lambda *args: ([{"available": False, "passed": False}], False, "not installed"))
    monkeypatch.setattr(exp, "_noise", lambda spec: ([{"simulator_seed": 17, "unit_id": "unit-17"}], [{"ber_compatible": True, "exact_compatible": True}]))
    monkeypatch.setattr(exp, "_benchmark", lambda spec: ([{"time": 0.1}], [{"median": 0.1}]))
    def fake_figures(dest, noise, bench):
        (dest / "figure_noise.png").write_bytes(b"test fixture")
        (dest / "figure_benchmark.png").write_bytes(b"test fixture")
    monkeypatch.setattr(exp, "_figures", fake_figures)
    return exp.run_experiment(tmp_path / "results", profile="paper", require_tfq=False, project_root=ROOT)


def verifier():
    spec = importlib.util.spec_from_file_location("verify_eca_bundle", ROOT / "scripts/verify_eca_bundle.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_missing_tfq_cannot_enable_confirmation(stubbed_run):
    report = stubbed_run
    assert not report["technical_gate_passed"]
    assert not report["confirmatory_claims_enabled"]
    assert not report["hypotheses"]["H3_H4_evaluated"]
    assert not report["hypotheses"]["H3_ber_matches_p"]


def test_archived_report_identical_to_disk_and_verified(stubbed_run):
    path = Path(stubbed_run["bundle"])
    with zipfile.ZipFile(path) as bundle:
        assert bundle.read("validation_report.json") == (path.parent / "validation_report.json").read_bytes()
    result = verifier().verify(path)
    assert result["verified"] == 10
    assert result["metadata_verified"] == 2


def test_metadata_tampering_detected(stubbed_run):
    directory = Path(stubbed_run["bundle"]).parent
    report = directory / "validation_report.json"
    report.write_text(report.read_text() + " ", encoding="utf-8")
    with pytest.raises(ValueError, match="hash"):
        verifier().verify_dir(directory)


def test_zip_extra_member_rejected(stubbed_run):
    path = Path(stubbed_run["bundle"])
    with zipfile.ZipFile(path, "a") as bundle:
        bundle.writestr("../escape.txt", "untrusted")
    with pytest.raises(ValueError, match="membros"):
        verifier().verify(path)


def test_existing_experiment_cannot_be_overwritten(stubbed_run):
    directory = Path(stubbed_run["bundle"]).parent
    with pytest.raises(FileExistsError):
        exp.run_experiment(directory, profile="paper", require_tfq=False)
