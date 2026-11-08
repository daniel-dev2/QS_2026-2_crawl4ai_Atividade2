# Referências humanas e fontes — Atividade 3

Cada referência foi escrita a partir do trecho da fonte indicada, não de saída de modelo.
**Revisão humana obrigatória:** conferir cada referência contra o HTML e preencher revisor/data.

---

## CT01 — Funcional (biblioteca)
- **Fonte:** `fontes/ct01.html` · **URL:** http://localhost:8000/ct01.html
- **Trecho que sustenta:** "A biblioteca funciona de segunda a sexta, das 8h às 17h." / "O empréstimo de livros é gratuito, por até 14 dias." / links `acervo`, `contato`.
- **Referência:**
```json
{"titulo":"Biblioteca Comunitária Sol Nascente","url":"http://localhost:8000/ct01.html","conteudo":"Funciona de segunda a sexta, das 8h às 17h. Empréstimo de livros gratuito por até 14 dias.","links":["http://localhost:8000/acervo","http://localhost:8000/contato"]}
```


## CT02 — Funcional (produto)
- **Fonte:** `fontes/ct02.html` · **URL:** http://localhost:8000/ct02.html
- **Trecho que sustenta:** "Preço: R$ 18,90." / "Disponibilidade: em estoque." / "Capa dura, 10 matérias." / links `papelaria` e `carrinho`, ambos no corpo principal.
- **Referência:**
```json
{"titulo":"Caderno Universitário 200 Folhas","url":"http://localhost:8000/ct02.html","conteudo":"Preço R$ 18,90. Em estoque. Capa dura, 10 matérias.","links":["http://localhost:8000/papelaria","http://localhost:8000/carrinho"]}
```


## CT03 — Funcional (evento)
- **Fonte:** `fontes/ct03.html` · **URL:** http://localhost:8000/ct03.html
- **Trecho que sustenta:** "De 18 a 20 de novembro de 2026, no Auditório B." / "Inscrições gratuitas até 14 de novembro." / links `programação` e `inscrição`, ambos no corpo principal.
- **Referência:**
```json
{"titulo":"Semana de Tecnologia 2026","url":"http://localhost:8000/ct03.html","conteudo":"De 18 a 20 de novembro de 2026, no Auditório B. Inscrições gratuitas até 14 de novembro.","links":["http://localhost:8000/eventos/programacao","http://localhost:8000/eventos/inscricao"]}
```


## CT04 — Funcional (ruído de menu/rodapé)
- **Fonte:** `fontes/ct04.html` · **URL:** http://localhost:8000/ct04.html
- **Trecho que sustenta:** "O laboratório possui 20 computadores e foi inaugurado em 3 de setembro." / link `estágios abertos` dentro do `<article>`. Menu (`Início`, `Notícias`, `Contato`) e rodapé (`Privacidade`) ficam fora por regra.
- **Referência:**
```json
{"titulo":"Novo laboratório de redes é inaugurado","url":"http://localhost:8000/ct04.html","conteudo":"O laboratório possui 20 computadores e foi inaugurado em 3 de setembro.","links":["http://localhost:8000/noticias/estagios"]}
```


## CT05 — Sem evidência suficiente (abstenção)
- **Fonte:** `fontes/ct05.html` · **URL:** http://localhost:8000/ct05.html
- **Trecho que sustenta:** "Estamos atualizando esta página. Volte em breve." (não há horário, contato nem outros dados). A página não tem nenhum link, por isso `links` é uma lista vazia.
- **Comportamento esperado:** declarar a limitação em `conteudo`, `links` vazio, nenhum dado inventado (horário, telefone, etc.).
- **Referência:**
```json
{"titulo":"Página em manutenção","url":"http://localhost:8000/ct05.html","conteudo":"Informação insuficiente: a página informa apenas que está em manutenção.","links":[]}
```


## CT06 — Variação de CT01 (erros de digitação + paráfrase)
- **Fonte:** `fontes/ct06.html` · **URL:** http://localhost:8000/ct06.html
- **Alterações em relação a CT01:** "Comunitaria" (sem acento), "funsiona", "as 8h" (sem crase), e a frase do empréstimo reescrita ("Você pode pegar livros emprestados sem custo por até 14 dias"). Os links `acervo` e `contato` são os mesmos de CT01.
- **Referência (mesmo sentido de CT01, com ortografia corrigida):**
```json
{"titulo":"Biblioteca Comunitária Sol Nascente","url":"http://localhost:8000/ct06.html","conteudo":"Funciona de segunda a sexta, das 8h às 17h. Empréstimo de livros gratuito por até 14 dias.","links":["http://localhost:8000/acervo","http://localhost:8000/contato"]}
```

