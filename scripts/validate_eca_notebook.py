#!/usr/bin/env python3
"""Executa o notebook em kernel Jupyter real; repetição mantém o mesmo processo."""
import argparse
from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
import io
import json
import os
from pathlib import Path
import re
import resource
import sys
import time
import traceback

import nbformat
from nbclient import NotebookClient
from eca_colab_support import cpu_environment

ROOT = Path(__file__).resolve().parents[1]
NB = next(ROOT.glob("COMPARAÇÃO_DE_AUTÔMATOS_CELULARES_CLÁSSICOS_E_QUANTICOS_*.ipynb"))


def structure(notebook):
    cells = notebook.cells
    codes = [cell for cell in cells if cell.cell_type == "code"]
    source = "\n".join(cell.source for cell in cells)
    code = "\n".join(cell.source for cell in codes)
    checks = {
        "21_cells": len(cells) == 21, "11_code": len(codes) == 11,
        "author": "MARCELO CLARO LARANJEIRA" in source,
        "orcid": "0000-0001-8996-2887" in source,
        "no_guard": "TEST_OPENED" not in code,
        "tfq_semantics": "não é uma quarta implementação independente" in source,
        "no_sdk_import_in_ui": not any(s in code for s in ("import tensorflow", "import qiskit", "import pennylane", "import cirq", "from eca_qca_lab")),
    }
    for i, cell in enumerate(codes):
        compile(cell.source, f"code-{i}", "exec")
    if not all(checks.values()):
        raise AssertionError(checks)
    return checks


def streams(notebook):
    return "\n".join(output.get("text", "") for cell in notebook.cells
                     for output in cell.get("outputs", []) if output.output_type == "stream")


def execute_pass(client, template, log_dir, index):
    client.nb = deepcopy(template)
    client.reset_execution_trackers()
    started = time.perf_counter()
    timings = []
    for i, cell in enumerate(client.nb.cells):
        if cell.cell_type != "code":
            continue
        start = time.perf_counter()
        print(f"Passagem {index} · célula {i+1}/21 ({cell.id})", flush=True)
        client.execute_cell(cell, i)
        timings.append({"cell": i+1, "id": cell.id, "seconds": time.perf_counter()-start})
    # Instrumentação separada: não integra as 11 células do notebook entregue.
    diagnostic = nbformat.v4.new_code_cell(
        "import resource\n"
        "print('ECA_VALIDATION_STATE=' + json.dumps({"
        "'run_state': ECA_RUN_STATE, 'kernel_pid': os.getpid(), "
        "'peak_kernel_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, "
        "'scientific_sdks_in_kernel': [m for m in "
        "['qiskit','pennylane','cirq','tensorflow','tensorflow_quantum','eca_qca_lab'] if m in sys.modules]}))")
    client.nb.cells.append(diagnostic)
    client.execute_cell(diagnostic, len(client.nb.cells)-1)
    diagnostics = streams(client.nb).split("ECA_VALIDATION_STATE=")[-1].strip().splitlines()[0]
    observed = json.loads(diagnostics)
    client.nb.cells.pop()
    output = streams(client.nb)
    tests = re.findall(r"(\d+) passed", output)
    (log_dir/f"run-{index}.log").write_text(output, encoding="utf-8")
    # Saídas ricas são grandes; ficam no diretório local de validação.
    nbformat.write(client.nb, log_dir/f"run-{index}.ipynb")
    if observed["scientific_sdks_in_kernel"]:
        raise AssertionError("SDK científico carregado no kernel da interface")
    if observed["run_state"]["status"] != "completed":
        raise AssertionError("Execução incompleta")
    return {"seconds": time.perf_counter()-started, "pytest_passed": int(tests[-1]) if tests else None,
            "cells": timings, **observed}


def execute_namespace_pass(template, namespace, log_dir, index):
    """Teste limitado de Python; não valida transporte Jupyter nem frontend Colab."""
    stream = io.StringIO()
    started = time.perf_counter()
    timings = []
    for i, cell in enumerate(template.cells):
        if cell.cell_type != "code":
            continue
        print(f"Namespace {index} · célula {i+1}/21 ({cell.id})", flush=True)
        start = time.perf_counter()
        with redirect_stdout(stream), redirect_stderr(stream):
            exec(compile(cell.source, f"cell-{i+1}", "exec"), namespace)
        timings.append({"cell": i+1, "id": cell.id, "seconds": time.perf_counter()-start})
    output = stream.getvalue()
    (log_dir/f"run-{index}.log").write_text(output, encoding="utf-8")
    tests = re.findall(r"(\d+) passed", output)
    loaded = [m for m in ("qiskit", "pennylane", "cirq", "tensorflow", "tensorflow_quantum", "eca_qca_lab") if m in sys.modules]
    if loaded:
        raise AssertionError(f"SDKs presentes no processo da interface: {loaded}")
    return {"seconds": time.perf_counter()-started, "pytest_passed": int(tests[-1]) if tests else None,
            "cells": timings, "run_state": namespace.get("ECA_RUN_STATE"), "process_pid": os.getpid(),
            "peak_process_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "scientific_sdks_in_kernel": loaded}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=("smoke", "paper"), default="smoke")
    parser.add_argument("--output-dir", type=Path, default=ROOT/"eca_qca_results")
    parser.add_argument("--report", type=Path, default=ROOT/"eca_notebook_validation.json")
    parser.add_argument("--repeat-run-all", action="store_true")
    parser.add_argument("--allow-install", action="store_true")
    parser.add_argument("--executor", choices=("jupyter", "namespace"), default="jupyter",
                        help="namespace é teste limitado; não inicia nem valida kernel Jupyter")
    args = parser.parse_args()
    template = nbformat.read(NB, as_version=4)
    nbformat.validate(template)
    checks = structure(template)
    env = cpu_environment()
    env.update(ECA_PROFILE=args.profile, ECA_OUTPUT_DIR=str(args.output_dir.resolve()),
               ECA_ALLOW_INSTALL="1" if args.allow_install else "0")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    log_dir = args.report.parent / (args.report.stem + "_logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    runs, status, error = [], "passed", None
    try:
        if args.executor == "jupyter":
            client = NotebookClient(deepcopy(template), timeout=1800, allow_errors=False, record_timing=True)
            manager = client.create_kernel_manager()
            manager.kernel_spec.argv = [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"]
            with client.setup_kernel(cwd=str(ROOT), env=env):
                for index in range(1, 3 if args.repeat_run_all else 2):
                    runs.append(execute_pass(client, template, log_dir, index))
        else:
            os.environ.update(env)
            namespace = {"__name__": "__main__"}
            for index in range(1, 3 if args.repeat_run_all else 2):
                runs.append(execute_namespace_pass(template, namespace, log_dir, index))
        if len(runs) == 2:
            if args.executor == "jupyter" and runs[0]["kernel_pid"] != runs[1]["kernel_pid"]:
                raise AssertionError("O kernel mudou entre passagens")
            if runs[0]["run_state"]["output_dir"] == runs[1]["run_state"]["output_dir"]:
                raise AssertionError("Passagens compartilharam a pasta de resultados")
    except Exception:
        status, error = "failed", traceback.format_exc()
    report = {"schema_version": "3.2", "executor": args.executor,
              "status": status, "error": error, "profile": args.profile, "checks": checks,
              "runs": runs, "same_kernel_reentry": args.executor == "jupyter" and len(runs) == 2 and runs[0]["kernel_pid"] == runs[1]["kernel_pid"],
              "same_namespace_reentry": args.executor == "namespace" and len(runs) == 2,
              "limitation": "não valida kernel Jupyter nem frontend Colab" if args.executor == "namespace" else None}
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "runs"}, ensure_ascii=False, indent=2))
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
