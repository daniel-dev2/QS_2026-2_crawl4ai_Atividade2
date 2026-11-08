# Resumo dos testes de contexto e metamórficos

- Modo **online** | prompt **p2** | repetições 3 | modelo ollama/qwen3:4b | sufixo /no_think

| Variante | Prompt | Rep | QA Gate (P3) | Status | Observação |
|---|---|---|---|---|---|
| CT-CTX-01a | p2 | 1 | ✅ | PASSOU |  |
| CT-CTX-01a | p2 | 2 | ✅ | PASSOU |  |
| CT-CTX-01a | p2 | 3 | ❌ | FALHOU | sem saída utilizável |
| CT-CTX-01b | p2 | 1 | ❌ | FALHOU | [QA-GATE P3] Campo 'titulo': Value error, O campo 'titulo' deve ser do tipo string, recebi |
| CT-CTX-01b | p2 | 2 | ✅ | PASSOU |  |
| CT-CTX-01b | p2 | 3 | ✅ | PASSOU |  |
| CT-CTX-01c | p2 | 1 | ❌ | REVISAR | sem saída do Crawl4AI/LLM: falha controlada. Documentar no relatório (o sistema avisou o e |
| CT-CTX-01c | p2 | 2 | ❌ | REVISAR | sem saída do Crawl4AI/LLM: falha controlada. Documentar no relatório (o sistema avisou o e |
| CT-CTX-01c | p2 | 3 | ❌ | REVISAR | sem saída do Crawl4AI/LLM: falha controlada. Documentar no relatório (o sistema avisou o e |
| CT-CTX-02a | p2 | 1 | ✅ | PASSOU |  |
| CT-CTX-02a | p2 | 2 | ❌ | FALHOU | [QA-GATE P3] Campo 'titulo': Field required |
| CT-CTX-02a | p2 | 3 | ✅ | PASSOU |  |
| CT-MET-01a | p2 | 1 | ❌ | FALHOU | [QA-GATE P3] Campo 'url': Field required |
| CT-MET-01a | p2 | 2 | ❌ | FALHOU | [QA-GATE P3] Campo 'url': Field required |
| CT-MET-01a | p2 | 3 | ✅ | FALHOU | links deveria conter 'educacao.html' |
| CT-MET-02b | met02_parafrase_pt | 1 | ❌ | FALHOU | [QA-GATE P3] Campo 'url': Field required |
| CT-MET-02b | met02_parafrase_pt | 2 | ❌ | FALHOU | [QA-GATE P3] Campo 'titulo': Field required |
| CT-MET-02b | met02_parafrase_pt | 3 | ✅ | PASSOU |  |
| CT-MET-02c | met02_en | 1 | ❌ | FALHOU | [QA-GATE P3] Campo 'url': Field required |
| CT-MET-02c | met02_en | 2 | ❌ | FALHOU | [QA-GATE P3] Campo 'url': Field required |
| CT-MET-02c | met02_en | 3 | ❌ | FALHOU | [QA-GATE P3] Campo 'url': Field required |

## Estabilidade entre repetições

- CT-CTX-01a (p2): INSTÁVEL (2 saídas diferentes)
- CT-CTX-01b (p2): INSTÁVEL (3 saídas diferentes)
- CT-CTX-01c (p2): estável (todas iguais)
- CT-CTX-02a (p2): INSTÁVEL (3 saídas diferentes)
- CT-MET-01a (p2): INSTÁVEL (3 saídas diferentes)
- CT-MET-02b (met02_parafrase_pt): INSTÁVEL (3 saídas diferentes)
- CT-MET-02c (met02_en): INSTÁVEL (3 saídas diferentes)

## Métricas

- Execuções: 21 | PASSOU 7 | FALHOU 11 | REVISAR 3
- Saídas válidas no QA Gate da Pessoa 3: 8/21 (38%)

## Veredito final (após revisão manual)

- PASSOU 10 | FALHOU 11 (as linhas REVISAR foram decididas; justificativa por linha no `evidencias.csv`)
- Classificação das ocorrências (categoria · severidade): confiabilidade · alta = 1; dados/contexto · alta = 2; dados/contexto · média = 1; factualidade · média = 2; formato · média = 4; prompt · média = 1; usabilidade · baixa = 3
