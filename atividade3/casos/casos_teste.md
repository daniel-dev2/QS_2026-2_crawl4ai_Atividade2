# Casos de teste — Atividade 3 (Crawl4AI · saída estruturada)

**Recorte:** geração de saída estruturada do Crawl4AI. Entrada = uma página HTML fixa + a URL da página; saída = JSON no esquema `PageExtractionSchema` (`titulo`, `url`, `conteudo`, `links`).
**Modelo:** Qwen2.5-7B , igual em A e B. **Mudança A→B:** somente o prompt 

## Por que páginas HTML fixas e sintéticas
- Congelam a fonte: A e B recebem exatamente o mesmo conteúdo, e o experimento é reproduzível.
- Dados sintéticos, sem sigilo e sem dependência de site externo: as páginas são servidas localmente em `http://localhost:8000`.
- A `url` do campo de saída é o endereço real da página no servidor local (`http://localhost:8000/ct01.html` etc.), então a referência bate com o que o Crawl4AI enxerga.

## Como servir as páginas (Pessoa 4)
1. Abrir um terminal na pasta `atividade3/casos/fontes/`.
2. Rodar: `python -m http.server 8000`
3. Conferir no navegador: `http://localhost:8000/ct01.html`.
4. Manter o servidor ligado e a porta 8000 durante toda a execução de A e B. Se usarem outra porta: a `url` das referências muda junto.
5. Os links dentro das páginas (`/acervo`, `/contato` etc.) não existem de fato; o Crawl4AI só lê o texto deles e não deve segui-los.

## Regras de preenchimento (devem constar no prompt A e no prompt B)
1. `titulo` = texto do `<h1>` da página.
2. `url` = a URL informada abaixo, sem alteração.
3. `conteudo` = resumo fiel do texto principal, sem menu, rodapé ou informação inventada.
4. `links` = links do corpo principal (`<main>`/`<article>`), excluindo menu e rodapé; lista vazia se não houver.
5. Se a página não tiver informação suficiente, declarar isso em `conteudo`; não inventar dados.

## Resumo dos casos

| ID | Tipo | Fonte | URL informada | O que o caso exercita |
|---|---|---|---|---|
| CT01 | Funcional | `fontes/ct01.html` | http://localhost:8000/ct01.html | Extração básica: horário e prazo (números) + 2 links |
| CT02 | Funcional | `fontes/ct02.html` | http://localhost:8000/ct02.html | Fidelidade de valor monetário (R$ 18,90) |
| CT03 | Funcional | `fontes/ct03.html` | http://localhost:8000/ct03.html | Fidelidade de datas (18–20/11; inscrição até 14/11) |
| CT04 | Funcional | `fontes/ct04.html` | http://localhost:8000/ct04.html | Ruído: menu e rodapé devem ficar fora; `<title>` ≠ `<h1>` |
| CT05 | Sem evidência suficiente | `fontes/ct05.html` | http://localhost:8000/ct05.html | Abstenção: página só diz "em manutenção"; não inventar |
| CT06 | Variação de CT01 | `fontes/ct06.html` | http://localhost:8000/ct06.html | Mesma intenção de CT01, com erros de digitação e uma frase parafraseada |

## Observações
- CT06 **não é observação independente** de CT01.
- Referências e trechos de apoio: `referencias.md` (versão legível) e `referencias.json`.

## Pergunta de verificação e resposta esperada (para o avaliador humano)

O prompt do Crawl4AI é o mesmo em todos os casos. Estas perguntas curtas servem para o avaliador (R1/R2) checar se o JSON gerado contém a informação correta da fonte.

| ID | Pergunta de verificação | Resposta esperada |
|---|---|---|
| CT01 | Qual o horário de funcionamento e o prazo de empréstimo? | Segunda a sexta, 8h às 17h; empréstimo gratuito por até 14 dias |
| CT02 | Qual o preço e a disponibilidade do produto? | R$ 18,90; em estoque |
| CT03 | Quando e onde ocorre o evento, e até quando vão as inscrições? | 18 a 20 de novembro de 2026, Auditório B; inscrições até 14 de novembro |
| CT04 | Quantos computadores tem o laboratório e quando foi inaugurado? | 20 computadores; inaugurado em 3 de setembro (e o menu/rodapé não aparecem no conteúdo) |
| CT05 | Qual o horário de atendimento da secretaria? | Não há informação na página; o correto é declarar que a informação é insuficiente |
| CT06 | Mesma pergunta de CT01 | Mesma resposta de CT01, apesar dos erros de digitação e da paráfrase |
