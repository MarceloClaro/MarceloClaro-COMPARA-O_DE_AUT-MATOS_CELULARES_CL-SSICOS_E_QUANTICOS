#!/usr/bin/env python3
"""Executa o notebook célula a célula, opcionalmente duas vezes no mesmo namespace."""
import argparse,io,json,os,re,resource,time,traceback
from contextlib import redirect_stdout,redirect_stderr
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];NB=ROOT/"COMPARAÇÃO_DE_AUTÔMATOS_CELULARES_CLÁSSICOS_E_QUANTICOS_Performance,_robustez_ao_ruÍdo_e_aplicações_.ipynb"
# Corrige o nome em sistemas Unicode sem reconstruir caminho manualmente.
NB=next(ROOT.glob("COMPARAÇÃO_DE_AUTÔMATOS_CELULARES_CLÁSSICOS_E_QUANTICOS_*.ipynb"))
def structure(nb):
 cells=nb["cells"];codes=[x for x in cells if x["cell_type"]=="code"];allsrc="\n".join("".join(x["source"]) for x in cells);codesrc="\n".join("".join(x["source"]) for x in codes)
 checks={"21_cells":len(cells)==21,"11_code":len(codes)==11,"author":"MARCELO CLARO LARANJEIRA" in allsrc,"orcid":"0000-0001-8996-2887" in allsrc,"no_guard":"TEST_OPENED" not in codesrc,"tfq_semantics":"não é uma quarta implementação independente" in allsrc}
 for i,x in enumerate(codes):compile("".join(x["source"]),f"code-{i}","exec")
 if not all(checks.values()):raise AssertionError(checks)
 return checks
def execute(nb,ns):
 out=io.StringIO();start=time.perf_counter()
 with redirect_stdout(out),redirect_stderr(out):
  for i,x in enumerate(nb["cells"]):
   if x["cell_type"]=="code":
    try:exec(compile("".join(x["source"]),f"cell-{i+1}","exec"),ns)
    except Exception:traceback.print_exc();raise RuntimeError(f"célula {i+1}")
 txt=out.getvalue();m=re.findall(r"(\d+) passed",txt);return {"seconds":time.perf_counter()-start,"pytest_passed":int(m[-1]) if m else None,"output_tail":txt[-6000:],"run_state":ns.get("ECA_RUN_STATE")}
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--profile",choices=("smoke","paper"),default="smoke");p.add_argument("--output-dir",type=Path,default=ROOT/"eca_qca_results");p.add_argument("--report",type=Path,default=ROOT/"eca_notebook_validation.json");p.add_argument("--repeat-run-all",action="store_true");p.add_argument("--allow-install",action="store_true");a=p.parse_args();nb=json.loads(NB.read_text());checks=structure(nb);os.environ["ECA_PROFILE"]=a.profile;os.environ["ECA_OUTPUT_DIR"]=str(a.output_dir.resolve());os.environ["ECA_ALLOW_INSTALL"]="1" if a.allow_install else os.environ.get("ECA_ALLOW_INSTALL","0");ns={"__name__":"__main__"};runs=[];status="passed";error=None
 try:
  runs.append(execute(nb,ns))
  if a.repeat_run_all:runs.append(execute(nb,ns))
 except Exception as e:status="failed";error=f"{type(e).__name__}: {e}"
 report={"schema_version":"3.1","status":status,"error":error,"profile":a.profile,"checks":checks,"runs":runs,"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss};a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n");print(json.dumps({k:v for k,v in report.items() if k!="runs"},ensure_ascii=False,indent=2));raise SystemExit(0 if status=="passed" else 1)
