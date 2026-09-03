#!/usr/bin/env python3
"""Gera deterministicamente o notebook Colab ECA/QCA."""
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NB=ROOT/"COMPARAÇÃO_DE_AUTÔMATOS_CELULARES_CLÁSSICOS_E_QUANTICOS_Performance,_robustez_ao_ruído_e_aplicações_.ipynb"
def m(text,id):return {"cell_type":"markdown","id":id,"metadata":{},"source":text.strip().splitlines(keepends=True)}
def c(text,id):return {"cell_type":"code","execution_count":None,"id":id,"metadata":{},"outputs":[],"source":text.strip().splitlines(keepends=True)}
def build():
 cells=[
 m(r'''<a href="https://colab.research.google.com/github/MarceloClaro/MarceloClaro-COMPARA-O_DE_AUT-MATOS_CELULARES_CL-SSICOS_E_QUANTICOS/blob/main/COMPARA%C3%87%C3%83O_DE_AUT%C3%94MATOS_CELULARES_CL%C3%81SSICOS_E_QUANTICOS_Performance%2C_robustez_ao_ru%C3%ADdo_e_aplica%C3%A7%C3%B5es_.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg"/></a>
# Laboratório ECA/QCA multiframework v3.1
**MARCELO CLARO LARANJEIRA — [@MarceloClaro](https://github.com/MarceloClaro)**<br>
Professor de Geografia e Pedagogo · Crateús–CE<br>
[GeoMaker](https://bit.ly/geomaker) · [ORCID 0000-0001-8996-2887](https://orcid.org/0000-0001-8996-2887) · [Instagram](https://www.instagram.com/marceloclaro.geomaker/)

Regras 30, 60 e 90 e $U_F|x\rangle|y\rangle=|x\rangle|y\oplus F(x)\rangle$ em Qiskit, PennyLane e Cirq. TFQ integra TensorFlow–Cirq e **não é uma quarta implementação independente**. Sem alegação de vantagem quântica.''',"title"),
 m('''## Antes de executar
Use **CPU**, mantenha `smoke` e clique em **Executar tudo**. Repetir é seguro: não existe bloqueio de teste aberto.

**502 em `prod.colab.dev/api/kernelspecs`:** a VM não criou o kernel; reconecte uma sessão CPU. **Compatibilidade:** TFQ roda em **processo isolado** com TF 2.18.1, TF-Keras 2.18.0 e Cirq 1.5.0.''',"before"),
 c('''import os,sys
from pathlib import Path
PROFILE = os.environ.get("ECA_PROFILE", "smoke").strip().lower()
if PROFILE not in {"smoke", "paper"}: raise ValueError("perfil inválido")
IN_COLAB = "google.colab" in sys.modules
RUN_NUMBER = int(globals().get("ECA_RUN_STATE", {}).get("run_number", 0)) + 1
OUTPUT_DIR = Path(os.environ.get("ECA_OUTPUT_DIR", "/content/eca_qca_results" if IN_COLAB else "eca_qca_results")).resolve()
print(f"Perfil={PROFILE}; CPU; execução={RUN_NUMBER}")''',"config"),
 m('''## 1. Ambiente
A célula instala uma matriz única antes de importar qualquer SDK. Se `pip` for interrompido, descarte a VM parcial e recomece.''',"env-md"),
 c('''import importlib.metadata,subprocess
PINS={"numpy":"2.0.2","qiskit":"2.5.2","qiskit-aer":"0.17.2","PennyLane":"0.45.1","cirq-core":"1.5.0","tensorflow":"2.18.1","tf-keras":"2.18.0","tensorflow-quantum":"0.7.6","pyparsing":"3.2.5","matplotlib":"3.10.6","pandas":"2.2.2","pytest":"8.4.2","nbformat":"5.10.4","nbclient":"0.10.2","psutil":"7.0.0"}
def version(name):
 try:return importlib.metadata.version(name)
 except importlib.metadata.PackageNotFoundError:return None
bad={n:(version(n),v) for n,v in PINS.items() if version(n)!=v}
if bad:
 if not (IN_COLAB or os.environ.get("ECA_ALLOW_INSTALL")=="1"): raise EnvironmentError(f"dependências: {bad}")
 subprocess.run([sys.executable,"-m","pip","install","--disable-pip-version-check","-q",*[f"{n}=={v}" for n,v in PINS.items()]],check=True)
bad={n:(version(n),v) for n,v in PINS.items() if version(n)!=v}
if bad: raise EnvironmentError(f"matriz incompatível: {bad}")
print("Matriz verificada; TensorFlow ainda não foi importado no kernel.")''',"install"),
 m('''## 2. Código versionado
No Colab, um clone raso é criado uma vez; localmente é usado o checkout atual.''',"source-md"),
 c('''import subprocess
REPOSITORY="https://github.com/MarceloClaro/MarceloClaro-COMPARA-O_DE_AUT-MATOS_CELULARES_CL-SSICOS_E_QUANTICOS.git"
PROJECT_ROOT=Path.cwd()
if not (PROJECT_ROOT/"eca_qca_lab").is_dir():
 PROJECT_ROOT=Path("/content/eca-qca-lab-v3")
 if not (PROJECT_ROOT/".git").is_dir(): subprocess.run(["git","clone","--depth","1","--branch","main",REPOSITORY,str(PROJECT_ROOT)],check=True)
if str(PROJECT_ROOT) not in sys.path:sys.path.insert(0,str(PROJECT_ROOT))
print(PROJECT_ROOT)''',"source"),
 c('''from eca_qca_lab.core import *
from eca_qca_lab.adapters import BACKENDS,statevector
from eca_qca_lab.experiment import run_experiment
print({n:version(n) for n in PINS});print(PROFILE_SPECS[PROFILE].to_dict())''',"imports"),
 m('''## 3. TDD antes do experimento
Numeração, sincronia, reversibilidade, ordenação, três SDKs, TFQ e contratos são verificados antes dos resultados.''',"tdd-md"),
 c('''tests=sorted(str(p) for p in (PROJECT_ROOT/"tests").glob("test_eca_*.py"))
tested=subprocess.run([sys.executable,"-m","pytest","-q",*tests],cwd=PROJECT_ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
print(tested.stdout)
if tested.returncode:raise AssertionError("TDD falhou; experimento bloqueado")''',"tdd"),
 m('''## 4. ECA clássico
$f_r(l,c,d)=(r>>(4l+2c+d))\\&1$; atualização síncrona e fronteira periódica.''',"classic-md"),
 c('''for rule in (30,60,90):print(rule,"".join(str(row[3]) for row in truth_table(rule)))
for row in eca_evolve((0,0,1,0,0),30,8):print("".join("█" if b else "·" for b in row))''',"classic"),
 m('''## 5. Incorporação reversível
`x` é preservado e `F(x)` entra por XOR em `y`; a ordem de qubits é normalizada explicitamente.''',"oracle-md"),
 c('''initial=(0,0,1);ref=oracle_statevector(30,3,initial=initial)
for backend in BACKENDS:print(backend,fidelity(statevector(backend,30,3,initial=initial),ref))
print("esperado",eca_step(initial,30))''',"oracle"),
 m('''## 6. Superposição e emaranhamento
`|+⟩ⁿ|0⟩ⁿ` detecta erros de fase; a entropia mede a partição entrada–saída. TFQ será validado em subprocesso.''',"coherent-md"),
 c('''for rule in (30,60,90):
 ref=oracle_statevector(rule,3,plus_input=True);fs=[fidelity(statevector(b,rule,3,plus_input=True),ref) for b in BACKENDS]
 print(rule,min(fs),von_neumann_entropy_input(ref,3))''',"coherent"),
m('''## 7. Protocolo completo
Gates determinísticos e TFQ antecedem ruído. A unidade é `(regra,estado,p,semente)`; IC95% usa bootstrap e a decisão conjunta usa banda Bonferroni–Hoeffding. Warm-up é excluído e tempos não provam vantagem.''',"run-md"),
 c('''OUTPUT_DIR.mkdir(parents=True,exist_ok=True)
REPORT=run_experiment(OUTPUT_DIR,profile=PROFILE,require_tfq=True,project_root=PROJECT_ROOT)
if not REPORT["technical_gate_passed"]:raise AssertionError("gate técnico falhou")
print(REPORT["counts"]);print(REPORT["numerics"])''',"run"),
 c('''import json
subprocess.run([sys.executable,str(PROJECT_ROOT/"scripts"/"verify_eca_bundle.py"),str(OUTPUT_DIR)],cwd=PROJECT_ROOT,check=True)
manifest=json.loads((OUTPUT_DIR/"manifest.json").read_text());print("hashes",len(manifest["artifact_sha256"]));print(REPORT["bundle"])
try:
 from google.colab import files
 files.download(REPORT["bundle"])
except ImportError:pass''',"artifacts"),
 m('''## 8. Exercícios e gabaritos
1. Encontre uma colisão de `F₃₀`. 2. Prove que `U_F²=I`. 3. Por que bases não bastam para fase? 4. Para `n=5,p=.1`, calcule BER e sucesso. 5. Por que TFQ não é independente?

<details><summary>Gabaritos</summary>Colisão implica não unitariedade no mesmo espaço; XOR duas vezes cancela; probabilidades apagam fase; BER=.1 e sucesso=.9⁵=.59049; TFQ executa o mesmo circuito Cirq.</details>''',"exercises"),
 c('''ECA_RUN_STATE={"status":"completed","profile":PROFILE,"run_number":RUN_NUMBER,"technical_gate_passed":bool(REPORT["technical_gate_passed"]),"bundle_sha256":REPORT["bundle_sha256"]}
print("Execução reentrante concluída:",ECA_RUN_STATE)''',"final")]
 assert len(cells)==21 and sum(x["cell_type"]=="code" for x in cells)==11
 return {"cells":cells,"metadata":{"accelerator":"CPU","colab":{"name":NB.name,"provenance":[]},"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python","version":"3.12"}},"nbformat":4,"nbformat_minor":5}
def text():return json.dumps(build(),ensure_ascii=False,indent=1)+"\n"
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--check",action="store_true");a=p.parse_args();wanted=text()
 if a.check:raise SystemExit(0 if NB.is_file() and NB.read_text()==wanted else 1)
 NB.write_text(wanted,encoding="utf-8");print(NB)
