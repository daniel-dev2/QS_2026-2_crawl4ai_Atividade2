# Resumo dos testes de contexto e metamórficos

- Modo **online** | prompt **p3** | repetições 3 | modelo ollama/qwen3:4b | sufixo /no_think

| Variante | Prompt | Rep | QA Gate (P3) | Status | Observação |
|---|---|---|---|---|---|
| CT-CTX-01a | p3 | 1 | ✅ | PASSOU |  |
| CT-CTX-01a | p3 | 2 | ❌ | FALHOU | [QA-GATE P3] Campo 'titulo': Field required |
| CT-CTX-01a | p3 | 3 | ✅ | PASSOU |  |
| CT-CTX-01b | p3 | 1 | ✅ | PASSOU |  |
| CT-CTX-01b | p3 | 2 | ✅ | PASSOU |  |
| CT-CTX-01b | p3 | 3 | ✅ | PASSOU |  |
| CT-CTX-01c | p3 | 1 | ❌ | REVISAR | sem saída do Crawl4AI/LLM: falha controlada. Documentar no relatório (o sistema avisou o e |
| CT-CTX-01c | p3 | 2 | ❌ | REVISAR | sem saída do Crawl4AI/LLM: falha controlada. Documentar no relatório (o sistema avisou o e |
| CT-CTX-01c | p3 | 3 | ❌ | REVISAR | sem saída do Crawl4AI/LLM: falha controlada. Documentar no relatório (o sistema avisou o e |
| CT-CTX-02a | p3 | 1 | ✅ | PASSOU |  |
| CT-CTX-02a | p3 | 2 | ✅ | PASSOU |  |
| CT-CTX-02a | p3 | 3 | ✅ | PASSOU |  |
| CT-MET-01a | p3 | 1 | ✅ | PASSOU |  |
| CT-MET-01a | p3 | 2 | ❌ | FALHOU | [QA-GATE P3] Campo 'titulo': Field required |
| CT-MET-01a | p3 | 3 | ❌ | FALHOU | [QA-GATE P3] Campo 'titulo': Field required |

## Estabilidade entre repetições

- CT-CTX-01a (p3): INSTÁVEL (2 saídas diferentes)
- CT-CTX-01b (p3): estável (todas iguais)
- CT-CTX-01c (p3): estável (todas iguais)
- CT-CTX-02a (p3): estável (todas iguais)
- CT-MET-01a (p3): INSTÁVEL (3 saídas diferentes)

## Métricas

- Execuções: 15 | PASSOU 9 | FALHOU 3 | REVISAR 3
- Saídas válidas no QA Gate da Pessoa 3: 9/15 (60%)

## Veredito final (após revisão manual)

- PASSOU 12 | FALHOU 3 (as linhas REVISAR foram decididas; justificativa por linha no `evidencias.csv`)
- Classificação das ocorrências (categoria · severidade): formato · alta = 1; formato · média = 2; usabilidade · baixa = 3
