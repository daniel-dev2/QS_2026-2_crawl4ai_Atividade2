#!/usr/bin/env python3
"""Grafico simples: F1 lexical por caso e versao, com linha do tau."""
import csv, sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

d = Path(__file__).resolve().parent
rows = list(csv.DictReader(open(d / "resultados_f1.csv", encoding="utf-8-sig")))
casos = sorted({r["caso"] for r in rows})
f = {(r["caso"], r["versao"]): float(r["f1"]) for r in rows}
tau = float(rows[0]["tau"])
x = range(len(casos)); w = 0.38
fig, ax = plt.subplots(figsize=(8, 4.2))
ax.bar([i - w / 2 for i in x], [f[(c, "A")] for c in casos], w, label="Versão A (P1)", color="#9aa5b1")
ax.bar([i + w / 2 for i in x], [f[(c, "B")] for c in casos], w, label="Versão B (P2)", color="#2f6fb3")
ax.axhline(tau, color="#c0392b", ls="--", lw=1.2, label=f"τ = {tau:.2f}")
ax.set_xticks(list(x)); ax.set_xticklabels(casos); ax.set_ylim(0, 1.05)
ax.set_ylabel("F1 lexical"); ax.set_title("F1 lexical por caso e versão")
ax.legend(loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.1))
fig.tight_layout(); fig.savefig(d / "grafico_f1.png", dpi=160)
print("ok")
