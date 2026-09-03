#!/usr/bin/env python3
"""Capa reprodutível: o padrão à direita é uma evolução ECA 30 real."""
import os
from pathlib import Path
import sys

os.environ.setdefault("MPLBACKEND", "Agg")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from eca_qca_lab.core import eca_evolve


def build():
    navy, white, teal = "#0b1830", "#f1f6ff", "#4de2c0"
    fig = plt.figure(figsize=(16, 6.5), facecolor=navy)
    fig.text(.055, .89, "GEOMAKER  /  LABORATÓRIO COMPUTACIONAL", color=teal,
             fontsize=12, weight="bold")
    fig.text(.055, .68, "AUTÔMATOS", color=white, fontsize=39, weight="bold")
    fig.text(.055, .55, "CELULARES", color=white, fontsize=39, weight="bold")
    fig.text(.058, .44, "Do padrão à prova.", color=teal, fontsize=23)
    fig.text(.058, .32, "Observe. Formule. Teste. Reproduza.", color=white, fontsize=14)
    fig.text(.058, .23, "ECA 30 · 60 · 90   /   INCORPORAÇÃO REVERSÍVEL",
             color="#b6c8e0", fontsize=11)
    fig.text(.058, .11, "MARCELO CLARO LARANJEIRA", color=white, fontsize=14, weight="bold")
    fig.text(.058, .063, "Professor de Geografia e Pedagogo  ·  Crateús–CE",
             color="#b6c8e0", fontsize=10)
    ax = fig.add_axes([.575, .19, .38, .68])
    initial = [0] * 81
    initial[40] = 1
    ax.imshow(eca_evolve(initial, 30, 40), aspect="auto", interpolation="nearest",
              cmap=ListedColormap([navy, teal]), vmin=0, vmax=1)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.text(.59, .11, "REGRA 30  /  81 CÉLULAS  /  40 PASSOS", color=teal, fontsize=10)
    fig.text(.59, .067, "Padrão calculado · fronteira periódica · estado central único",
             color="#b6c8e0", fontsize=9)
    destination = ROOT / "assets/eca-cover.png"
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=120, facecolor=navy)
    plt.close(fig)
    return destination


if __name__ == "__main__":
    print(build())
