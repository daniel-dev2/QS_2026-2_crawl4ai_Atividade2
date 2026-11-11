# Métrica automática (F1 lexical) — Atividade 3 · Qualidade de Software · Crawl4AI

Pasta `atividade3/metricas/`, parte da **Pessoa 5**. Aqui fica tudo o que calcula e documenta o **sinal automático** do experimento: o F1 lexical entre cada saída gerada (versões A e B) e a referência humana, a classificação "aprova/reprova" com o limiar τ, e a concordância desse sinal com a decisão humana.

---

## 1. Em uma frase

Para cada uma das 12 saídas (6 casos × 2 versões) o script compara, palavra por palavra, o texto gerado com a referência escrita por uma pessoa, calcula precisão, recall e F1, e diz se o sinal automático "aprova" (F1 ≥ τ = 0,50) ou "reprova". Depois, a concordância com a decisão humana é medida em **iguais/12**.

## 2. Onde isto se encaixa no experimento (GQM)

| Elemento | Definição | Onde é produzido |
|---|---|---|
| **Q2** | O sinal automático representa a adequação da resposta? | esta pasta |
| **M2 — F1 lexical** | Escala [0,1], uma nota por saída (12 notas) | `calculo_f1.py` → `resultados_f1.csv` |
| **M3 — Concordância automático–humano** | Decisões iguais / 12 | `concordancia_auto_humano.py` → `tabela_auto_humano.csv` |
| M1 — Taxa de aprovação humana | Aprovadas / 6 por versão | Pessoas 6 e 7 (não é desta pasta) |

O GQM, o valor de τ e a regra de falha crítica foram definidos pela Pessoa 1 (seções 1.1 e 1.2 do relatório). Esta pasta só os **aplica**.

## 3. Estrutura esperada do repositório

O script lê os arquivos das outras pessoas **sem modificá-los**:

```
atividade3/
├── casos/
│   └── referencias.json            # Pessoa 2: referência humana de cada caso
├── execucoes/
│   ├── registro_execucoes.csv      # Pessoa 4: metadados de cada execução
│   ├── A/CT01..CT06/saida_bruta.json   # Pessoa 4: 6 saídas da versão A
│   └── B/CT01..CT06/saida_bruta.json   # Pessoa 4: 6 saídas da versão B
├── avaliacoes/
│   ├── avaliacao_humana_R1.xlsx    # Pessoa 6: R1 das 12 saídas
│   └── R2.csv                      # Pessoa 7: R2 de CT01 e CT05 (A e B); ajuste o caminho se o arquivo estiver em outra pasta (na branch da P7 ele se chama r2.csv)
└── metricas/                       # <- ESTA PASTA (Pessoa 5)
    ├── README.md
    ├── calculo_f1.py
    ├── test_calculo_f1.py
    ├── grafico_f1.py
    ├── montar_decisao_humana.py
    ├── concordancia_auto_humano.py
    ├── resultados_f1.csv           # gerado
    ├── resumo_f1.md                # gerado
    ├── grafico_f1.png              # gerado
    ├── decisao_humana.csv          # gerado (R1)
    ├── decisao_humana_sens_R2.csv  # gerado (sensibilidade)
    └── tabela_auto_humano.csv      # gerado
```

## 4. Como executar (passo a passo)

**Requisitos:** Python 3.9 ou superior. O cálculo do F1 usa só a biblioteca padrão. Só o gráfico precisa de `matplotlib` (`pip install matplotlib`).

Todos os comandos são rodados **de dentro de `atividade3/metricas/`**.

```bash
# 1) (opcional, recomendado) rodar os testes unitários
python -m unittest -v test_calculo_f1.py

# 2) calcular precisão, recall e F1 das 12 saídas
python calculo_f1.py
#    gera resultados_f1.csv e resumo_f1.md e imprime a tabela na tela

# 3) gerar o gráfico (F1 por caso e versão, com a linha do τ)
python grafico_f1.py
#    gera grafico_f1.png

# 4) montar a decisão humana final a partir do R1 (Pessoa 6) e do R2 (Pessoa 7)
python montar_decisao_humana.py --r1 ../avaliacoes/avaliacao_humana_R1.xlsx \
    --r2 ../avaliacoes/R2.csv --saida decisao_humana.csv --sensibilidade
#    gera decisao_humana.csv (decisão operacional = R1) e decisao_humana_sens_R2.csv;
#    imprime a comparação R1 x R2 nas 4 saídas revisadas (.xlsx exige: pip install openpyxl)

# 5) calcular a concordância automático-humano (M3) e listar divergências
python concordancia_auto_humano.py --humano decisao_humana.csv
#    gera tabela_auto_humano.csv e imprime iguais/12, aprovação humana por versão e divergências
```

Opções úteis do `calculo_f1.py`:

| Opção | Padrão | Para quê |
|---|---|---|
| `--tau` | `0.50` | Limiar do sinal automático. **Não mudar depois de ver os resultados** (ver seção 8). |
| `--raiz` | pasta pai da pasta do script | Caminho da pasta `atividade3/`, caso o script esteja em outro lugar. |
| `--saida` | `<raiz>/metricas` | Pasta onde gravar os resultados. |

**Formato do arquivo `decisao_humana.csv`** (gerado pelo passo 4; uma linha por saída). Se o grupo registrar um consenso formal em CT01 e CT05, passe `--consenso consenso.csv` (colunas `caso,versao,aprovacao_humana`) para ele prevalecer nessas saídas:

```csv
caso,versao,aprovacao_humana
CT01,A,0
CT01,B,1
...
```

Aceita `1/0` ou `aprova/reprova`. Aprovação humana = três notas 2 **e** nenhuma falha crítica (regra da seção 1.2 do relatório). O script exige as 12 linhas e avisa se faltar alguma.

## 5. Para que serve cada arquivo

| Arquivo | Para que serve |
|---|---|
| `calculo_f1.py` | Programa principal. Lê referências e saídas brutas, tokeniza, calcula P, R, F1, aplica τ e grava os resultados. As regras fixas estão documentadas no cabeçalho do arquivo. |
| `resultados_f1.csv` | **Entregável principal.** Uma linha por saída (12), com contagens de tokens, P, R, F1, sinal e colunas diagnósticas (seção 6). |
| `resumo_f1.md` | Tabela legível das 12 saídas e as médias/medianas por versão, pronta para consultar ou colar no relatório. |
| `grafico_f1.py` / `grafico_f1.png` | Gráfico de barras do F1 por caso e versão, com a linha do τ. Atende ao "gráfico ou visualização" da Parte E. |
| `montar_decisao_humana.py` | Lê o R1 (`.xlsx`/`.csv`) e o R2 (`.csv`), normaliza nomes (`CT-01` → `CT01`, `SIM`/`Aprovado` → aprova), confere a regra de aprovação, compara R1 × R2 nas 4 saídas revisadas e grava `decisao_humana.csv`. |
| `concordancia_auto_humano.py` | Cruza o sinal automático com a decisão humana final: calcula M3 (iguais/12) e lista as divergências, que são o ponto de partida da análise obrigatória. |
| `decisao_humana.csv` / `decisao_humana_sens_R2.csv` | Decisão humana por saída (R1) e variante em que as 4 saídas do R2 usam a decisão do R2 (análise de sensibilidade). |
| `tabela_auto_humano.csv` | Saída do script anterior: F1, sinal, decisão humana e se concordam, por saída. |
| `test_calculo_f1.py` | 15 testes unitários: tokenização, casos extremos, um cálculo conferido à mão (CT05/B) e a normalização da decisão humana. |
| `README.md` | Este documento. |

## 6. Colunas do `resultados_f1.csv`

| Coluna | Significado |
|---|---|
| `caso`, `versao` | Identificam a saída (CT01–CT06; A ou B). |
| `n_objetos_saida` | Quantos objetos JSON a saída trouxe (0 = `[]`). |
| `tokens_resposta`, `tokens_referencia`, `tokens_comuns` | Contagens usadas nas fórmulas. |
| `precisao`, `recall`, `f1` | Medida **oficial** (texto completo, ver seção 7). |
| `tau`, `sinal_automatico` | Limiar usado e classificação ("aprova" se F1 ≥ τ). |
| `f1_texto_sensibilidade`, `sinal_texto_sensibilidade` | F1 recalculado só com `titulo` + `conteudo`. **Não é oficial**; mostra o quanto URL e links elevam o F1. |
| `saida_vazia` | 1 se a saída foi `[]`. Saída vazia **não é descartada**: recebe F1 = 0. |
| `json_valido` | Vem do registro da Pessoa 4. |
| `url_exata`, `links_iguais`, `titulo_nulo` | Verificações auxiliares contra a referência. Ajudam a investigar divergências, mas **não substituem a rubrica humana** nem definem falha crítica. |
| `saida_sha` | Hash da saída (do registro da Pessoa 4); duas saídas com o mesmo hash são idênticas (por exemplo, CT03 em A e B). |

## 7. As fórmulas e o que cada uma significa

### 7.1 Tokens e o que conta como "palavra"

Antes de comparar, os dois textos passam pelo mesmo tratamento:

1. **Normalização Unicode NFC:** letras com acento têm uma única forma de representação.
2. **`casefold`:** tudo em minúsculas ("Página" = "página").
3. **Tokenização:** sequências de letras e dígitos viram um token cada. Números com separador decimal ("18,90") viram **um** token; "8h" também é **um** token; "10/11" vira dois ("10" e "11"). Pontuação não conta.

Acentos **não** são removidos ("pagina" ≠ "página") e o markdown **não** é removido (`[acervo](http://localhost:8000/acervo)` gera vários tokens). Isso é deliberado: o tratamento é o mesmo nas duas versões e não mexe no texto do modelo.

### 7.2 Interseção de multiconjuntos

`tokens_comuns` conta quantas vezes cada palavra aparece nos **dois** textos, ficando com o **mínimo** de cada uma. Se a referência tem "a" duas vezes e a resposta uma, entra 1 em comum. Isso impede que repetir uma palavra aumente o F1.

### 7.3 Precisão, recall e F1

```
P  = tokens_comuns / tokens_da_resposta     (quanto do que o modelo escreveu está na referência)
R  = tokens_comuns / tokens_da_referencia   (quanto da referência o modelo cobriu)
F1 = 2 · P · R / (P + R)                    (média harmônica: só é alta se P e R forem altas)
```

- Resposta vazia ou sem nenhuma palavra em comum: **F1 = 0**.
- Referência sem tokens: o script **para com erro** (a atividade manda corrigir o caso, não inventar nota).
- P baixa com R alta significa que o modelo escreveu **demais**; R baixa com P alta significa que **faltou** conteúdo.

### 7.4 O sinal automático e o limiar τ

```
sinal_automatico = "aprova"   se F1 >= τ
                   "reprova"  se F1 <  τ        (τ = 0,50, fixado antes da bateria)
```

### 7.5 Concordância automático–humano (M3)

```
M3 = (número de saídas em que sinal_automatico == decisão humana final) / 12
```

O denominador é sempre **12**. Não confundir com a concordância R1–R2, que é calculada só nas 4 saídas revisadas duas vezes (iguais/4) e é responsabilidade da Pessoa 7.

### 7.6 Exemplo calculado à mão (CT05, versão B)

- Texto da resposta: `http://localhost:8000/ct05.html` + `Estamos atualizando esta página. Volte em breve.` (título é `null`). São 12 tokens.
- Texto da referência: `Página em manutenção` + a URL + `Informação insuficiente: a página informa apenas que está em manutenção.`. São 18 tokens.
- Em comum: `http`, `localhost`, `8000`, `ct05`, `html`, `página` e `em`, ou seja, 7 tokens.
- P = 7/12 = 0,583; R = 7/18 = 0,389; F1 = 2·0,583·0,389 / (0,583+0,389) = **0,467** → "reprova", pois 0,467 < 0,50.

Esse valor está em `test_calculo_f1.py` como teste automático.

## 8. Decisões de projeto (e por quê)

| Decisão | Motivo |
|---|---|
| **Texto comparado = valores de `titulo`, `url`, `conteudo` e `links`, sem as chaves JSON.** | A referência é um objeto com os quatro campos. As chaves e a pontuação do JSON seriam tokens "de graça" e inflariam o F1 de qualquer saída com formato correto. A atividade não define "texto gerado", então esta é uma **escolha nossa** e deve estar registrada no relatório. |
| **Sensibilidade com só `titulo` + `conteudo`.** | URL e links costumam ser copiados corretamente e aumentam o F1. Mostrar as duas versões deixa claro o quanto o resultado depende dessa escolha. O sinal oficial não usa a sensibilidade. |
| **τ = 0,50, fixado antes.** | A atividade proíbe ajustar o limiar depois de ver os resultados. Qualquer mudança invalida a comparação. |
| **Saída vazia recebe F1 = 0 e continua na tabela.** | A atividade proíbe descartar falhas ou fabricar resposta. |
| **Execução única por caso e versão.** | É o que a atividade pede (12 saídas). Não há repetição, portanto não há medida de variabilidade. |

## 9. O que o F1 NÃO mede (limitações)

- **Fatos:** "10/11" no lugar de "11/11" mantém quase todas as palavras, mas muda a resposta. Os testes incluem esse exemplo.
- **Paráfrase correta:** pontua menos que cópia literal (por exemplo, CT06 em B).
- **Cópia de erros:** reproduzir erros de digitação da fonte quase não pune a saída.
- **Estrutura:** não verifica se o JSON é válido nem se o campo certo recebeu a informação. Para isso há a rubrica humana e as colunas diagnósticas.
- **Markdown dentro de `conteudo`:** adiciona tokens que reduzem a precisão sem haver erro de conteúdo.
- **Amostra:** 6 casos sintéticos, uma execução cada, e CT06 é derivado de CT01 (não é observação independente). Os resultados valem só para este conjunto.

## 10. Como testar e conferir os resultados

1. **Testes automáticos:** `python -m unittest -v test_calculo_f1.py` deve terminar com `Ran 15 tests ... OK`. Eles cobrem a tokenização ("8h", "18,90", datas, URLs), resposta vazia, ausência de sobreposição, multiconjunto, erro por referência vazia, o cálculo manual de CT05/B e a normalização de `caso` e `aprovação` das avaliações humanas.
2. **Quantidade:** `resultados_f1.csv` deve ter exatamente **12 linhas de dados** (6 casos × 2 versões).
3. **Conferência manual:** escolha uma linha, conte os tokens do JSON de saída e da referência e confira `tokens_comuns`, P, R e F1 com as fórmulas da seção 7. A seção 7.6 mostra um caso completo.
4. **Reprodutibilidade:** rodar `calculo_f1.py` duas vezes deve gerar arquivos idênticos (não há aleatoriedade).
5. **Sensibilidade a τ (apenas para discussão):** `python calculo_f1.py --tau 0.6 --saida /tmp/teste` grava os resultados em outra pasta e **não substitui os oficiais**. Não use isso para trocar o τ do relatório.

## 11. Resultados obtidos nas 12 saídas (τ = 0,50)

| Versão | F1 médio | F1 mediano | Aprovadas pelo sinal automático |
|---|---|---|---|
| A | 0,135 | 0,000 | 1/6 |
| B | 0,722 | 0,768 | 5/6 |

**Concordância automático–humano (M3): 12/12**, usando a decisão do R1 (Pessoa 6). Aprovação humana: A 1/6 e B 5/6, igual ao sinal automático. Não houve divergência; o caso-limite é CT05/B (F1 = 0,467, reprovado pelo F1 e pelo humano, por razões diferentes). Trocando o R1 pelo R2 nas 4 saídas revisadas, o resultado continua 12/12. Cinco dos 12 acordos vêm das saídas vazias de A. A interpretação está na seção 4 do relatório (`secao_relatorio_pessoa5.md`).

## 12. Dependências com as outras pessoas

| Preciso de | De quem | Para quê |
|---|---|---|
| τ e regra de falha crítica | Pessoa 1 | Aplicar o sinal automático (τ = 0,50 já está no relatório). |
| `referencias.json` | Pessoa 2 | Texto de referência de cada caso. |
| Versões A/B documentadas | Pessoa 3 | Saber qual prompt gerou cada saída. |
| 12 `saida_bruta.json` e `registro_execucoes.csv` | Pessoa 4 | Entrada do cálculo. |
| R1 (`avaliacao_humana_R1.xlsx`) e R2 (`R2.csv`); consenso formal, se houver | Pessoas 6 e 7 | Calcular M3 e analisar divergências. |

## 13. Solução de problemas

| Mensagem ou sintoma | Causa provável |
|---|---|
| `Faltando .../saida_bruta.json` | Falta alguma saída da Pessoa 4, ou o script foi rodado fora de `atividade3/metricas/` (use `--raiz`). |
| `FileNotFoundError: casos/referencias.json` | A pasta `casos/` não está em `atividade3/` ou `--raiz` aponta para o lugar errado. |
| `ValueError: Referencia sem tokens` | Alguma referência está vazia ou sem palavras. Corrija o caso; não mude o script. |
| `Sem decisao humana para: [...]` | O `decisao_humana.csv` não tem as 12 linhas. |
| `AVISO: ... R1 inconsistente com a regra` | A coluna de aprovação do R1 não bate com a regra (três notas 2 e falha crítica 0). Corrija com a Pessoa 6. |
| `Para ler .xlsx: pip install openpyxl` | Instale `openpyxl` ou exporte a aba do R1 para CSV. |
| `ModuleNotFoundError: matplotlib` | Só afeta o gráfico: `pip install matplotlib`. |
| Acentos quebrados ao abrir o CSV | Abra como UTF-8 (no Excel: Dados → Obter dados → De texto/CSV → UTF-8). |
