#!/usr/bin/env python3
"""Verifica o conjunto fechado do ZIP sem extrair caminhos fornecidos por ele."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eca_qca_lab.experiment import PRIMARY_ARTIFACTS

METADATA = ("manifest.json", "validation_report.json")
MEMBERS = (*PRIMARY_ARTIFACTS, *METADATA, "SHA256SUMS.txt")
MAX_TOTAL_BYTES = 128 * 1024 * 1024


def _verify(read_bytes):
    manifest = json.loads(read_bytes("manifest.json"))
    version = manifest["schema_version"]
    declared = manifest["artifact_sha256"]
    if version not in {"3.1", "3.2"} or set(declared) != set(PRIMARY_ARTIFACTS):
        raise ValueError("manifesto inválido")
    for name in PRIMARY_ARTIFACTS:
        if sha256(read_bytes(name)).hexdigest() != declared[name]:
            raise ValueError(f"hash inválido: {name}")
    metadata_count = 0
    if version == "3.2":
        entries = {}
        for line in read_bytes("SHA256SUMS.txt").decode("utf-8").splitlines():
            digest, name = line.split("  ", 1)
            if name in entries:
                raise ValueError("hash duplicado")
            entries[name] = digest
        if set(entries) != set((*PRIMARY_ARTIFACTS, *METADATA)):
            raise ValueError("conjunto de hashes inválido")
        for name, digest in entries.items():
            if sha256(read_bytes(name)).hexdigest() != digest:
                raise ValueError(f"hash inválido: {name}")
        if manifest["result"] != json.loads(read_bytes("validation_report.json")):
            raise ValueError("relatório e manifesto divergentes")
        metadata_count = len(METADATA)
    return {"verified": len(PRIMARY_ARTIFACTS), "metadata_verified": metadata_count,
            "schema_version": version, "integrity_only": True}


def verify_dir(directory):
    directory = Path(directory)
    return _verify(lambda name: (directory/name).read_bytes())


def verify(path):
    path = Path(path)
    if path.is_dir():
        return verify_dir(path)
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(MEMBERS) or set(names) != set(MEMBERS):
            raise ValueError("membros do ZIP inválidos, duplicados ou inesperados")
        if sum(info.file_size for info in archive.infolist()) > MAX_TOTAL_BYTES:
            raise ValueError("ZIP excede o limite de tamanho")
        return _verify(archive.read)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.path.resolve()), indent=2))
