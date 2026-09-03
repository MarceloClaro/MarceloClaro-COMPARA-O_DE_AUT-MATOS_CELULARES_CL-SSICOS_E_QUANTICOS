#!/usr/bin/env python3
"""Validação manual CPU: sem API, GitHub Actions ou serviço de execução pago."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import uuid

from eca_colab_support import cpu_environment, run_json

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=("smoke", "paper"), default="smoke")
    parser.add_argument("--notebook", action="store_true", help="duas passagens smoke no mesmo kernel Jupyter")
    parser.add_argument("--notebook-executor", choices=("jupyter", "namespace"), default="jupyter")
    parser.add_argument("--output-base", type=Path, default=ROOT/"eca_validation_logs")
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    output = args.output_base.resolve() / stamp
    output.mkdir(parents=True, exist_ok=False)
    print(f"Validação manual CPU · {args.profile}\nLogs: {output}", flush=True)
    env = cpu_environment()
    subprocess.run([sys.executable, "-m", "pip", "check"], check=True, env=env)
    tests = sorted(str(p) for p in (ROOT/"tests").glob("test_eca_*.py"))
    tested = subprocess.run([sys.executable, "-m", "pytest", "-q", *tests], cwd=ROOT, env=env,
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=900)
    (output/"pytest.log").write_text(tested.stdout, encoding="utf-8")
    print(tested.stdout, flush=True)
    tested.check_returncode()
    report = run_json(sys.executable, ROOT, "run_eca_experiment.py",
                      ["--profile", args.profile, "--output-dir", str(output/args.profile)], timeout=1200)
    verified = run_json(sys.executable, ROOT, "verify_eca_bundle.py", [report["bundle"]])
    print(json.dumps({"counts": report["counts"], "verification": verified}, indent=2), flush=True)
    if args.notebook:
        subprocess.run([sys.executable, str(ROOT/"scripts/validate_eca_notebook.py"),
                        "--profile", "smoke", "--output-dir", str(output/"notebook-runs"),
                        "--report", str(output/"notebook_validation.json"), "--repeat-run-all",
                        "--executor", args.notebook_executor],
                       cwd=ROOT, env=env, check=True, timeout=3600)
    print("Validação concluída. Esta reprodução não constitui nova confirmação independente.")


if __name__ == "__main__":
    main()
