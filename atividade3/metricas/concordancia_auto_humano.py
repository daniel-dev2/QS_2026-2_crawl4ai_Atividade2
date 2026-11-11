#!/usr/bin/env python3
"""
Concordancia automatico-humano (M3): iguais/12. Rodar SO depois que a P6 (R1)
e a P7 (consenso de CT01/CT05) fecharem a decisao humana final.

Entrada: resultados_f1.csv (esta pasta) e decisao_humana.csv com colunas
  caso,versao,aprovacao_humana   (1/0 ou aprova/reprova)
Saida: tabela_auto_humano.csv + lista de divergencias (candidatas a analise).
Uso: python concordancia_auto_humano.py --humano ../avaliacoes/decisao_humana.csv
"""
import argparse, csv
from pathlib import Path

def norm(v):
    return "aprova" if str(v).strip().lower() in {"1", "aprova", "aprovado", "sim", "true"} else "reprova"

ap = argparse.ArgumentParser()
ap.add_argument("--f1", default=str(Path(__file__).resolve().parent / "resultados_f1.csv"))
ap.add_argument("--humano", required=True)
ap.add_argument("--saida", default=str(Path(__file__).resolve().parent / "tabela_auto_humano.csv"))
a = ap.parse_args()

f1 = {(r["caso"], r["versao"]): r for r in csv.DictReader(open(a.f1, encoding="utf-8-sig"))}
hum = {(r["caso"], r["versao"]): norm(r["aprovacao_humana"])
       for r in csv.DictReader(open(a.humano, encoding="utf-8-sig"))}
faltando = [k for k in f1 if k not in hum]
if faltando:
    raise SystemExit(f"Sem decisao humana para: {faltando}")

linhas, iguais = [], 0
for k, r in f1.items():
    ok = r["sinal_automatico"] == hum[k]
    iguais += ok
    linhas.append({"caso": k[0], "versao": k[1], "f1": r["f1"], "sinal_automatico": r["sinal_automatico"],
                   "decisao_humana": hum[k], "concorda": int(ok)})
with open(a.saida, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(linhas[0])); w.writeheader(); w.writerows(linhas)

print(f"Concordancia auto-humano: {iguais}/{len(linhas)}")
for v in ("A", "B"):
    h = sum(l["decisao_humana"] == "aprova" for l in linhas if l["versao"] == v)
    print(f"Aprovacao humana {v}: {h}/6")
for l in linhas:
    if not l["concorda"]:
        print(f"DIVERGENCIA {l['caso']}/{l['versao']}: F1={l['f1']} auto={l['sinal_automatico']} humano={l['decisao_humana']}")
