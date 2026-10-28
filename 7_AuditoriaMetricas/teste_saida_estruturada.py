"""
ST-01 - Teste de saída estruturada (Pessoa 7, em conjunto com a Pessoa 3).

Verifica se o QA Gate (DataQualityValidator) rejeita saídas inválidas e aceita as válidas:
JSON malformado, campo ausente, URL inválida, tipo incorreto, formatos reais vistos nos testes do grupo.

Como executar (a partir desta pasta):
    pip install pydantic
    python teste_saida_estruturada.py

Saídas em evidencias/: ST-01_resultados.csv, ST-01_resultados.json e quarantine/ (registros rejeitados).
"""
import csv
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE.parent / "3_EsquemaJsonEValidador"))

from validator import DataQualityValidator  # noqa: E402

EVID = BASE / "evidencias"
EVID.mkdir(exist_ok=True)

TEXTO = "A biblioteca municipal da Vila Aurora foi inaugurada neste sábado com 120 lugares."
VALIDO = {"titulo": "Biblioteca inaugurada", "url": "https://exemplo.org/biblioteca",
          "conteudo": TEXTO, "links": ["https://exemplo.org/educacao"]}

def sem(campo):
    d = dict(VALIDO); d.pop(campo); return d

def com(**kw):
    d = dict(VALIDO); d.update(kw); return d

# Formatos reais observados nas evidências do grupo (resultados/*.json e seção 5 da Pessoa 5)
BLOCO_TIMEOUT = [{"index": 0, "error": True, "tags": ["error"],
    "content": "litellm.APIConnectionError: OllamaException - litellm.Timeout: Connection timed out. Timeout passed=600.0"}]
PAGINA_404 = {"titulo": "Ops! página não encontrada", "url": "https://g1.globo.com/erro/",
    "conteudo": "O endereço abaixo não existe na globo.com https://g1.globo.com/erro/",
    "links": ["https://www.globo.com?utm_source=barraGCOM"]}

# (id, grupo, descrição, entrada, esperado: True=aceitar, False=rejeitar)
CASOS = [
    ("ST-01-C0", "Controle",        "Payload válido (dict)",                         VALIDO, True),
    ("ST-01-C0j","Controle",        "Payload válido (string JSON)",                  json.dumps(VALIDO), True),
    ("ST-01-A1", "JSON malformado", "JSON truncado",                                 json.dumps(VALIDO)[:-25], False),
    ("ST-01-A2", "JSON malformado", "String vazia",                                  "", False),
    ("ST-01-A3", "JSON malformado", "JSON dentro de cerca Markdown (```json)",       "```json\n" + json.dumps(VALIDO) + "\n```", False),
    ("ST-01-A4", "JSON malformado", "Texto livre antes do JSON",                     "Aqui está o JSON: " + json.dumps(VALIDO), False),
    ("ST-01-B1", "Campo ausente",   "Sem 'url'",                                     sem("url"), False),
    ("ST-01-B2", "Campo ausente",   "Sem 'titulo' e 'conteudo'",                     {"url": VALIDO["url"], "links": []}, False),
    ("ST-01-B3", "Campo ausente",   "Chaves em inglês (title/content), falha F1 da P5", {"title": "x", "url": VALIDO["url"], "content": TEXTO, "links": []}, False),
    ("ST-01-B4", "Campo ausente",   "titulo = null (conflito P2 x esquema, F6)",     com(titulo=None), False),
    ("ST-01-U1", "URL inválida",    "Protocolo inválido",                            com(url="protocolo_invalido://sem-host"), False),
    ("ST-01-U2", "URL inválida",    "Sem host",                                      com(url="https://"), False),
    ("ST-01-U3", "URL inválida",    "Protocolo ftp://",                              com(url="ftp://exemplo.org/arquivo"), False),
    ("ST-01-U4", "URL inválida",    "Link inválido dentro de 'links' (deve sanear)", com(links=["javascript:void(0)", "https://exemplo.org/ok"]), True),
    ("ST-01-T1", "Tipo incorreto",  "'links' como string em vez de lista",           com(links="https://exemplo.org"), False),
    ("ST-01-T2", "Tipo incorreto",  "'conteudo' numérico",                           com(conteudo=12345678901234567890), False),
    ("ST-01-R1", "Formato real",    "Lista de blocos de erro do Crawl4AI (timeout)", json.dumps(BLOCO_TIMEOUT), False),
    ("ST-01-R2", "Formato real",    "Array vazio [] (P1, página irrelevante)",       "[]", False),
    ("ST-01-S1", "Semântico",       "Página 404 do g1 (aceita como notícia?)",       PAGINA_404, False),
    ("ST-01-S2", "Semântico",       "Conteúdo trocado por frase de preenchimento",   com(conteudo="... (the rest of the string) ..."), False),
]

val = DataQualityValidator(quarantine_dir=EVID / "quarantine", auto_sanitize=True)
linhas = []
for cid, grupo, desc, entrada, esperado in CASOS:
    r = val.validate(entrada)
    ok = (r.is_valid == esperado)
    linhas.append({
        "id": cid, "grupo": grupo, "descricao": desc,
        "esperado": "aceitar" if esperado else "rejeitar",
        "observado": "aceitou" if r.is_valid else "rejeitou",
        "status": "PASSOU" if ok else "FALHOU",
        "campos_com_falha": "|".join(r.failed_fields),
        "mensagem": (r.errors[0] if r.errors else "")[:160],
    })

with open(EVID / "ST-01_resultados.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(linhas[0])); w.writeheader(); w.writerows(linhas)
(EVID / "ST-01_resultados.json").write_text(json.dumps(linhas, indent=2, ensure_ascii=False), encoding="utf-8")

total = len(linhas); passou = sum(l["status"] == "PASSOU" for l in linhas)
print(f"{'ID':<10}{'Esperado':<10}{'Observado':<11}{'Status':<8} Descrição")
for l in linhas:
    print(f"{l['id']:<10}{l['esperado']:<10}{l['observado']:<11}{l['status']:<8} {l['descricao']}")
print(f"\nResultado: {passou}/{total} sub-casos conforme o esperado ({passou/total:.0%}).")
