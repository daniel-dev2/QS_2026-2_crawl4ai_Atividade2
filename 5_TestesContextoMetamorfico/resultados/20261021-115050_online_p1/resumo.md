# Resumo dos testes de contexto e metamórficos

- Modo **online** | prompt **p1** | repetições 3 | modelo ollama/qwen3:4b | sufixo /no_think

| Variante | Prompt | Rep | QA Gate (P3) | Status | Observação |
|---|---|---|---|---|---|
| CT-CTX-01a | p1 | 1 | ✅ | PASSOU |  |
| CT-CTX-01a | p1 | 2 | ✅ | PASSOU |  |
| CT-CTX-01a | p1 | 3 | ❌ | FALHOU | [QA-GATE P3] Campo 'titulo': Field required |
| CT-CTX-01b | p1 | 1 | ✅ | PASSOU |  |
| CT-CTX-01b | p1 | 2 | ✅ | PASSOU |  |
| CT-CTX-01b | p1 | 3 | ✅ | PASSOU |  |
| CT-CTX-01c | p1 | 1 | ❌ | REVISAR | sem saída do Crawl4AI/LLM: falha controlada. Documentar no relatório (o sistema avisou o e |
| CT-CTX-01c | p1 | 2 | ❌ | REVISAR | sem saída do Crawl4AI/LLM: falha controlada. Documentar no relatório (o sistema avisou o e |
| CT-CTX-01c | p1 | 3 | ❌ | REVISAR | sem saída do Crawl4AI/LLM: falha controlada. Documentar no relatório (o sistema avisou o e |
| CT-CTX-02a | p1 | 1 | ✅ | PASSOU |  |
| CT-CTX-02a | p1 | 2 | ✅ | REVISAR | conflito de datas: conteudo só traz nenhuma (15/22). Escolha silenciosa? |
| CT-CTX-02a | p1 | 3 | ❌ | FALHOU | [QA-GATE P3] Campo 'titulo': Field required |
| CT-MET-01a | p1 | 1 | ❌ | FALHOU | [QA-GATE P3] Campo 'titulo': Field required |
| CT-MET-01a | p1 | 2 | ❌ | FALHOU | [QA-GATE P3] Campo 'titulo': Field required |
| CT-MET-01a | p1 | 3 | ❌ | FALHOU | sem saída utilizável |

## Estabilidade entre repetições

- CT-CTX-01a (p1): INSTÁVEL (3 saídas diferentes)
- CT-CTX-01b (p1): INSTÁVEL (3 saídas diferentes)
- CT-CTX-01c (p1): estável (todas iguais)
- CT-CTX-02a (p1): INSTÁVEL (3 saídas diferentes)
- CT-MET-01a (p1): INSTÁVEL (3 saídas diferentes)

## Métricas

- Execuções: 15 | PASSOU 6 | FALHOU 5 | REVISAR 4
- Saídas válidas no QA Gate da Pessoa 3: 7/15 (46%)

## Veredito final (após revisão manual)

- PASSOU 9 | FALHOU 6 (as linhas REVISAR foram decididas; justificativa por linha no `evidencias.csv`)
- Classificação das ocorrências (categoria · severidade): confiabilidade · média = 1; dados/contexto · média = 1; formato · alta = 1; formato · média = 3; usabilidade · baixa = 3
