#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from eca_qca_lab.experiment import run_experiment
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--profile",choices=("smoke","paper"),default="smoke");p.add_argument("--output-dir",type=Path,default=Path("eca_qca_results"));p.add_argument("--skip-tfq",action="store_true");a=p.parse_args();r=run_experiment(a.output_dir,profile=a.profile,require_tfq=not a.skip_tfq,project_root=ROOT);print(json.dumps(r,ensure_ascii=False,indent=2))
