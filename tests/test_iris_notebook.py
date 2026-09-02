"""Testes estáticos de regressão para o notebook Iris destinado ao Colab."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "Classificador_Quântico_Híbrido_de_Alta_Performance_para_Classificação_de_Dados_Iris_(Otimizado).ipynb"
BUILDER = ROOT / "scripts" / "build_iris_colab.py"
VALIDATOR = ROOT / "scripts" / "validate_iris_notebook.py"
EXPECTED_ORDER = [
    "title", "project-presentation", "author-presentation", "instructions",
    "setup", "imports-config", "protocol", "data", "quantum-model",
    "circuits", "features-tests", "architecture-selection", "optimization",
    "landscape", "robustness", "final-test", "artifacts", "limits",
]


class IrisNotebookContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
        cls.cells = cls.notebook["cells"]
        cls.by_id = {cell["id"]: cell for cell in cls.cells}

    @staticmethod
    def text(cell: dict) -> str:
        return "".join(cell.get("source", []))

    @classmethod
    def loaded_names(cls, cell: dict) -> set[str]:
        tree = ast.parse(cls.text(cell))
        return {
            node.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
        }

    def test_01_notebook_structure_order_and_clean_state(self) -> None:
        self.assertEqual(self.notebook["nbformat"], 4)
        identifiers = [cell["id"] for cell in self.cells]
        self.assertEqual(identifiers, EXPECTED_ORDER)
        self.assertEqual(len(identifiers), len(set(identifiers)))
        for cell in self.cells:
            if cell["cell_type"] == "code":
                ast.parse(self.text(cell))
                self.assertIsNone(cell["execution_count"])
                self.assertEqual(cell["outputs"], [])

    def test_02_every_code_cell_has_an_explicit_gate(self) -> None:
        for cell in self.cells:
            if cell["cell_type"] == "code":
                with self.subTest(cell=cell["id"]):
                    self.assertRegex(self.text(cell), r"GATE [A-ZÁÉÍÓÚÇ ]+")

    def test_03_project_author_and_recovery_instructions_are_preserved(self) -> None:
        project = self.text(self.by_id["project-presentation"])
        author = self.text(self.by_id["author-presentation"])
        instructions = self.text(self.by_id["instructions"])
        self.assertIn("Apresentação do projeto", project)
        self.assertIn("VQC Cirq", project)
        self.assertIn("Prof. Marcelo Claro Laranjeira", author)
        self.assertIn("Professor de Geografia e Pedagogo", author)
        self.assertIn("https://github.com/MarceloClaro", author)
        self.assertIn("https://bit.ly/geomaker", author)
        self.assertIn("0000-0001-8996-2887", author)
        self.assertIn("@marceloclaro.geomaker", author)
        self.assertIn("reinicie o runtime", instructions)
        self.assertIn("GATE ...: aprovado", instructions)

    def test_04_setup_checks_every_dependency_contract(self) -> None:
        setup = self.text(self.by_id["setup"])
        for requirement in (
            "cirq-core==1.6.1", "scikit-learn>=1.4,<2", "scipy>=1.16,<2",
            "matplotlib>=3.8,<4", "pandas>=2.0,<3",
        ):
            self.assertIn(requirement, setup)
        self.assertIn("sys.version_info[:2] < (3, 10)", setup)
        self.assertIn("maximum_major", setup)
        self.assertIn("subprocess.CalledProcessError", setup)
        self.assertIn("site.addsitedir(site.getusersitepackages())", setup)
        self.assertIn("Pós-condição de dependências falhou", setup)
        self.assertNotIn('"tensorflow"', setup.lower())

    def test_05_data_contract_has_fixed_balanced_disjoint_splits(self) -> None:
        data = self.text(self.by_id["data"])
        self.assertIn("X_raw.shape == (100, 4)", data)
        self.assertIn("(60, 20, 20)", data)
        self.assertIn("set(train_ids).isdisjoint(validation_ids)", data)
        self.assertIn("input_scaler.fit_transform(X_raw[train_ids])", data)
        self.assertIn("TEST_OPENED = False", data)
        self.assertIn("TEST_OPEN_COUNT = 0", data)
        self.assertNotIn("X_test =", data)
        self.assertNotIn("y_test =", data)

    def test_06_circuit_and_feature_cells_enforce_physical_invariants(self) -> None:
        circuits = self.text(self.by_id["circuits"])
        features = self.text(self.by_id["features-tests"])
        self.assertIn("cirq.parameter_names(circuit)", circuits)
        self.assertIn("not circuit.has_measurements()", circuits)
        self.assertIn("len(circuit_signatures) == len(CIRCUITS)", circuits)
        self.assertIn("simulate_expectation_values", features)
        self.assertIn("FloatingPointError", features)
        self.assertIn("z_zero, 1.0", features)
        self.assertIn("z_one, -1.0", features)
        self.assertIn("Entrada inválida deveria produzir ValueError", features)

    def test_07_selection_cells_cannot_load_test_data(self) -> None:
        forbidden = {"X_test", "y_test", "test_probability", "test_prediction"}
        for identifier in ("architecture-selection", "optimization", "landscape", "robustness"):
            with self.subTest(cell=identifier):
                self.assertTrue(forbidden.isdisjoint(self.loaded_names(self.by_id[identifier])))

    def test_08_selection_is_deterministic_and_optimization_is_gated(self) -> None:
        selection = self.text(self.by_id["architecture-selection"])
        configuration = self.text(self.by_id["imports-config"])
        optimization = self.text(self.by_id["optimization"])
        self.assertIn('["validation_log_loss", "architecture"]', selection)
        self.assertIn('kind="stable"', selection)
        self.assertIn("cobyla_f_target=0.04", configuration)
        self.assertIn("cobyla_f_target=None", configuration)
        self.assertIn('"tol": SPEC.cobyla_tol', optimization)
        self.assertIn("len(objective_history) == int(optimization.nfev)", optimization)
        self.assertIn("if not optimization.success", optimization)
        self.assertIn("GATE COBYLA FALHOU", optimization)

    def test_09_robustness_precedes_confirmation_and_has_unique_seeds(self) -> None:
        identifiers = [cell["id"] for cell in self.cells]
        self.assertLess(identifiers.index("robustness"), identifiers.index("final-test"))
        robustness = self.text(self.by_id["robustness"])
        self.assertIn("X_validation", robustness)
        self.assertIn("y_validation", robustness)
        self.assertNotIn("X_test", robustness)
        self.assertNotIn("y_test", robustness)
        self.assertIn("validation_post_selection", robustness)
        self.assertIn("np.random.SeedSequence([SEED, noise_index, replicate])", robustness)
        self.assertIn('noise_results["noise_seed"].is_unique', robustness)

    def test_10_test_data_are_loaded_only_by_confirmation_cell(self) -> None:
        consumers = {
            cell["id"]
            for cell in self.cells
            if cell["cell_type"] == "code"
            and {"X_test", "y_test"}.intersection(self.loaded_names(cell))
        }
        self.assertEqual(consumers, {"final-test"})
        confirmation = self.text(self.by_id["final-test"])
        self.assertIn("if TEST_OPENED", confirmation)
        self.assertIn("TEST_OPENED = True", confirmation)
        self.assertIn("TEST_OPEN_COUNT += 1", confirmation)
        self.assertIn("TEST_OPEN_COUNT == 1", confirmation)

    def test_11_artifact_archive_uses_a_closed_member_list(self) -> None:
        artifacts = self.text(self.by_id["artifacts"])
        self.assertNotIn("output_dir.glob", artifacts)
        self.assertIn("artifact_paths = (", artifacts)
        self.assertIn("archive_members = (*artifact_paths, sha_path)", artifacts)
        self.assertIn("sorted(bundle.namelist())", artifacts)
        for name in (
            "architecture_validation.csv", "landscape_validation.csv",
            "validation_input_noise_raw.csv", "test_metrics.csv",
            "optimized_parameters.csv", "optimization_history.csv",
            "manifest.json", "sha256.json",
        ):
            self.assertIn(name, artifacts)

    def test_12_no_tensorflow_keras_or_embedded_secret(self) -> None:
        all_code = "\n".join(
            self.text(cell) for cell in self.cells if cell["cell_type"] == "code"
        )
        self.assertIsNone(
            re.search(r"^\s*(?:import|from)\s+(?:tensorflow|keras)", all_code, re.MULTILINE)
        )
        self.assertIsNone(
            re.search(
                r"(?i)(?:token|password|api_key)\s*=\s*[\"'][^\"']+[\"']", all_code,
            )
        )

    def test_13_validator_reports_cells_and_reexecution_guard(self) -> None:
        validator_source = VALIDATOR.read_text(encoding="utf-8")
        ast.parse(validator_source)
        self.assertIn('"failed_cell"', validator_source)
        self.assertIn('"peak_rss_mib"', validator_source)
        self.assertIn('report["test_reexecution_guard"] = "passed"', validator_source)
        self.assertIn("--allow-install", validator_source)

    def test_14_generator_is_deterministic(self) -> None:
        subprocess.run([sys.executable, str(BUILDER)], cwd=ROOT, check=True, capture_output=True)
        first = hashlib.sha256(NOTEBOOK.read_bytes()).hexdigest()
        subprocess.run([sys.executable, str(BUILDER)], cwd=ROOT, check=True, capture_output=True)
        second = hashlib.sha256(NOTEBOOK.read_bytes()).hexdigest()
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
