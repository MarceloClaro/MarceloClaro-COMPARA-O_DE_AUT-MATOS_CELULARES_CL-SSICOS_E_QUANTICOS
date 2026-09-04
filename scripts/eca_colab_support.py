"""Suporte Colab: somente biblioteca padrão; nenhum SDK no kernel da interface."""
from __future__ import annotations

import html
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

UV_VERSION = "0.12.9"
PYTHON_REQUEST = "3.12"


def cpu_environment():
    env = os.environ.copy()
    env.update(CUDA_VISIBLE_DEVICES="-1", TF_USE_LEGACY_KERAS="1",
               TF_CPP_MIN_LOG_LEVEL="3", OPENBLAS_NUM_THREADS="1",
               OMP_NUM_THREADS="1", MKL_NUM_THREADS="1",
               TF_NUM_INTRAOP_THREADS="1", TF_NUM_INTEROP_THREADS="1",
               MPLBACKEND="Agg", PIP_NO_CACHE_DIR="1",
               PIP_DISABLE_PIP_VERSION_CHECK="1", PYTHONNOUSERSITE="1")
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
        "Nenhum Python 3.11/3.12 foi encontrado no sistema.")


def _bootstrap_uv(parent):
    """Instala somente o utilitário uv em venv próprio, sem tocar no kernel."""
    bootstrap = Path(parent).resolve() / ".eca-uv-bootstrap-v321"
    if bootstrap.exists() and not (bootstrap / "pyvenv.cfg").is_file():
        raise RuntimeError(f"Bootstrap existente não é venv; não será sobrescrito: {bootstrap}")
    bootstrap_python = bootstrap / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    uv = bootstrap / ("Scripts/uv.exe" if os.name == "nt" else "bin/uv")
    if not bootstrap_python.is_file():
        print("Preparando o instalador isolado de Python (uv).", flush=True)
        subprocess.run([sys.executable, "-m", "venv", str(bootstrap)], check=True, timeout=120)
    installed = ""
    if uv.is_file():
        installed = subprocess.check_output([str(uv), "--version"], text=True, timeout=30).strip()
    if not installed.startswith(f"uv {UV_VERSION} ") and installed != f"uv {UV_VERSION}":
        subprocess.run([str(bootstrap_python), "-m", "pip", "install",
                        "--disable-pip-version-check", "--only-binary=:all:",
                        "--no-deps", "-q", f"uv=={UV_VERSION}"],
                       check=True, timeout=300)
    if not uv.is_file():
        raise RuntimeError("O bootstrap uv não produziu um executável. Reconecte a sessão CPU e tente novamente.")
    return str(uv)


def install_managed_python(parent):
    """Obtém CPython 3.12 em /content (ou diretório equivalente) sem privilégios."""
    parent = Path(parent).resolve()
    uv = _bootstrap_uv(parent)
    managed = parent / ".eca-python-v321"
    uv_env = cpu_environment()
    uv_env.update(UV_PYTHON_INSTALL_DIR=str(managed),
                  UV_CACHE_DIR=str(parent / ".eca-uv-cache-v321"),
                  UV_NO_PROGRESS="1")
    print(f"Kernel Python {sys.version_info.major}.{sys.version_info.minor}; obtendo Python 3.12 gerenciado e isolado.", flush=True)
    subprocess.run([uv, "python", "install", PYTHON_REQUEST, "--no-bin", "--no-progress", "--no-config"],
                   env=uv_env, check=True, timeout=900)
    found = subprocess.check_output(
        [uv, "python", "find", PYTHON_REQUEST, "--managed-python", "--no-project", "--no-config"],
        env=uv_env, text=True, timeout=60).strip()
    if not Path(found).is_file():
        raise RuntimeError("O Python 3.12 gerenciado não foi localizado após o download.")
    version = subprocess.check_output(
        [found, "-c", "import sys,json;print(json.dumps(list(sys.version_info[:2])))"],
        text=True, timeout=30)
    if tuple(json.loads(version)) != (3, 12):
        raise RuntimeError(f"O interpretador gerenciado não é Python 3.12: {found}")
    return found


def resolve_base_python(parent):
    try:
        return compatible_python()
    except RuntimeError:
        return install_managed_python(parent)


def ensure_environment(root, destination, *, allow_install=False, reuse_current=True):
    """Usa ambiente verificado ou cria venv; nunca executa pip no Python do Colab."""
    root = Path(root).resolve()
    pins = read_pins(root / "requirements-eca-colab.txt")
    if reuse_current and probe_versions(sys.executable, pins) == pins:
        return sys.executable
    if not allow_install:
        raise RuntimeError("Ambiente divergente: instale requirements-eca-colab.txt em um venv.")
    destination = Path(destination).resolve()
    base_python = resolve_base_python(destination.parent)
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
