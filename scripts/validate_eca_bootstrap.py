#!/usr/bin/env python3
"""Integração manual com downloads reais; não confundir com execução no Colab."""
import argparse
from datetime import datetime, timezone
import importlib.abc
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import eca_colab_support as support

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True, help="diretório novo para a instalação real")
    parser.add_argument("--allow-download", action="store_true", help="autoriza baixar Python e a matriz científica CPU")
    parser.add_argument("--hide-system-python", action="store_true", help="limita PATH ao Python hospedeiro para exercitar o fallback")
    args = parser.parse_args()
    if not args.allow_download:
        parser.error("use --allow-download para autorizar a instalação isolada")
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    report = {"started_utc": datetime.now(timezone.utc).isoformat(),
              "host_python": sys.version, "host_executable": sys.executable,
              "system_python_hidden": args.hide_system_python,
              "colab_session": False, "commands": [], "status": "running"}
    original_path = os.environ.get("PATH", "")
    original_runner = support._run_checked

    class ForbidHostInstallTools(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname.split(".")[0] in {"pip", "venv", "ensurepip"}:
                raise AssertionError(f"Dependência proibida no hospedeiro: {fullname}")

    blocker = ForbidHostInstallTools()

    def checked(command, **kwargs):
        if command[0] == sys.executable and "-m" in command:
            raise AssertionError("Instalação por módulo no Python hospedeiro")
        report["commands"].append([str(arg) for arg in command])
        return original_runner(command, **kwargs)

    started = time.monotonic()
    try:
        if args.hide_system_python:
            os.environ["PATH"] = str(Path(sys.executable).parent)
        sys.meta_path.insert(0, blocker)
        support._run_checked = checked
        python = support.ensure_environment(ROOT, output / "scientific", allow_install=True, reuse_current=False)
        first_count = len(report["commands"])
        assert support.ensure_environment(ROOT, output / "scientific", allow_install=True, reuse_current=False) == python
        reentry_commands = report["commands"][first_count:]
        assert reentry_commands == [[python, "-m", "pip", "check"]]
        report.update(scientific_python=python, reentry_without_install=True,
                      host_install_tools_forbidden=True,
                      versions=support.probe_versions(python, support.read_pins(ROOT / "requirements-eca-colab.txt")),
                      scientific_python_version=subprocess.check_output([python, "--version"], text=True).strip(),
                      status="passed")
    except Exception as exc:
        report.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        os.environ["PATH"] = original_path
        support._run_checked = original_runner
        if blocker in sys.meta_path:
            sys.meta_path.remove(blocker)
        report["seconds"] = time.monotonic() - started
        (output / "installation.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps({"status": report["status"], "report": str(output / "installation.json"),
                          "seconds": report["seconds"]}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
