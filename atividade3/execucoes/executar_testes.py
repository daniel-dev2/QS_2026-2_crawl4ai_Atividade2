"""
Atividade 3 - Pessoa 4: execução dos 6 casos nas versões A e B (12 saídas brutas).

Uso (a partir da raiz do repo; precisa de: export OPENROUTER_API_KEY=sua_chave):
    python atividade3/execucoes/executar_testes.py            # roda A e B
    python atividade3/execucoes/executar_testes.py --versao A # só A
    python atividade3/execucoes/executar_testes.py --dry-run  # confere tudo sem chamar o LLM

O script sobe sozinho o servidor local das páginas (porta 8000).
Nada é descartado: falha, saída vazia ou JSON inválido são gravados como estão.
"""
import argparse, ast, asyncio, csv, functools, hashlib, http.server, json
import os, platform, socketserver, subprocess, threading
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent            # atividade3/execucoes
ATV3 = BASE.parent                                # atividade3
FONTES = ATV3 / "casos" / "fontes"
REFS = ATV3 / "casos" / "referencias.json"
PORTA = 8000


def _carregar_env():
    """Lê atividade3/.env (CHAVE=valor) sem sobrescrever variáveis já definidas."""
    f = Path(__file__).resolve().parent.parent / ".env"
    if f.exists():
        for linha in f.read_text(encoding="utf-8").splitlines():
            linha = linha.strip()
            if linha and not linha.startswith("#") and "=" in linha:
                k, v = linha.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_carregar_env()

# ---- Configuração IGUAL em A e B (só o prompt muda) ----
# Modelo via OpenRouter definido em .env (OPENROUTER_MODEL); o preflight confirma se existe
USAR_OLLAMA = os.environ.get("LLM_PROVIDER", "openrouter").lower() == "ollama"
if USAR_OLLAMA:   # Qwen2.5-7B rodando no Ollama (ex.: Google Colab)
    MODELO = "ollama/" + os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")
else:             # OpenRouter
    MODELO = "openrouter/" + os.environ.get("OPENROUTER_MODEL", "qwen/qwen3.8-27b:free")
TEMPERATURE = 0
EXTRA_ARGS = {"temperature": TEMPERATURE}
PAUSA_ENTRE_CHAMADAS_S = 5       # o tier gratuito tem limite de requisições por minuto
CHUNK_TOKEN_THRESHOLD = 1000
APPLY_CHUNKING = True
WORD_COUNT_THRESHOLD = 10


def prompt_da_versao(versao: str) -> tuple[str, str]:
    """Lê o prompt direto do extracao_g1.py da versão (sem importar crawl4ai)."""
    src = (ATV3 / "versoes" / versao / "extracao_g1.py").read_text(encoding="utf-8")
    nome = "PROMPT_P1" if versao == "A" else "PROMPT_P2"
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and node.targets[0].id == nome:
            return nome, ast.literal_eval(node.value)
    raise RuntimeError(f"{nome} não encontrado em versoes/{versao}/extracao_g1.py")


def sha(txt: str) -> str:
    return hashlib.sha256(txt.encode("utf-8")).hexdigest()[:16]


def subir_servidor():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(FONTES))
    handler.log_message = lambda *a, **k: None
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("localhost", PORTA), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def _ollama_list():
    try:
        return subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=15).stdout.strip()
    except Exception as e:
        return f"indisponível ({e})"


def info_ambiente() -> dict:
    def cmd(c):
        try:
            return subprocess.run(c, capture_output=True, text=True, timeout=15).stdout.strip()
        except Exception as e:
            return f"indisponível ({e})"
    try:
        from importlib.metadata import version
        c4 = str(version("crawl4ai"))
    except Exception:
        c4 = "não instalado"
    return {"python": platform.python_version(), "so": platform.platform(),
            "crawl4ai": c4, "modelo": MODELO, "data_bateria": datetime.now().isoformat(timespec="seconds"),
            "provedor": "ollama" if USAR_OLLAMA else "openrouter",
            "ollama_list": (_ollama_list() if USAR_OLLAMA else None),
            "nota": ("modelo local no Ollama; digest em ollama_list" if USAR_OLLAMA
                     else "modelo servido via API; provedor/revisão não congelável")}


async def executar_um(versao, caso, prompt_nome, prompt, dry):
    from_dir = BASE / versao / caso["id"]
    from_dir.mkdir(parents=True, exist_ok=True)
    url = caso["url"]
    reg = {
        "versao": versao, "caso": caso["id"], "tipo": caso["tipo"], "url": url,
        "fonte_html": caso["fonte"], "prompt_id": prompt_nome, "prompt_sha": sha(prompt),
        "modelo": MODELO, "temperature": TEMPERATURE, "extra_args": EXTRA_ARGS,
        "apply_chunking": APPLY_CHUNKING, "chunk_token_threshold": CHUNK_TOKEN_THRESHOLD,
        "word_count_threshold": WORD_COUNT_THRESHOLD, "cache_mode": "BYPASS",
        "inicio": datetime.now().isoformat(timespec="seconds"),
        "crawl_success": False, "erro": None, "saida_vazia": True,
        "json_valido": False, "duracao_s": None,
    }
    t0 = datetime.now()
    bruta, contexto = "", ""
    if dry:
        reg["erro"] = "dry-run (LLM não chamado)"
    else:
        try:
            from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, LLMConfig
            from crawl4ai.extraction_strategy import LLMExtractionStrategy
            import sys
            sys.path.insert(0, str(ATV3 / "versoes" / versao / "3_EsquemaJsonEValidador"))
            from schema import PageExtractionSchema
            estrategia = LLMExtractionStrategy(
                llm_config=LLMConfig(provider=MODELO, api_token=os.environ.get("OPENROUTER_API_KEY", "no-token")),
                schema=PageExtractionSchema.model_json_schema(),
                extraction_type="schema", instruction=prompt, verbose=False,
                apply_chunking=APPLY_CHUNKING, chunk_token_threshold=CHUNK_TOKEN_THRESHOLD,
                extra_args=EXTRA_ARGS)
            cfg = CrawlerRunConfig(extraction_strategy=estrategia, cache_mode=CacheMode.BYPASS,
                                   word_count_threshold=WORD_COUNT_THRESHOLD)
            async with AsyncWebCrawler() as crawler:
                r = await crawler.arun(url=url, config=cfg)
            reg["crawl_success"] = bool(r.success)
            if not r.success:
                reg["erro"] = f"falha no crawl: {r.error_message}"
            bruta = r.extracted_content or ""
            md = r.markdown
            contexto = str(md.raw_markdown if hasattr(md, "raw_markdown") else (md or ""))
        except Exception as e:                       # registra e segue, não aborta a bateria
            reg["erro"] = f"exceção: {type(e).__name__}: {e}"
    reg["duracao_s"] = round((datetime.now() - t0).total_seconds(), 1)
    reg["saida_vazia"] = not bruta.strip()
    reg["chunk_com_erro_llm"] = '"error": true' in bruta.lower().replace('"error":true','"error": true')
    if reg["chunk_com_erro_llm"]:
        try:
            msg = json.loads(bruta)[0].get("content", "")
        except Exception:
            msg = "chunk com error=true"
        reg["erro"] = f"LLM retornou erro: {str(msg)[:300]}"
    if bruta.strip():
        try:
            json.loads(bruta); reg["json_valido"] = True
        except json.JSONDecodeError as e:
            reg["erro"] = (reg["erro"] or "") + f" | JSON inválido: {e}"
    if reg["saida_vazia"] and not reg["erro"]:
        reg["erro"] = "crawl OK mas saída vazia"
    reg["saida_sha"] = sha(bruta)
    reg["contexto_chars"] = len(contexto)

    (from_dir / "saida_bruta.json").write_text(bruta, encoding="utf-8")
    (from_dir / "contexto_enviado_ao_llm.md").write_text(contexto, encoding="utf-8")
    (from_dir / "registro.json").write_text(json.dumps(reg, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[{versao}/{caso['id']}] ok={reg['crawl_success']} vazia={reg['saida_vazia']} "
          f"json={reg['json_valido']} {reg['duracao_s']}s" + (f"  ERRO: {reg['erro']}" if reg["erro"] else ""))
    return reg


def preflight():
    """Confirma chave/modelo antes da bateria (OpenRouter: 1 chamada mínima; Ollama: modelo instalado)."""
    import urllib.request, urllib.error
    if USAR_OLLAMA:
        nome = MODELO.replace("ollama/", "", 1)
        try:
            tags = json.loads(urllib.request.urlopen("http://localhost:11434/api/tags", timeout=15).read())
        except Exception as e:
            raise SystemExit(f"Ollama não está respondendo em localhost:11434: {e}")
        if not any(m.get("name", "").startswith(nome) for m in tags.get("models", [])):
            raise SystemExit(f"Modelo {nome} não instalado no Ollama. Rode: ollama pull {nome}")
        print(f"Preflight OK (Ollama): {nome}")
        return
    modelo = MODELO.replace("openrouter/", "", 1)
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps({"model": modelo, "max_tokens": 5, "temperature": 0,
                         "messages": [{"role": "user", "content": "Responda: ok"}]}).encode(),
        headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
                 "Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=60).read()
        print(f"Preflight OK: {modelo}")
    except urllib.error.HTTPError as e:
        corpo = e.read().decode("utf-8", "replace")[:400]
        raise SystemExit(f"Preflight FALHOU (HTTP {e.code}) para {modelo}:\n{corpo}\n"
                         "Troque OPENROUTER_MODEL no arquivo .env e rode de novo. Nada foi executado.")
    except Exception as e:
        raise SystemExit(f"Preflight FALHOU: {e}")


def arquivar_anteriores(versoes):
    """Nunca sobrescreve execuções antigas: move para execucoes/_tentativas_anteriores/<data>/."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    for v in versoes:
        d = BASE / v
        if d.exists() and any(d.iterdir()):
            dest = BASE / "_tentativas_anteriores" / ts
            dest.mkdir(parents=True, exist_ok=True)
            d.rename(dest / v)
            print(f"Execução anterior de {v} arquivada em {dest / v}")


def consolidar_csv(nome_csv):
    regs = []
    for v in ("A", "B"):
        for c in sorted((BASE / v).glob("CT*/registro.json")):
            regs.append(json.loads(c.read_text(encoding="utf-8")))
    if not regs:
        return
    campos = []
    for r in regs:
        for k in r:
            if k not in campos:
                campos.append(k)
    out = BASE / nome_csv
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for r in regs:
            w.writerow({k: json.dumps(r.get(k), ensure_ascii=False) if isinstance(r.get(k), dict) else r.get(k) for k in campos})
    print(f"\nRegistro consolidado ({len(regs)} execuções): {out}")


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--versao", choices=["A", "B"])
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if not USAR_OLLAMA and not a.dry_run and not os.environ.get("OPENROUTER_API_KEY"):
        raise SystemExit("Defina OPENROUTER_API_KEY (export OPENROUTER_API_KEY=...) antes de rodar.")
    casos = json.loads(REFS.read_text(encoding="utf-8"))
    versoes = [a.versao] if a.versao else ["A", "B"]
    if not a.dry_run:
        preflight()
        arquivar_anteriores(versoes)
    srv = subir_servidor()
    print(f"Servidor das fontes em http://localhost:{PORTA} ({FONTES})")
    (BASE / "ambiente.json").write_text(json.dumps(info_ambiente(), indent=2, ensure_ascii=False), encoding="utf-8")
    regs = []
    try:
        for v in versoes:
            nome, prompt = prompt_da_versao(v)
            for c in casos:
                r = await executar_um(v, c, nome, prompt, a.dry_run)
                regs.append(r)
                if r.get("erro") and any(t in r["erro"] for t in ("NotFoundError", "AuthenticationError", "no longer available")):
                    print("\nERRO de modelo/chave: bateria interrompida. Corrija o .env e rode de novo.")
                    raise SystemExit(1)
                if not a.dry_run:
                    await asyncio.sleep(PAUSA_ENTRE_CHAMADAS_S)
    finally:
        srv.shutdown()
        if regs and not a.dry_run:
            consolidar_csv("registro_execucoes.csv")


if __name__ == "__main__":
    asyncio.run(main())
