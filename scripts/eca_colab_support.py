"""Suporte Colab: somente biblioteca padrão; nenhum SDK no kernel da interface."""
from __future__ import annotations

import html
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def cpu_environment():
    env = os.environ.copy()
    env.update(CUDA_VISIBLE_DEVICES="-1", TF_USE_LEGACY_KERAS="1",
               TF_CPP_MIN_LOG_LEVEL="3", OPENBLAS_NUM_THREADS="1",
               OMP_NUM_THREADS="1", MKL_NUM_THREADS="1",
               TF_NUM_INTRAOP_THREADS="1", TF_NUM_INTEROP_THREADS="1",
               MPLBACKEND="Agg")
    return env


def read_pins(path):
    pins = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            name, version = line.split("==", 1)
            pins[name] = version
    return pins


def probe_versions(python, pins):
    code = ("import importlib.metadata as m,json; out={}\n"
            "for name in " + repr(list(pins)) + ":\n"
            " try: out[name]=m.version(name)\n"
            " except m.PackageNotFoundError: out[name]=None\n"
            "print(json.dumps(out))")
    result = subprocess.run([str(python), "-c", code], check=True,
                            text=True, capture_output=True, timeout=30)
    return json.loads(result.stdout)


def compatible_python():
    for candidate in (sys.executable, shutil.which("python3.12"), shutil.which("python3.11")):
        if not candidate:
            continue
        version = subprocess.check_output(
            [candidate, "-c", "import sys,json;print(json.dumps(list(sys.version_info[:2])))"],
            text=True, timeout=30)
        if tuple(json.loads(version)) in {(3, 11), (3, 12)}:
            return candidate
    raise RuntimeError(
        "Esta matriz TFQ exige Python 3.11/3.12. Selecione um runtime Colab "
        "compatível ou execute localmente com Python 3.12. Nenhum pacote foi alterado.")


def ensure_environment(root, destination, *, allow_install=False, reuse_current=True):
    """Usa ambiente verificado ou cria venv; nunca executa pip no Python do Colab."""
    root = Path(root).resolve()
    pins = read_pins(root / "requirements-eca-colab.txt")
    if reuse_current and probe_versions(sys.executable, pins) == pins:
        return sys.executable
    if not allow_install:
        raise RuntimeError("Ambiente divergente: instale requirements-eca-colab.txt em um venv.")
    base_python = compatible_python()
    destination = Path(destination).resolve()
    if destination.exists() and not (destination / "pyvenv.cfg").is_file():
        raise RuntimeError(f"Diretório existente não é venv; não será sobrescrito: {destination}")
    python = destination / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.is_file():
        print("Criando ambiente isolado; os pacotes do Colab serão preservados.", flush=True)
        subprocess.run([base_python, "-m", "venv", str(destination)], check=True, timeout=120)
    if probe_versions(python, pins) != pins:
        print("Instalando a matriz fixada. A primeira execução pode levar alguns minutos.", flush=True)
        subprocess.run([str(python), "-m", "pip", "install", "--disable-pip-version-check",
                        "--prefer-binary", "--only-binary=tensorflow-quantum,tensorflow,numpy,qiskit",
                        "-q", "-r", str(root / "requirements-eca-colab.txt")],
                       env=cpu_environment(), check=True, timeout=1800)
    if probe_versions(python, pins) != pins:
        raise RuntimeError("Instalação incompleta. Reexecute esta célula; não avance sem matriz válida.")
    subprocess.run([str(python), "-m", "pip", "check"], check=True, timeout=60)
    return str(python)


def run_json(python, root, script, arguments=(), *, timeout=600):
    result = subprocess.run([str(python), str(Path(root) / "scripts" / script), *map(str, arguments)],
                            cwd=root, env=cpu_environment(), text=True,
                            capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f"Etapa {script} falhou ({result.returncode}):\n"
                           + (result.stderr + result.stdout)[-6000:])
    return json.loads(result.stdout)


def table_html(rows):
    if not rows:
        return "<p>Nenhuma linha disponível.</p>"
    columns = list(rows[0])
    head = "".join(f"<th style='padding:9px;text-align:left'>{html.escape(str(c))}</th>" for c in columns)
    body = "".join("<tr>" + "".join(
        f"<td style='padding:9px;border-bottom:1px solid #cbd5e1'>{html.escape(str(row.get(c, '')))}</td>"
        for c in columns) + "</tr>" for row in rows)
    return ("<div style='overflow-x:auto'><table style='border-collapse:collapse;width:100%;"
            "font:14px system-ui;color:#172638;background:#fff'><thead style='background:#e6f3f3'>"
            f"<tr>{head}</tr></thead><tbody>{body}</tbody></table></div>")


def report_html(report):
    counts, numerics = report.get("counts", {}), report.get("numerics", {})
    technical = "APROVADO" if report.get("technical_gate_passed") else "NÃO APROVADO"
    hypotheses = report.get("hypotheses", {})
    if not hypotheses.get("H3_H4_evaluated"):
        inference = "NÃO AVALIADAS (smoke ou gate indisponível)"
    elif hypotheses.get("H3_ber_matches_p") and hypotheses.get("H4_exact_success_matches_theory"):
        inference = "COMPATÍVEIS dentro das bandas planejadas"
    else:
        inference = "FORA das bandas planejadas — investigar"
    rows = [
        {"Indicador": "Perfil / gate técnico", "Resultado": f"{report.get('profile', '?')} / {technical}"},
        {"Indicador": "H3 / H4 — ruído", "Resultado": inference},
        {"Indicador": "Bases / pares de estado / observáveis TFQ", "Resultado":
         f"{counts.get('basis_backend_checks', '—')} / {counts.get('statevector_pair_checks', '—')} / {counts.get('tfq_observable_checks', '—')}"},
        {"Indicador": "Unidades de ruído / linhas pareadas", "Resultado":
         f"{counts.get('noise_design_units', '—')} / {counts.get('noise_records', '—')}"},
        {"Indicador": "Fidelidade mínima", "Resultado": numerics.get("minimum_cross_framework_fidelity", "—")},
        {"Indicador": "Erro máximo de probabilidade", "Resultado": numerics.get("maximum_basis_probability_error", "—")},
    ]
    return "<h3 style='font-family:system-ui'>Painel da execução atual</h3>" + table_html(rows)
