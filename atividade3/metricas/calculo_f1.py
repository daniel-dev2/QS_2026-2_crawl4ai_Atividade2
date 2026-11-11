#!/usr/bin/env python3
r"""
Atividade 3 - Qualidade de Software - Crawl4AI (Pessoa 5)
F1 lexical por tokens: saida gerada (A/B) x referencia humana.

Le direto da estrutura do repositorio:
  atividade3/casos/referencias.json
  atividade3/execucoes/<A|B>/<CTxx>/saida_bruta.json
Escreve:
  atividade3/metricas/resultados_f1.csv      (12 linhas)
  atividade3/metricas/resumo_f1.md           (tabela + medias por versao)

DEFINICOES FIXAS (registrar no relatorio ANTES de interpretar resultados)
-------------------------------------------------------------------------
Texto comparado (principal, "completo"):
  valores dos campos titulo, url, conteudo e links, nessa ordem, separados
  por espaco. Chaves do JSON e pontuacao sintatica ficam de fora; null vira
  vazio. Saida `[]` (vazia) -> texto vazio -> F1 = 0 (nao e descartada).
  Se a saida tiver mais de um objeto, os textos sao concatenados.
Texto comparado (sensibilidade, "texto"): apenas titulo + conteudo.
  Serve so para mostrar quanto url/links inflam o F1; o sinal oficial usa
  o "completo".
Normalizacao: Unicode NFC + casefold.
Tokenizacao: numeros com separador decimal/milhar (18,90 ; 1.000) viram um
  token; demais sequencias \w+ (8h, 17h, 10, ct01...). Sem remocao de
  acentos e sem remocao de markdown: [acervo](http://...) gera tokens.
Interseccao: multiconjunto (Counter &).
Formulas: P = comuns/tokens_resposta ; R = comuns/tokens_referencia ;
  F1 = 2PR/(P+R). Sem sobreposicao ou resposta vazia -> F1 = 0.
  Referencia sem tokens -> erro (corrigir o caso; nao inventar score).
Sinal automatico: aprova se F1 >= tau (tau = 0.50, fixado pela P1 antes
  da bateria; NAO ajustar depois).

Colunas diagnosticas (auxiliares; NAO substituem a rubrica humana):
  json_valido/saida_vazia vem de execucoes/registro_execucoes.csv;
  url_exata, links_iguais, titulo_nulo comparam com a referencia.

Uso (a partir de atividade3/metricas/):
  python calculo_f1.py            # usa tau 0.50
  python calculo_f1.py --tau 0.5 --raiz ..
"""
import argparse, csv, json, re, statistics, sys, unicodedata
from collections import Counter
from pathlib import Path

TOKEN_RE = re.compile(r"\d+(?:[.,]\d+)+|\w+", re.UNICODE)
CASOS = ["CT01", "CT02", "CT03", "CT04", "CT05", "CT06"]
VERSOES = ["A", "B"]


def tokenizar(texto):
    return TOKEN_RE.findall(unicodedata.normalize("NFC", texto or "").casefold())


def f1_lexical(resposta, referencia):
    tr, tf = tokenizar(resposta), tokenizar(referencia)
    if not tf:
        raise ValueError("Referencia sem tokens: corrigir o caso (nao inventar score).")
    comuns = sum((Counter(tr) & Counter(tf)).values())
    if not tr or comuns == 0:
        return dict(n_resp=len(tr), n_ref=len(tf), comuns=comuns, P=0.0, R=0.0, F1=0.0)
    p, r = comuns / len(tr), comuns / len(tf)
    return dict(n_resp=len(tr), n_ref=len(tf), comuns=comuns, P=p, R=r, F1=2 * p * r / (p + r))


def para_texto(obj, campos):
    partes = []
    for c in campos:
        v = obj.get(c)
        if v is None:
            continue
        partes.extend(str(x) for x in v) if isinstance(v, list) else partes.append(str(v))
    return " ".join(partes)


def carregar_saida(caminho):
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    if isinstance(dados, dict):
        dados = [dados]
    return [d for d in dados if isinstance(d, dict)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raiz", default=str(Path(__file__).resolve().parent.parent),
                    help="pasta atividade3/")
    ap.add_argument("--tau", type=float, default=0.50)
    ap.add_argument("--saida", default=None, help="pasta de saida (padrao: <raiz>/metricas)")
    a = ap.parse_args()
    raiz = Path(a.raiz)
    saida = Path(a.saida) if a.saida else raiz / "metricas"
    saida.mkdir(parents=True, exist_ok=True)

    refs = {r["id"]: r["referencia"] for r in json.loads(
        (raiz / "casos" / "referencias.json").read_text(encoding="utf-8"))}
    reg = {}
    f = raiz / "execucoes" / "registro_execucoes.csv"
    if f.exists():
        for r in csv.DictReader(open(f, encoding="utf-8-sig")):
            reg[(r["versao"], r["caso"])] = r

    COMPLETO = ["titulo", "url", "conteudo", "links"]
    TEXTO = ["titulo", "conteudo"]
    linhas = []
    for v in VERSOES:
        for c in CASOS:
            p = raiz / "execucoes" / v / c / "saida_bruta.json"
            if not p.exists():
                sys.exit(f"Faltando {p}")
            objs = carregar_saida(p)
            ref = refs[c]
            resp_c = " ".join(para_texto(o, COMPLETO) for o in objs)
            resp_t = " ".join(para_texto(o, TEXTO) for o in objs)
            m = f1_lexical(resp_c, para_texto(ref, COMPLETO))
            mt = f1_lexical(resp_t, para_texto(ref, TEXTO))
            o = objs[0] if objs else {}
            rg = reg.get((v, c), {})
            linhas.append({
                "caso": c, "versao": v,
                "n_objetos_saida": len(objs),
                "tokens_resposta": m["n_resp"], "tokens_referencia": m["n_ref"],
                "tokens_comuns": m["comuns"],
                "precisao": round(m["P"], 4), "recall": round(m["R"], 4),
                "f1": round(m["F1"], 4), "tau": a.tau,
                "sinal_automatico": "aprova" if m["F1"] >= a.tau else "reprova",
                "f1_texto_sensibilidade": round(mt["F1"], 4),
                "sinal_texto_sensibilidade": "aprova" if mt["F1"] >= a.tau else "reprova",
                "saida_vazia": int(not objs),
                "json_valido": rg.get("json_valido", ""),
                "url_exata": int(o.get("url") == ref["url"]) if objs else 0,
                "links_iguais": int(sorted(o.get("links") or []) == sorted(ref["links"])) if objs else 0,
                "titulo_nulo": int(objs != [] and o.get("titulo") is None),
                "saida_sha": rg.get("saida_sha", ""),
            })

    campos = list(linhas[0])
    with open(saida / "resultados_f1.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader(); w.writerows(linhas)

    md = [f"# Resultados F1 lexical (tau = {a.tau:.2f})\n",
          "| Caso | Ver. | Tok. resp. | Tok. ref. | Comuns | P | R | F1 | Sinal | F1 (so titulo+conteudo) |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for l in linhas:
        md.append(f"| {l['caso']} | {l['versao']} | {l['tokens_resposta']} | {l['tokens_referencia']} | "
                  f"{l['tokens_comuns']} | {l['precisao']:.3f} | {l['recall']:.3f} | {l['f1']:.3f} | "
                  f"{l['sinal_automatico']} | {l['f1_texto_sensibilidade']:.3f} |")
    md += ["", "| Versao | F1 medio | F1 mediana | Aprovados pelo sinal automatico |", "|---|---|---|---|"]
    for v in VERSOES:
        fs = [l["f1"] for l in linhas if l["versao"] == v]
        n = sum(l["sinal_automatico"] == "aprova" for l in linhas if l["versao"] == v)
        md.append(f"| {v} | {statistics.mean(fs):.3f} | {statistics.median(fs):.3f} | {n}/{len(fs)} |")
    (saida / "resumo_f1.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
