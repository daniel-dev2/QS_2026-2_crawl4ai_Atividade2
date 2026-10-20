# Etapa 3 — Esquema JSON e Validador (QA Gate)

Este módulo implementa a camada de **Garantia da Qualidade de Dados (QA Gate / Data Validator)** para pipelines de web scraping construídos com a biblioteca **Crawl4AI** e **Pydantic v2**.

Ele atua inspecionando os dados logo após a coleta, aplicando validações estruturais, saneamento automático e isolando dados anômalos em quarentena (Dead Letter Queue - DLQ).

---

## Estrutura de Arquivos

```text
3_EsquemaJsonEValidador/
│
├── schema.py               # Contrato Pydantic v2 (PageExtractionSchema) e exportador de JSON Schema
├── validator.py            # Classe DataQualityValidator (QA Gate, saneamento, logs e quarentena)
├── crawler_integration.py  # Exemplo integrado com AsyncWebCrawler do Crawl4AI
├── test_validator.py       # Bateria completa com 26 testes unitários automatizados (pytest)
├── page_schema.json        # Representação JSON Schema gerada para o time
├── quarantine/             # Pasta de quarentena (DLQ) com os registros rejeitados em formato JSON
└── README.md               # Este guia passo a passo
```

---

##  Passo a Passo para Instalar e Rodar

### Passo 1: Pré-requisitos e Dependências

Certifique-se de estar com o ambiente virtual Python ativado (Python 3.10 ou superior) e instale os pacotes necessários:

```powershell
pip install crawl4ai pydantic pytest
```

*(Opcional: se for a primeira vez utilizando o Crawl4AI na máquina, configure os navegadores do Playwright executando `crawl4ai-setup`).*

---

### Passo 2: Navegar até a Pasta do Módulo

No terminal (PowerShell ou Bash), navegue até esta pasta:

```powershell
cd 3_EsquemaJsonEValidador
```

---

### Passo 3: Executar a Bateria de Testes Unitários (`pytest`)

Para executar todos os 26 testes automatizados com relatório detalhado de cada caso de teste:

```powershell
python -m pytest -v
```

#### O que é validado nos testes:
* **Casos de Sucesso:** Validação de payloads válidos via dicionário e via string JSON.
* **JSON Malformado:** Strings truncadas, chaves quebradas e strings vazias são rejeitadas.
* **Campos Obrigatórios:** Ausência de `titulo`, `url` ou `conteudo` reprova o registro.
* **Validação Estrita de URLs:** URLs sem protocolo `http`/`https` ou sem host são rejeitadas.
* **Regras de Negócio de QA:** Títulos contendo apenas espaços ou conteúdos menores que 20 caracteres são reprovados.
* **Saneamento Automático:** URLs quebradas (`javascript:`, `#links`, etc.) em `links` são descartadas, mantendo as válidas.
* **Persistência em Quarentena:** Validação de que arquivos na pasta `quarantine/` gravam os erros e payload original.
* **Auditoria de Logs:** Validação de captura dos logs estruturados do QA Gate.

---

### Passo 4: Executar a Integração com Crawl4AI

Para rodar a demonstração prática do crawler assíncrono consumindo uma página web e passando os dados pelo validador:

```powershell
python crawler_integration.py
```

O script executará 3 cenários em sequência:
1. **Cenário 1 (Sucesso):** O crawler extrai a página real (`example.com`), passa pelo QA Gate, é **aprovado** e exibe o JSON estruturado.
2. **Cenário 2 (Payload Corrompido):** Simula campos inválidos, exibe logs de erro estruturados e envia o item para a pasta `quarantine/`.
3. **Cenário 3 (JSON Sintaticamente Quebrado):** Simula string JSON truncada, detecta o `JSONDecodeError` e isola em `quarantine/`.

---

### Passo 5: Gerar / Atualizar o JSON Schema para a Equipe

Para gerar ou atualizar o arquivo `page_schema.json` (padrão formal compartilhado com os outros membros do time):

```powershell
python schema.py
```

O arquivo `page_schema.json` será atualizado automaticamente nesta pasta.

---

## Como Funciona a Quarentena (`quarantine/`)

Quando um payload é rejeitado pelo QA Gate por violação estrutural ou de contrato, ele é gravado em um arquivo JSON exclusivo dentro de `quarantine/` com o seguinte formato:

```json
{
  "quarantined_at": "2026-10-20T20:11:47.862548+00:00",
  "error_type": "ValidationError",
  "failed_fields": ["conteudo", "titulo", "url"],
  "error_messages": [
    "Campo 'titulo': Value error, O campo 'titulo' não pode ser vazio ou conter apenas espaços em branco.",
    "Campo 'url': Value error, A URL de origem 'protocolo_invalido://sem-host' possui protocolo inválido.",
    "Campo 'conteudo': Value error, O campo 'conteudo' deve ter no mínimo 20 caracteres representativos."
  ],
  "raw_payload": { ... }
}
```

Isso garante auditabilidade total sem interromper o pipeline principal de scraping.

