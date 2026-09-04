"""Suporte Colab: somente biblioteca padrão; nenhum SDK no kernel da interface."""
from __future__ import annotations

import html
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
from urllib.request import urlopen
import zipfile

UV_VERSION = "0.12.9"
PIP_VERSION = "26.2.1"
PYTHON_REQUEST = "3.12"
# Wheels oficiais PyPI; hashes verificados em 2026-09-04. O bootstrap automático
# tem como alvo o Linux x86_64 do Colab. Outros sistemas podem usar o venv local.
UV_WHEELS = {
    ("Linux", "x86_64"): (
        "https://files.pythonhosted.org/packages/37/4b/cd04809c7ad5149faac55160925bd67aab43f803f6c01be1c32aec7d24d9/"
        "uv-0.12.9-py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
        "5badfd805fd88bf99b4b4f044f6e8f762f1892cab27477f4427bb473e93dd049"),
}
MAX_WHEEL_BYTES = 64 * 1024 * 1024
MAX_UV_BYTES = 128 * 1024 * 1024


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


def _run_checked(command, *, stage, timeout, env=None):
    """Mantém stdout/stderr no erro; o traceback genérico não basta para diagnosticar."""
    try:
        return subprocess.run(command, check=True, text=True, capture_output=True,
                              timeout=timeout, env=env or cpu_environment())
    except subprocess.CalledProcessError as exc:
        output = (exc.stdout or "") + "\n" + (exc.stderr or "")
        raise RuntimeError(f"{stage} falhou (código {exc.returncode}).\n{output[-6000:]}") from None
    except subprocess.TimeoutExpired as exc:
        output = exc.stderr or exc.stdout or "Sem saída adicional."
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        raise RuntimeError(f"{stage} excedeu {timeout}s. Reexecute a etapa após conferir a conexão.\n"
                           + output[-6000:]) from None


def _bootstrap_uv(parent):
    """Obtém o binário uv verificado sem pip, venv ou ensurepip do hospedeiro."""
    key = (platform.system(), platform.machine().lower())
    if key not in UV_WHEELS:
        raise RuntimeError("Bootstrap automático disponível para Colab/Linux x86_64. "
                           "Neste sistema, use um venv local com requirements-eca-colab.txt.")
    url, wheel_digest = UV_WHEELS[key]
    parent = Path(parent).resolve()
    bootstrap = parent / ".eca-uv-bootstrap-v322"
    uv = bootstrap / "uv"
    receipt_path = bootstrap / "receipt.json"
    if bootstrap.is_symlink():
        raise RuntimeError(f"Bootstrap simbólico não será sobrescrito: {bootstrap}")
    if bootstrap.exists():
        if not receipt_path.is_file() or not uv.is_file():
            raise RuntimeError(f"Bootstrap existente não reconhecido; não será sobrescrito: {bootstrap}")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if (uv.is_symlink() or uv.stat().st_size > MAX_UV_BYTES
                or receipt.get("version") != UV_VERSION
                or receipt.get("wheel_sha256") != wheel_digest
                or receipt.get("binary_sha256") != sha256(uv.read_bytes()).hexdigest()):
            raise RuntimeError(f"Falha de integridade do instalador: {bootstrap}. Preserve os arquivos e use uma nova sessão.")
        return str(uv)
    print("Obtendo uv independente de pip/venv do Colab; verificando SHA-256.", flush=True)
    try:
        with urlopen(url, timeout=60) as response:
            wheel_bytes = response.read(MAX_WHEEL_BYTES + 1)
    except (OSError, TimeoutError) as exc:
        raise RuntimeError(f"Download do uv interrompido: {exc}. Confira a conexão e reexecute esta etapa.") from None
    if len(wheel_bytes) > MAX_WHEEL_BYTES or sha256(wheel_bytes).hexdigest() != wheel_digest:
        raise RuntimeError("SHA-256 ou tamanho inválido no wheel uv; nenhum binário foi executado.")
    member = f"uv-{UV_VERSION}.data/scripts/uv"
    with zipfile.ZipFile(io.BytesIO(wheel_bytes)) as archive:
        if archive.namelist().count(member) != 1 or archive.getinfo(member).file_size > MAX_UV_BYTES:
            raise RuntimeError("Wheel uv não contém exatamente o binário esperado dentro do limite de tamanho.")
        binary = archive.read(member)  # Não extrair caminhos fornecidos pelo ZIP.
    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".eca-uv-stage-", dir=parent) as staging:
        staged = Path(staging)
        staged_uv = staged / "uv"
        staged_uv.write_bytes(binary)
        staged_uv.chmod(0o755)
        version = _run_checked([str(staged_uv), "--version"], stage="Verificação uv", timeout=30).stdout.strip()
        if version != f"uv {UV_VERSION}" and not version.startswith(f"uv {UV_VERSION} "):
            raise RuntimeError(f"Versão uv inesperada: {version}")
        (staged / "receipt.json").write_text(json.dumps({
            "version": UV_VERSION, "source": url, "wheel_sha256": wheel_digest,
            "binary_sha256": sha256(binary).hexdigest()}, indent=2), encoding="utf-8")
        staged.rename(bootstrap)  # Publicar o diretório somente após todas as verificações.
    return str(uv)


def uv_environment(parent):
    parent = Path(parent).resolve()
    env = cpu_environment()
    env.update(UV_PYTHON_INSTALL_DIR=str(parent / ".eca-python-v322"),
               UV_CACHE_DIR=str(parent / ".eca-uv-cache-v322"), UV_NO_PROGRESS="1")
    return env


def install_managed_python(parent):
    """Obtém CPython 3.12 em /content (ou diretório equivalente) sem privilégios."""
    parent = Path(parent).resolve()
    uv = _bootstrap_uv(parent)
    uv_env = uv_environment(parent)
    print(f"Kernel Python {sys.version_info.major}.{sys.version_info.minor}; obtendo Python 3.12 gerenciado e isolado.", flush=True)
    _run_checked([uv, "python", "install", PYTHON_REQUEST, "--no-bin", "--no-progress", "--no-config"],
                 stage="Instalação Python 3.12", env=uv_env, timeout=900)
    found = _run_checked(
        [uv, "python", "find", PYTHON_REQUEST, "--managed-python", "--no-project", "--no-config"],
        stage="Localização Python 3.12", env=uv_env, timeout=60).stdout.strip()
    if not Path(found).is_file():
        raise RuntimeError("O Python 3.12 gerenciado não foi localizado após o download.")
    version = _run_checked(
        [found, "-c", "import sys,json;print(json.dumps(list(sys.version_info[:2])))"],
        stage="Verificação Python 3.12", timeout=30).stdout
    if tuple(json.loads(version)) != (3, 12):
        raise RuntimeError(f"O interpretador gerenciado não é Python 3.12: {found}")
    return found


def resolve_base_python(parent):
    try:
        return compatible_python()
    except RuntimeError:
        pass
    return install_managed_python(parent)


def ensure_environment(root, destination, *, allow_install=False, reuse_current=True):
    """Usa ambiente verificado ou cria venv; nunca executa pip no Python do Colab."""
    root = Path(root).resolve()
    pins = read_pins(root / "requirements-eca-colab.txt")
    if reuse_current and probe_versions(sys.executable, pins) == pins:
        return sys.executable
    if not allow_install:
        raise RuntimeError("Ambiente divergente: instale requirements-eca-colab.txt em um venv.")
    if Path(destination).is_symlink():
        raise RuntimeError(f"Destino simbólico não será sobrescrito: {destination}")
    destination = Path(destination).resolve()
    if destination.exists() and not (destination / "pyvenv.cfg").is_file():
        raise RuntimeError(f"Diretório existente não é venv; não será sobrescrito: {destination}")
    python = destination / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.is_file():
        base_python = resolve_base_python(destination.parent)
        uv = _bootstrap_uv(destination.parent)
        print("Criando ambiente científico com uv, sem depender do venv/ensurepip do Colab.", flush=True)
        _run_checked([uv, "venv", "--python", base_python, "--no-python-downloads", "--no-project",
                      "--no-config", "--no-progress", str(destination)],
                     stage="Criação do ambiente científico", env=uv_environment(destination.parent), timeout=120)
    if probe_versions(python, {"pip": PIP_VERSION}) != {"pip": PIP_VERSION}:
        uv = _bootstrap_uv(destination.parent)
        _run_checked([uv, "pip", "install", "--python", str(python), "--only-binary=:all:",
                      "--no-config", "--no-progress", f"pip=={PIP_VERSION}"],
                     stage="Preparação pip científico", env=uv_environment(destination.parent), timeout=300)
    if probe_versions(python, pins) != pins:
        print("Instalando a matriz fixada. A primeira execução pode levar alguns minutos.", flush=True)
        _run_checked([str(python), "-m", "pip", "install", "--disable-pip-version-check",
                        "--prefer-binary", "--only-binary=tensorflow-quantum,tensorflow,numpy,qiskit",
                        "-q", "-r", str(root / "requirements-eca-colab.txt")],
                     stage="Instalação da matriz científica", env=cpu_environment(), timeout=1800)
    if probe_versions(python, pins) != pins:
        raise RuntimeError("Instalação incompleta. Reexecute esta célula; não avance sem matriz válida.")
    _run_checked([str(python), "-m", "pip", "check"], stage="Checagem de dependências", timeout=60)
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
