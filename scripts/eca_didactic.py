#!/usr/bin/env python3
"""Ilustrações didáticas, separadas das unidades confirmatórias congeladas."""
import argparse
import json
import os
from pathlib import Path
import sys

os.environ.setdefault("MPLBACKEND", "Agg")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np
from eca_qca_lab.core import (
    SUPPORTED_RULES, PROFILE_SPECS, bits_from_index, eca_evolve, eca_step,
    fidelity, oracle_statevector, truth_table, von_neumann_entropy_input,
)
from eca_qca_lab.adapters import BACKENDS, statevector

COLORS = ("#147d92", "#9b4bba", "#d65b2c")


def classic(dest):
    initial = (0,) * 20 + (1,) + (0,) * 20
    fig, axes = plt.subplots(1, 3, figsize=(12, 5), layout="constrained")
    for ax, rule, color in zip(axes, SUPPORTED_RULES, COLORS, strict=True):
        ax.imshow(eca_evolve(initial, rule, 30), cmap=ListedColormap(["#f3f5fa", color]),
                  interpolation="nearest", vmin=0, vmax=1, aspect="auto")
        ax.set(title=f"Regra {rule}", xlabel="Célula (posição)", ylabel="Tempo (passo)")
    fig.suptitle("Uma regra local, três padrões globais", weight="bold", fontsize=15)
    path = dest / "didactic_classic.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    tables = {r: truth_table(r) for r in SUPPORTED_RULES}
    rows = [{"Vizinhança (esq., centro, dir.)": "".join(map(str, row[:3])),
             **{f"Regra {r}": tables[r][i][3] for r in SUPPORTED_RULES}}
            for i, row in enumerate(tables[30])]
    return {"title": "01 · ECA clássico", "rows": rows, "images": [str(path)],
            "interpretation": "Cada linha é um instante; todos os sítios são atualizados a partir da linha anterior. As bordas se conectam. Exemplo didático: 41 células, 30 passos; não integra a amostra confirmatória."}


def oracle(dest):
    initial, n = (0, 0, 1), 3
    rows = []
    for rule in SUPPORTED_RULES:
        reference = oracle_statevector(rule, n, initial=initial)
        for backend in BACKENDS:
            vector = statevector(backend, rule, n, initial=initial)
            observed = bits_from_index(int(np.argmax(abs(vector) ** 2)), 2 * n)
            rows.append({"Regra": rule, "SDK": backend, "Entrada x": "001",
                         "x preservado": "".join(map(str, observed[:n])),
                         "Saída y": "".join(map(str, observed[n:])),
                         "F(x) esperado": "".join(map(str, eca_step(initial, rule))),
                         "Fidelidade": fidelity(vector, reference)})
    return {"title": "02 · A informação de entrada não é apagada", "rows": rows, "images": [],
            "interpretation": "Aqui y começa em 000. A tabela compara saídas de três SDKs com uma referência analítica. Para qualquer y, o contrato é y XOR F(x); aplicar o mesmo oráculo duas vezes devolve o estado original."}


def coherent(dest):
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.5), layout="constrained")
    rows = []
    for ax, rule in zip(axes, SUPPORTED_RULES, strict=True):
        reference = oracle_statevector(rule, 3, plus_input=True)
        image = ax.imshow(abs(reference.reshape(8, 8)) ** 2, vmin=0, vmax=1 / 8, cmap="magma")
        ax.set(title=f"Regra {rule}", xlabel="y (índice da saída)", ylabel="x (índice da entrada)")
        ax.set_xticks(range(8))
        ax.set_yticks(range(8))
        vectors = [statevector(b, rule, 3, plus_input=True) for b in BACKENDS]
        rows.append({"Regra": rule, "Entropia entrada–saída (bits)": von_neumann_entropy_input(reference, 3),
                     "Fidelidade mínima SDK × referência": min(fidelity(v, reference) for v in vectors)})
    fig.colorbar(image, ax=axes, label="Probabilidade conjunta P(x,y)", shrink=.8)
    fig.suptitle("Superposição: correlações entre entrada e saída", weight="bold")
    path = dest / "didactic_coherence.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return {"title": "03 · Probabilidade não é fase", "rows": rows, "images": [str(path)],
            "interpretation": "As matrizes mostram probabilidades da referência analítica. A tabela também verifica amplitudes dos três SDKs por fidelidade. Entropia positiva nesta partição de um estado puro indica emaranhamento; não demonstra vantagem computacional."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("classic", "oracle", "coherent", "spec"), required=True)
    parser.add_argument("--profile", choices=("smoke", "paper"), default="smoke")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.stage == "spec":
        result = {"title": "Desenho congelado", "rows": [{"Parâmetro": k, "Valor": str(v)} for k, v in PROFILE_SPECS[args.profile].to_dict().items()], "images": []}
    else:
        result = {"classic": classic, "oracle": oracle, "coherent": coherent}[args.stage](args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
