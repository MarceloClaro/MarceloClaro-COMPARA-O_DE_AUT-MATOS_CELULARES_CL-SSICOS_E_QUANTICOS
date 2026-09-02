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


class IrisNotebookContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
        cls.cells = cls.notebook["cells"]
        cls.by_id = {cell["id"]: cell for cell in cls.cells}

    @staticmethod
    def code(cell: dict) -> str:
        return "".join(cell.get("source", []))

    @staticmethod
    def loaded_names(cell: dict) -> set[str]:
        tree = ast.parse(IrisNotebookContractTests.code(cell))
        return {
            node.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
        }

    def test_notebook_structure_and_clean_state(self) -> None:
        self.assertEqual(self.notebook["nbformat"], 4)
        identifiers = [cell["id"] for cell in self.cells]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        for cell in self.cells:
            if cell["cell_type"] == "code":
                ast.parse(self.code(cell))
                self.assertIsNone(cell["execution_count"])
                self.assertEqual(cell["outputs"], [])

    def test_selection_cells_cannot_load_test_data(self) -> None:
        forbidden = {"X_test", "y_test", "test_probability", "test_prediction"}
        for identifier in ("architecture-selection", "optimization", "landscape"):
            self.assertTrue(forbidden.isdisjoint(self.loaded_names(self.by_id[identifier])))

    def test_test_data_are_loaded_only_by_confirmation_cell(self) -> None:
        consumers = {
            cell["id"]
            for cell in self.cells
            if cell["cell_type"] == "code"
            and {"X_test", "y_test"}.intersection(self.loaded_names(cell))
        }
        self.assertEqual(consumers, {"final-test"})
        confirmation = self.code(self.by_id["final-test"])
        self.assertIn("if TEST_OPENED", confirmation)
        self.assertIn("TEST_OPENED = True", confirmation)

    def test_robustness_uses_validation_partition(self) -> None:
        robustness = self.code(self.by_id["robustness"])
        self.assertIn("X_validation", robustness)
        self.assertIn("y_validation", robustness)
        self.assertNotIn("X_test", robustness)
        self.assertNotIn("y_test", robustness)
        self.assertIn("validation_post_selection", robustness)

    def test_cobyla_requires_a_successful_stop(self) -> None:
        configuration = self.code(self.by_id["imports-config"])
        optimization = self.code(self.by_id["optimization"])
        self.assertIn("cobyla_f_target=0.04", configuration)
        self.assertIn("cobyla_f_target=None", configuration)
        self.assertIn('"tol": SPEC.cobyla_tol', optimization)
        self.assertIn("if not optimization.success", optimization)
        self.assertIn("GATE COBYLA FALHOU", optimization)

    def test_no_tensorflow_keras_or_embedded_secret(self) -> None:
        all_code = "\n".join(
            self.code(cell) for cell in self.cells if cell["cell_type"] == "code"
        )
        self.assertIsNone(
            re.search(r"^\s*(?:import|from)\s+(?:tensorflow|keras)", all_code, re.MULTILINE)
        )
        self.assertIsNone(
            re.search(
                r"(?i)(?:token|password|api_key)\s*=\s*[\"'][^\"']+[\"']",
                all_code,
            )
        )

    def test_artifact_hash_file_does_not_hash_itself(self) -> None:
        artifacts = self.code(self.by_id["artifacts"])
        self.assertIn('path.name != "sha256.json"', artifacts)

    def test_generator_is_deterministic(self) -> None:
        subprocess.run([sys.executable, str(BUILDER)], cwd=ROOT, check=True, capture_output=True)
        first = hashlib.sha256(NOTEBOOK.read_bytes()).hexdigest()
        subprocess.run([sys.executable, str(BUILDER)], cwd=ROOT, check=True, capture_output=True)
        second = hashlib.sha256(NOTEBOOK.read_bytes()).hexdigest()
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
