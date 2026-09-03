#!/usr/bin/env python3
import argparse,json,tempfile,zipfile,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from eca_qca_lab.core import sha256_file
from eca_qca_lab.experiment import PRIMARY_ARTIFACTS
def verify_dir(d):
 m=json.loads((d/"manifest.json").read_text());decl=m["artifact_sha256"]
 if m["schema_version"]!="3.1" or set(decl)!=set(PRIMARY_ARTIFACTS):raise ValueError("manifesto inválido")
 for n in PRIMARY_ARTIFACTS:
  if not (d/n).is_file() or sha256_file(d/n)!=decl[n]:raise ValueError(f"hash inválido: {n}")
 return {"verified":len(PRIMARY_ARTIFACTS),"schema_version":"3.1"}
def verify(p):
 if p.is_dir():return verify_dir(p)
 with tempfile.TemporaryDirectory() as t:
  with zipfile.ZipFile(p) as z:z.extractall(t)
  return verify_dir(Path(t))
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("path",type=Path);a=p.parse_args();print(json.dumps(verify(a.path.resolve()),indent=2))
