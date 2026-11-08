# 5 · Testes de contexto e metamórficos

AV2 · Qualidade de Software · Crawl4AI · Missão C (Saída Estruturada Confiável)

Quatro casos de teste (7 variantes) com o Crawl4AI + `ollama/qwen3:4b`, usando os prompts do grupo (`../prompts/`) e o QA Gate da Pessoa 3 (`../3_EsquemaJsonEValidador/`).

## Conteúdo

| Item | O que é |
|---|---|
| `casos_teste.json` | Definição dos casos, páginas e checagens |
| `fixtures/` | 5 páginas HTML sintéticas (notícia fictícia "Vila Aurora") |
| `prompts_extras/` | Paráfrase em PT e versão em inglês (testes metamórficos) |
| `run_testes.py` | Executor dos testes |
| `consolidar.py` | Gera a tabela comparativa P1 × P2 × P3 |
| `amostras_offline/` | Saídas **fictícias** só para treino sem LLM (não são evidência) |
| `colab_testes_contexto.ipynb` | Notebook do Colab que roda tudo |
| `resultados/` | Evidências da execução real (21/10/2026), já classificadas |

## Casos

| Caso | Variante | Página | Verifica |
|---|---|---|---|
| CT-CTX-01 | 01a | `base.html` | Linha de base |
| | 01b | `irrelevante.html` | Conteúdo irrelevante: não inventar dados |
| | 01c | `vazia.html` | Conteúdo ausente: falha controlada |
| CT-CTX-02 | 02a | `conflitante.html` | Datas conflitantes (15 × 22 de novembro) |
| CT-MET-01 | 01a | `ruido.html` | Informação irrelevante adicionada |
| CT-MET-02 | 02b | `base.html` | Paráfrase em português (só com P2) |
| | 02c | `base.html` | Instrução em inglês (só com P2) |

## Resultados (`resultados/`)

- `consolidado.md` / `consolidado.csv`: comparação entre prompts.
- `<data>_online_p1|p2|p3/`: `evidencias.csv`, `resumo.md`, `saidas/` (JSON bruto), `quarantine/` (rejeitados pelo QA Gate).
- Modelo: `ollama/qwen3:4b` · sufixo `/no_think` · 3 repetições por variante.
- No `evidencias.csv`: `status` é o veredito automático; `categoria_falha`, `severidade`, `veredito_final` e `justificativa` são o resultado da revisão manual.

### Veredito final (47 execuções válidas, sem contar o treino offline)

| Prompt | Execuções | QA válido | PASSOU | FALHOU |
|---|---|---|---|---|
| P1 | 15 | 7 (46%) | 9 | 6 |
| P2 | 15 | 7 (46%) | 9 | 6 |
| P3 | 15 | 9 (60%) | 12 | 3 |
| P2 derivado (paráfrase PT) | 3 | 1 (33%) | 1 | 2 |
| P2 derivado (inglês) | 3 | 0 (0%) | 0 | 3 |

Falhas (20 no total, somando todos os prompts): formato 11, dados/contexto 4, confiabilidade 2, factualidade 2, prompt 1.

Decisão sobre as linhas REVISAR:
- **CT-CTX-01c (página vazia, 9 execuções) → PASSOU.** O Crawl4AI interrompeu antes do LLM e registrou o erro, sem fabricar dados. Observação (usabilidade, baixa): a mensagem fala em proteção anti-bot em vez de "página vazia".
- **CT-CTX-02a, P1 repetição 2 → FALHOU.** O QA Gate aprovou, mas as duas datas (15 e 22 de novembro) sumiram do conteúdo: o conflito foi perdido, nem preservado nem sinalizado.

## Como reproduzir

**Colab (recomendado, GPU T4):** envie o `colab_testes_contexto.ipynb`. A célula 3 pede um zip com a pasta `QS_testes/` (esta pasta + `prompts/` + `3_EsquemaJsonEValidador/`); para gerar, a partir da raiz do repositório:

```bash
mkdir QS_testes && cp -r prompts 3_EsquemaJsonEValidador 5_TestesContextoMetamorfico QS_testes/
zip -r QS_testes.zip QS_testes
```

**Local:**
```bash
pip install crawl4ai pydantic && crawl4ai-setup
ollama serve &  ollama pull qwen3:4b
cd 5_TestesContextoMetamorfico
python run_testes.py --modo offline            # treino sem LLM
python run_testes.py --modo online --provider ollama/qwen3:4b --base-url http://localhost:11434 \
    --prompt p2 --repeticoes 3 --sufixo "/no_think"
python consolidar.py
```

> O executor busca `../prompts/` e `../3_EsquemaJsonEValidador/`, então esta pasta deve ficar na **raiz do repositório**, ao lado delas.

## Limitações
LLM não determinístico (por isso 3 repetições); páginas sintéticas; resultados valem para o modelo e a versão do Crawl4AI usados.
