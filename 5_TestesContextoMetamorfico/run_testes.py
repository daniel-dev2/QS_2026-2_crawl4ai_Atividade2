#!/usr/bin/env python3
"""
Executor dos testes de contexto e metamórficos (AV2 · Qualidade de Software).

Usa SEM ALTERAÇÃO:
  - ../3_EsquemaJsonEValidador/schema.py e validator.py  (Pessoa 3)
  - ../prompts/p1.txt, p2.txt, p3.txt                    (prompts do grupo)

Modos:
  --modo offline   Usa amostras fictícias de amostras_offline/. Não precisa de LLM nem de rede.
                   Serve só para conferir se tudo está instalado. NÃO é evidência.
  --modo online    Sobe um servidor local com as páginas de fixtures/, roda o Crawl4AI
                   (extração com LLM) e avalia os resultados.

Saída: resultados/<data-hora>_<modo>_<prompt>/ com evidencias.csv, resumo.md, saidas/ e quarantine/.
"""

import argparse
import asyncio
import csv
import functools
import hashlib
import http.server
import json
import sys
import threading
import time
import unicodedata
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
REPO = BASE.parent
sys.path.insert(0, str(REPO / "3_EsquemaJsonEValidador"))

from validator import DataQualityValidator  # noqa: E402  (Pessoa 3)

PASSOU, FALHOU, REVISAR = "PASSOU", "FALHOU", "REVISAR"


# ------------------------------------------------------------------ utilidades
def norm(v) -> str:
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        v = " ".join(str(x) for x in v)
    t = unicodedata.normalize("NFKD", str(v).lower())
    return "".join(c for c in t if not unicodedata.combining(c)).strip()


def extrair_bloco(texto_bruto):
    """O Crawl4AI devolve uma LISTA de blocos; cada um tem a chave 'error'.
    Pega o primeiro bloco sem erro e remove 'error' (não faz parte do esquema)."""
    if texto_bruto is None or texto_bruto == "null":
        return None, "sem conteúdo extraído"
    try:
        parsed = json.loads(texto_bruto)
    except json.JSONDecodeError as e:
        return None, f"JSON malformado: {e}"
    if isinstance(parsed, dict):
        parsed = [parsed]
    if not isinstance(parsed, list):
        return None, "resposta não é lista nem objeto JSON"
    validos = [b for b in parsed if isinstance(b, dict) and not b.get("error")]
    if not validos:
        return None, "todos os blocos vieram com error=true"
    return {k: v for k, v in validos[0].items() if k != "error"}, f"{len(parsed)} bloco(s) devolvido(s)"


def carregar_prompt(nome: str) -> str:
    for pasta in (REPO / "prompts", BASE / "prompts_extras"):
        f = pasta / f"{nome}.txt"
        if f.exists():
            return f.read_text(encoding="utf-8")
    raise FileNotFoundError(f"Prompt '{nome}.txt' não encontrado em prompts/ nem em prompts_extras/")


# ------------------------------------------------------------------- avaliação
def avaliar(item, bloco, qa_valido, config):
    """Checagens semânticas além do esquema. Retorna (status, problemas, revisoes)."""
    ch = item["checagens"]
    problemas, revisoes = [], []

    if bloco is None:
        if ch.get("aceita_sem_saida"):
            return REVISAR, [], ["sem saída do Crawl4AI/LLM: falha controlada. Documentar no relatório "
                                 "(o sistema avisou o erro? não inventou dados?)"]
        return FALHOU, ["sem saída utilizável"], []

    if ch.get("nao_deve_ter_registro_valido") and qa_valido:
        problemas.append("gerou um registro VÁLIDO a partir de página vazia (possível alucinação)")

    titulo = bloco.get("titulo") or ""
    url = bloco.get("url") or ""
    conteudo = bloco.get("conteudo") or ""
    links = bloco.get("links") if isinstance(bloco.get("links"), list) else []
    links_txt = " ".join(str(x) for x in links)

    for s in ch.get("titulo_contem", []):
        if norm(s) not in norm(titulo):
            problemas.append(f"titulo deveria conter '{s}' (obtido: {titulo!r})")
    for s in ch.get("titulo_nao_contem", []):
        if norm(s) in norm(titulo):
            problemas.append(f"titulo NÃO deveria conter '{s}' (contaminação de contexto)")
    for s in ch.get("url_contem", []):
        if norm(s) not in norm(url):
            problemas.append(f"url deveria conter '{s}' (obtido: {url!r}); possível URL inventada/copiada de exemplo")
    for s in ch.get("conteudo_contem", []):
        if norm(s) not in norm(conteudo):
            problemas.append(f"conteudo deveria conter '{s}' (resumiu ou perdeu informação?)")
    for s in ch.get("conteudo_nao_contem", []):
        if norm(s) in norm(conteudo):
            problemas.append(f"conteudo NÃO deveria conter '{s}' (dado inventado/contaminação)")
    for s in ch.get("conteudo_revisar_se_contem", []):
        if norm(s) in norm(conteudo):
            revisoes.append(f"conteudo incluiu texto de ruído ('{s}'): avaliar contaminação")
    for s in ch.get("links_contem", []):
        if norm(s) not in norm(links_txt):
            problemas.append(f"links deveria conter '{s}'")
    for s in ch.get("links_nao_contem", []):
        if norm(s) in norm(links_txt):
            problemas.append(f"links NÃO deveria conter '{s}' (contaminação por ruído)")

    if "datas_conflito" in ch:
        a, b = ch["datas_conflito"]
        tem_a, tem_b = norm(a) in norm(conteudo), norm(b) in norm(conteudo)
        if not (tem_a and tem_b):
            revisoes.append(f"conflito de datas: conteudo só traz {'a primeira' if tem_a else 'a segunda' if tem_b else 'nenhuma'} "
                            f"({a}/{b}). Escolha silenciosa?")

    if ch.get("regra_nao_noticia_p2") and item["prompt_nome"] == "p2":
        frase = config["frase_regra_nao_noticia_p2"]
        if norm(frase) not in norm(conteudo):
            revisoes.append(f"o P2 manda escrever '{frase}' quando a página não é notícia, mas o modelo não seguiu "
                            "a regra (instrução condicional ignorada)")

    if not qa_valido:
        return FALHOU, problemas, revisoes  # os erros do QA são adicionados fora
    if problemas:
        return FALHOU, problemas, revisoes
    if revisoes:
        return REVISAR, problemas, revisoes
    return PASSOU, problemas, revisoes


# ------------------------------------------------------------- servidor local
def subir_servidor(porta):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(BASE / "fixtures"))
    handler.log_message = lambda *a, **k: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", porta), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


# --------------------------------------------------------------------- online
def _arq(pasta, item, ext):
    return pasta / "saidas" / f"{item['id']}_rep{item['rep']}{ext}"


async def executar_online(plano, args, pasta):
    """Roda o Crawl4AI para os itens que ainda não têm saída gravada (permite --retomar)."""
    pendentes = [i for i in plano if not _arq(pasta, i, ".json").exists()]
    if not pendentes:
        return
    from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig, LLMConfig, LLMExtractionStrategy
    from schema import PageExtractionSchema  # Pessoa 3

    schema_dict = PageExtractionSchema.model_json_schema()
    async with AsyncWebCrawler() as crawler:
        for n, item in enumerate(pendentes, 1):
            estrategia = LLMExtractionStrategy(
                llm_config=LLMConfig(provider=args.provider, api_token=args.token, base_url=args.base_url),
                schema=schema_dict,
                extraction_type="schema",
                instruction=item["instrucao_texto"],
                apply_chunking=False,
            )
            cfg = CrawlerRunConfig(extraction_strategy=estrategia, cache_mode=CacheMode.BYPASS, word_count_threshold=10)
            t0 = time.time()
            try:
                r = await crawler.arun(url=item["url"], config=cfg)
                bruto = r.extracted_content
                erro = None if r.success else (r.error_message or "falha no crawl")
            except Exception as e:  # noqa: BLE001
                bruto, erro = None, f"exceção: {e}"
            lat = round(time.time() - t0, 2)
            # grava NA HORA: se o Colab cair, o que já rodou não se perde
            _arq(pasta, item, ".json").write_text(bruto if bruto else "null", encoding="utf-8")
            _arq(pasta, item, ".meta.json").write_text(
                json.dumps({"latencia_s": lat, "erro_crawl": erro}, ensure_ascii=False), encoding="utf-8")
            print(f"  [{n}/{len(pendentes)}] {item['id']} rep{item['rep']} ({item['prompt_nome']}): {lat}s"
                  + (f"  ! {erro}" if erro else ""), flush=True)


def carregar_offline(plano, pasta):
    for item in plano:
        amostra = BASE / "amostras_offline" / f"{item['id']}.json"
        _arq(pasta, item, ".json").write_text(amostra.read_text(encoding="utf-8") if amostra.exists() else "null",
                                              encoding="utf-8")
        _arq(pasta, item, ".meta.json").write_text(json.dumps({"latencia_s": 0.0, "erro_crawl": None}), encoding="utf-8")


# ------------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--modo", choices=["offline", "online"], default="offline")
    ap.add_argument("--prompt", choices=["p1", "p2", "p3"], default="p2", help="prompt do grupo usado nos casos '@SELECIONADO'")
    ap.add_argument("--repeticoes", type=int, default=1, help="repetições por variante (use 3 no teste real)")
    ap.add_argument("--provider", default="ollama/qwen3:4b")
    ap.add_argument("--token", default="no-token")
    ap.add_argument("--base-url", default=None, help="ex.: http://localhost:11434")
    ap.add_argument("--sufixo", default="", help="texto adicionado ao fim de toda instrução. Qwen3: '/no_think'")
    ap.add_argument("--casos", default=None, help="filtrar por id de caso ou variante, ex.: CT-CTX-01,CT-MET-02b")
    ap.add_argument("--retomar", default=None, help="pasta de resultados existente para continuar uma execução interrompida")
    args = ap.parse_args()

    config = json.loads((BASE / "casos_teste.json").read_text(encoding="utf-8"))
    porta = config["porta_servidor_local"]
    filtro = set(args.casos.split(",")) if args.casos else None

    # ---- plano de execução
    plano = []
    for caso in config["casos"]:
        for v in caso["variantes"]:
            if filtro and caso["id"] not in filtro and v["id"] not in filtro:
                continue
            if v.get("somente_com_prompt") and v["somente_com_prompt"] != args.prompt:
                continue  # variantes derivadas do P2 só rodam na execução do P2
            nome = args.prompt if v["prompt"] == "@SELECIONADO" else v["prompt"]
            texto = carregar_prompt(nome)
            if args.sufixo:
                texto = texto.rstrip() + "\n" + args.sufixo
            for rep in range(1, args.repeticoes + 1):
                plano.append(dict(caso_id=caso["id"], tipo=caso["tipo"], id=v["id"], descricao=v["descricao"],
                                  pagina=v["pagina"], url=f"http://localhost:{porta}/{v['pagina']}",
                                  prompt_nome=nome, instrucao_texto=texto, rep=rep, checagens=v["checagens"]))
    if not plano:
        sys.exit("Nenhum caso selecionado. Confira --casos.")

    # ---- pasta de saída
    if args.retomar:
        pasta = Path(args.retomar)
        if not pasta.is_absolute():
            pasta = BASE / pasta
        if not (pasta / "saidas").exists():
            sys.exit(f"Pasta para retomar não encontrada: {pasta}")
    else:
        pasta = BASE / "resultados" / f"{datetime.now():%Y%m%d-%H%M%S}_{args.modo}_{args.prompt}"
        (pasta / "saidas").mkdir(parents=True)

    # ---- execução
    modelo = args.provider if args.modo == "online" else "OFFLINE-AMOSTRA"
    if args.modo == "online":
        print(f"Modo ONLINE | modelo {args.provider} | prompt {args.prompt} | {len(plano)} execuções | pasta {pasta.name}")
        srv = subir_servidor(porta)
        print(f"Servidor local de páginas em http://localhost:{porta}")
        try:
            asyncio.run(executar_online(plano, args, pasta))
        finally:
            srv.shutdown()
    else:
        print("Modo OFFLINE: amostras FICTÍCIAS (não é evidência real)")
        carregar_offline(plano, pasta)

    # ---- validação (Pessoa 3) + avaliação semântica
    qa = DataQualityValidator(quarantine_dir=str(pasta / "quarantine"), auto_sanitize=True)
    for r in plano:
        bruto = _arq(pasta, r, ".json").read_text(encoding="utf-8")
        meta = json.loads(_arq(pasta, r, ".meta.json").read_text(encoding="utf-8")) \
            if _arq(pasta, r, ".meta.json").exists() else {}
        r["latencia"], r["erro_crawl"] = meta.get("latencia_s", ""), meta.get("erro_crawl")
        r["bloco"], r["info_bloco"] = extrair_bloco(bruto)
        if r["bloco"] is not None:
            vr = qa.validate(r["bloco"])
            r["qa_valido"], r["qa_erros"], r["quarentena"] = vr.is_valid, list(vr.errors), vr.quarantine_path
        else:
            r["qa_valido"], r["quarentena"] = False, None
            r["qa_erros"] = [r["erro_crawl"] or r["info_bloco"]]
        r["status"], r["problemas"], r["revisoes"] = avaliar(r, r["bloco"], r["qa_valido"], config)
        if r["bloco"] is not None and not r["qa_valido"]:
            r["problemas"] = [f"[QA-GATE P3] {e}" for e in r["qa_erros"]] + r["problemas"]
        r["hash_saida"] = hashlib.md5(json.dumps(r["bloco"], sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:8]
        r["arquivo"] = str(_arq(pasta, r, ".json").relative_to(BASE))

    # ---- estabilidade entre repetições
    estab = {}
    for r in plano:
        estab.setdefault((r["id"], r["prompt_nome"]), set()).add(r["hash_saida"])

    # ---- CSV de evidências
    cols = ["id_caso", "id_variante", "tipo", "pagina", "prompt", "modelo", "repeticao", "latencia_s",
            "qa_valido", "esperado", "observado_titulo", "observado_url", "observado_conteudo_chars",
            "problemas", "revisoes", "status", "hash_saida", "categoria_falha", "severidade", "veredito_final", "justificativa",
            "quarentena", "arquivo_evidencia"]
    with open(pasta / "evidencias.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in plano:
            b = r["bloco"] or {}
            w.writerow({
                "id_caso": r["caso_id"], "id_variante": r["id"], "tipo": r["tipo"], "pagina": r["pagina"],
                "prompt": r["prompt_nome"], "modelo": modelo, "repeticao": r["rep"], "latencia_s": r["latencia"],
                "qa_valido": "sim" if r["qa_valido"] else "não", "esperado": r["descricao"],
                "observado_titulo": b.get("titulo", ""), "observado_url": b.get("url", ""),
                "observado_conteudo_chars": len(str(b.get("conteudo") or "").strip()),
                "problemas": " | ".join(r["problemas"]), "revisoes": " | ".join(r["revisoes"]),
                "status": r["status"], "hash_saida": r["hash_saida"], "categoria_falha": "", "severidade": "", "veredito_final": "", "justificativa": "",
                "quarentena": r["quarentena"] or "", "arquivo_evidencia": r["arquivo"],
            })

    # ---- resumo
    total = len(plano)
    cont = lambda s: sum(1 for r in plano if r["status"] == s)  # noqa: E731
    validos = sum(1 for r in plano if r["qa_valido"])
    L = ["# Resumo dos testes de contexto e metamórficos", "",
         f"- Modo **{args.modo}** | prompt **{args.prompt}** | repetições {args.repeticoes} | modelo {modelo} | sufixo {args.sufixo or '-'}",
         "", "| Variante | Prompt | Rep | QA Gate (P3) | Status | Observação |", "|---|---|---|---|---|---|"]
    for r in plano:
        obs = (r["problemas"] + r["revisoes"] or [""])[0][:90]
        L.append(f"| {r['id']} | {r['prompt_nome']} | {r['rep']} | {'✅' if r['qa_valido'] else '❌'} | {r['status']} | {obs} |")
    if args.repeticoes > 1:
        L += ["", "## Estabilidade entre repetições", ""]
        for (vid, pn), conj in estab.items():
            L.append(f"- {vid} ({pn}): " + ("estável (todas iguais)" if len(conj) == 1 else f"INSTÁVEL ({len(conj)} saídas diferentes)"))
    L += ["", "## Métricas", "",
          f"- Execuções: {total} | PASSOU {cont(PASSOU)} | FALHOU {cont(FALHOU)} | REVISAR {cont(REVISAR)}",
          f"- Saídas válidas no QA Gate da Pessoa 3: {validos}/{total} ({100 * validos // total}%)", "",
          "> Preencha `categoria_falha` (dados/contexto, prompt, factualidade, rastreabilidade, formato, segurança, "
          "confiabilidade, usabilidade) e `severidade` (baixa, média, alta, crítica) no evidencias.csv para as linhas FALHOU e REVISAR."]
    (pasta / "resumo.md").write_text("\n".join(L), encoding="utf-8")
    print("\n" + "\n".join(L))
    print(f"\nEvidências em: {pasta.relative_to(BASE)}/")


if __name__ == "__main__":
    main()
