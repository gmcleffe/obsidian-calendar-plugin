# Checklist de publicação

Rodar **inteiro** antes de criar o rascunho. Qualquer item reprovado bloqueia a edição.

## 1. Fatos

- [ ] Todo item tem `fonte.url` e a URL foi de fato aberta nesta execução.
- [ ] Toda data está dentro da janela declarada, ou é explicitamente marcada como contexto anterior.
- [ ] Todo número foi conferido contra a fonte primária — não contra uma matéria que cita a fonte.
- [ ] Nome de empresa, produto e pessoa conferidos na grafia oficial.
- [ ] Nenhuma das marcas homônimas foi confundida (ver *Desambiguação* em `fontes.md`).
- [ ] Nenhuma afirmação sobre resultado de cliente sem evidência documentada.

## 2. Sigilo

- [ ] Nenhum nome de cliente sem autorização escrita registrada na pauta.
- [ ] Nenhum dado sob NDA, número de contrato, receita ou volume de dados de cliente.
- [ ] Nenhuma conta em pipeline aberto identificada nominalmente.
- [ ] Sinais de CRM e de vagas aparecem apenas agregados.
- [ ] Nada extraído de e-mail pessoal.

## 3. Editorial

- [ ] Cada seção passou na régua de relevância (≥ 8/12 e Evidência ≥ 2).
- [ ] Marca sem material relevante ficou **de fora** — e o motivo está em `cortes`.
- [ ] Cada item de "O que mudou" tem um "e daí?" que **nomeia uma dor**, não só argumenta economia.
- [ ] Nenhum item anuncia capacidade sem dizer que contexto a torna útil (lente 1).
- [ ] Toda frase sobre automação fala em capacidade liberada, não em headcount reduzido (lente 5).
- [ ] Anúncio de parceria — nosso inclusive — foi lido com a lente 4: assinada não é integrada.
- [ ] Número do Panorama do GTM Brasil está atribuído à HubSpot, e não é fonte única de tese nossa.
- [ ] Total entre 900 e 1.400 palavras.
- [ ] Um único CTA.
- [ ] Assunto ≤ 60 caracteres e específico. Preheader não repete o assunto.

## 4. Linguagem

- [ ] Nenhum termo da lista de proibidos (`linha-editorial.md`).
- [ ] Nenhuma sigla técnica sem explicação na primeira aparição.
- [ ] Sem parágrafo que só reformula o anterior.
- [ ] Passou pela skill `humanizer` se o texto soar padronizado.

## 5. Técnico

- [ ] `python3 scripts/edicao.py validar <pasta>` passou sem erro.
- [ ] HTML renderizado abre corretamente e é legível no modo escuro.
- [ ] Todos os links clicados uma vez no HTML final (link quebrado é o erro mais comum e o mais barato de evitar).
- [ ] Peso do HTML < 100 KB (acima disso o Gmail corta a mensagem).
- [ ] Rascunho criado — **nunca enviado** pelo agente.

## 6. Entrega

- [ ] Rascunho no Gmail, revisão humana pendente.
- [ ] `edicao.json` e `edicao.html` versionados em `edicoes/AAAA-MM/`.
- [ ] Resumo ao usuário: o que entrou, o que foi cortado e por quê, e o que precisa de decisão dele.
