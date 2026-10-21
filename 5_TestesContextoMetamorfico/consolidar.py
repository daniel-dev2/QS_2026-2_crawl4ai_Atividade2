#!/usr/bin/env python3
"""Consolida todas as execuções ONLINE de resultados/ em uma tabela comparativa de prompts
(útil para a Pessoa 2 e a Pessoa 7). Uso:  python consolidar.py [--incluir-offline]"""
import csv, glob, sys
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent
incluir_offline = "--incluir-offline" in sys.argv
linhas = []
for f in sorted(glob.glob(str(BASE / "resultados" / "*" / "evidencias.csv"))):
    if "_offline_" in f and not incluir_offline:
        continue
    for r in csv.DictReader(open(f, encoding="utf-8-sig")):
        r["_pasta"] = Path(f).parent.name
        linhas.append(r)
if not linhas:
    sys.exit("Nenhuma execução online encontrada em resultados/.")

g = defaultdict(list)
for r in linhas:
    g[(r["prompt"], r["modelo"])].append(r)

saida = BASE / "resultados" / "consolidado.csv"
md = ["# Consolidado por prompt", "",
      "| Prompt | Modelo | Execuções | QA válido | PASSOU | FALHOU | REVISAR | Latência média (s) | Variantes instáveis |",
      "|---|---|---|---|---|---|---|---|---|"]
with open(saida, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["prompt", "modelo", "execucoes", "qa_valido_pct", "passou", "falhou", "revisar", "latencia_media_s", "variantes_instaveis"])
    for (prompt, modelo), rs in sorted(g.items()):
        n = len(rs)
        qa = sum(r["qa_valido"] == "sim" for r in rs)
        c = {s: sum((r.get("veredito_final") or r["status"]) == s for r in rs) for s in ("PASSOU", "FALHOU", "REVISAR")}
        lats = [float(r["latencia_s"]) for r in rs if r["latencia_s"] not in ("", None) and float(r["latencia_s"]) > 0]
        lat = round(sum(lats) / len(lats), 1) if lats else ""
        porvar = defaultdict(set)
        for r in rs:
            porvar[(r["_pasta"], r["id_variante"])].add(r["hash_saida"])
        inst = sum(1 for s in porvar.values() if len(s) > 1)
        w.writerow([prompt, modelo, n, f"{100 * qa // n}%", c["PASSOU"], c["FALHOU"], c["REVISAR"], lat, f"{inst}/{len(porvar)}"])
        md.append(f"| {prompt} | {modelo} | {n} | {qa}/{n} ({100 * qa // n}%) | {c['PASSOU']} | {c['FALHOU']} | {c['REVISAR']} | {lat} | {inst}/{len(porvar)} |")
(BASE / "resultados" / "consolidado.md").write_text("\n".join(md), encoding="utf-8")
print("\n".join(md))
print(f"\nGerado: {saida.relative_to(BASE)} e consolidado.md")
