#!/usr/bin/env python3
import argparse,json,sys,os,uuid
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from eca_colab_support import cpu_environment
os.environ.update(cpu_environment())
from eca_qca_lab.experiment import run_experiment
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--profile",choices=("smoke","paper"),default="smoke");p.add_argument("--output-dir",type=Path);p.add_argument("--allow-missing-tfq","--skip-tfq",dest="allow_missing_tfq",action="store_true",help="permite falha de TFQ apenas para diagnóstico; não habilita confirmação");a=p.parse_args()
 destination=a.output_dir or Path("eca_qca_results")/a.profile/(datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"-"+uuid.uuid4().hex[:8])
 r=run_experiment(destination,profile=a.profile,require_tfq=not a.allow_missing_tfq,project_root=ROOT);print(json.dumps(r,ensure_ascii=False,indent=2))
