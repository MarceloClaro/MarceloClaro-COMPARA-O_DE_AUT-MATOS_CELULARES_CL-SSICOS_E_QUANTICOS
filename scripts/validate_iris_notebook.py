"""Executa e audita cada célula de código do notebook Iris em ordem.

O validador usa somente a biblioteca-padrão. Por padrão, ele não instala pacotes;
use ``--allow-install`` em um ambiente limpo ou no Colab.
"""

from __future__ import annotations

import argparse
import json
import os
import resource
import sys
import tempfile
import time
import traceback
from contextlib import nullcontext
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / (
    "Classificador_Quântico_Híbrido_de_Alta_Performance_para_"
    "Classificação_de_Dados_Iris_(Otimizado).ipynb"
)


def peak_rss_mib() -> float:
    """Retorna o pico de RSS em MiB no Linux e no macOS."""
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == "darwin":
        return value / (1024 * 1024)
    return value / 1024


def write_report(path: Path | None, report: dict) -> None:
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")
    print(payload)


def execute(args: argparse.Namespace) -> int:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    report_path = args.report.resolve() if args.report else None

    os.environ["IRIS_PROFILE"] = args.profile
    os.environ.setdefault("MPLBACKEND", "Agg")
    if args.allow_install:
        os.environ.pop("IRIS_SKIP_INSTALL", None)
    else:
        os.environ["IRIS_SKIP_INSTALL"] = "1"

    namespace = {
        "__name__": "__main__",
        "display": lambda *_objects, **_options: None,
    }
    report = {
        "notebook": NOTEBOOK.name,
        "profile": args.profile,
        "python": sys.version.split()[0],
        "status": "running",
        "cells": [],
    }

    temporary = tempfile.TemporaryDirectory(prefix="iris-notebook-") if args.workdir is None else None
    context = temporary if temporary is not None else nullcontext(str(args.workdir.resolve()))
    original_directory = Path.cwd()
    started_all = time.perf_counter()
    try:
        with context as run_directory_text:
            run_directory = Path(run_directory_text)
            run_directory.mkdir(parents=True, exist_ok=True)
            os.chdir(run_directory)
            for ordinal, cell in enumerate(code_cells, start=1):
                cell_id = cell["id"]
                source = "".join(cell.get("source", []))
                started = time.perf_counter()
                record = {"ordinal": ordinal, "id": cell_id, "status": "running"}
                report["cells"].append(record)
                try:
                    compiled = compile(source, f"{NOTEBOOK.name}::{cell_id}", "exec")
                    exec(compiled, namespace)
                except Exception as error:  # relatório precisa preservar a célula exata
                    record.update(
                        status="failed",
                        seconds=time.perf_counter() - started,
                        peak_rss_mib=peak_rss_mib(),
                        error_type=type(error).__name__,
                        error=str(error),
                        traceback=traceback.format_exc(),
                    )
                    report["status"] = "failed"
                    report["failed_cell"] = cell_id
                    report["total_seconds"] = time.perf_counter() - started_all
                    report["peak_rss_mib"] = peak_rss_mib()
                    write_report(report_path, report)
                    return 1
                record.update(
                    status="passed",
                    seconds=time.perf_counter() - started,
                    peak_rss_mib=peak_rss_mib(),
                )

            # O segundo disparo deve parar antes de tocar novamente no teste.
            confirmation = next(cell for cell in code_cells if cell["id"] == "final-test")
            try:
                exec(
                    compile(
                        "".join(confirmation["source"]),
                        f"{NOTEBOOK.name}::final-test-reexecution",
                        "exec",
                    ),
                    namespace,
                )
            except RuntimeError as error:
                if "já foi aberto" not in str(error):
                    raise
                report["test_reexecution_guard"] = "passed"
            else:
                raise AssertionError("A segunda execução da célula final deveria ser bloqueada.")
    finally:
        os.chdir(original_directory)

    report["status"] = "passed"
    report["total_seconds"] = time.perf_counter() - started_all
    report["peak_rss_mib"] = peak_rss_mib()
    write_report(report_path, report)
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("smoke", "full"), default="smoke")
    parser.add_argument(
        "--allow-install",
        action="store_true",
        help="permite que a célula setup instale dependências incompatíveis ou ausentes",
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        help="diretório de execução persistente; por padrão usa um diretório temporário",
    )
    parser.add_argument("--report", type=Path, help="caminho opcional do relatório JSON")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(execute(parse_args()))
