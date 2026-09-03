import ast,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];NB=ROOT/"COMPARAÇÃO_DE_AUTÔMATOS_CELULARES_CLÁSSICOS_E_QUANTICOS_Performance,_robustez_ao_ruído_e_aplicações_.ipynb"
def load():return json.loads(NB.read_text())
def test_files():
 names=["README.md","CITATION.cff","docs/SDD.md","docs/PROTOCOL.md","docs/ARTICLE_PLAN.md","docs/ECA_VALIDATION.md","eca_qca_lab/core.py","eca_qca_lab/adapters.py","eca_qca_lab/experiment.py","scripts/run_eca_experiment.py","scripts/verify_eca_bundle.py"]
 assert all((ROOT/n).is_file() for n in names)
def test_pins():
 r=(ROOT/"requirements-eca-colab.txt").read_text();assert all(x in r for x in ["qiskit==2.5.2","PennyLane==0.45.1","cirq-core==1.5.0","tensorflow==2.18.1","tf-keras==2.18.0","tensorflow-quantum==0.7.6"])
def test_protocol():
 p=(ROOT/"docs/PROTOCOL.md").read_text().lower();assert "não permitido" in p and "vantagem quântica" in p and "réplicas" in p and "bonferroni–hoeffding" in p and "emenda 1" in p
def test_notebook_shape():
 n=load();assert len(n["cells"])==21 and sum(x["cell_type"]=="code" for x in n["cells"])==11
def test_code_compiles():
 for i,x in enumerate(load()["cells"]):
  if x["cell_type"]=="code":ast.parse("".join(x["source"]),filename=f"cell-{i}")
def test_cell_three_light():
 s="".join(load()["cells"][2]["source"]);assert "tensorflow" not in s.lower() and "nvidia-smi" not in s and "RuntimeError" not in s
def test_tfq_semantics():
 s="\n".join("".join(x["source"]) for x in load()["cells"]);assert "não é uma quarta implementação independente" in s and "processo isolado" in s
def test_profiles_and_reentry():
 s="\n".join("".join(x["source"]) for x in load()["cells"]);codes="\n".join("".join(x["source"]) for x in load()["cells"] if x["cell_type"]=="code");assert 'PROFILE not in {"smoke", "paper"}' in s;assert "ECA_RUN_STATE" in s and "TEST_OPENED" not in codes
def test_generator_check():assert subprocess.run([sys.executable,str(ROOT/"scripts/build_eca_colab.py"),"--check"]).returncode==0
