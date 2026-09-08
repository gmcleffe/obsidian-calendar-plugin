---
name: newsletter-neurocraft
description: Produz a newsletter mensal da Neurocraft para clientes e parceiros, cobrindo Neurocraft, Bizmetric, Vexta e Datamint. Apura fontes internas (Gmail, Notion, Google Drive, Apollo/CRM) e externas (plataformas, regulação, setor), aplica a régua de relevância, monta a edição em pt-BR para C-level e entrega um rascunho no Gmail. Use quando o usuário pedir "newsletter do mês", "edição de <mês>", "montar a pauta da newsletter", "rodar a newsletter da Neurocraft", ou quando um agendamento mensal disparar a produção da edição.
---

# Newsletter mensal da Neurocraft

Agente editorial. Apura, seleciona, escreve, valida e entrega **um rascunho** — a decisão de
enviar é sempre humana.

## Antes de começar

Leia, nesta ordem:

1. `config/marcas.json` — marcas ativas, posicionamento, stack, contas de publicação.
2. `references/icp-leitor.md` — quem lê e o **inventário de dores**. Todo `so_what` mapeia para
   uma delas.
3. `references/linha-editorial.md` — régua de relevância, estrutura, o que é proibido.
4. `references/voz-e-narrativa.md` — tom, equívocos a combater, repertório de origem, CTA.
5. `references/tese-gtm-brasil.md` — as cinco lentes que filtram candidatos antes da régua.
6. `references/fontes.md` — o que consultar e em que ordem de prioridade.

Antes de escrever (Fase 4), leia também `edicoes/2026-08/edicao.md` inteira — é a referência
canônica de estilo, e imitar um exemplo bom funciona melhor que seguir uma regra abstrata.

Nunca reescreva regra editorial dentro deste arquivo: ela mora nas referências.

**Pré-requisitos.** O connector do Gmail precisa estar autorizado para a conta usada. Se
`Guilherme.Cleffe@neurocraft.ai` não estiver conectada, apure só o que estiver acessível,
**diga isso explicitamente no resumo final** e siga — não bloqueie a edição por isso.

## Regra que manda em todas as outras

> Marca sem material relevante no mês **não aparece na edição.** Nem uma linha.

Vale para Neurocraft também. Registre o motivo em `cortes` e siga. Nunca preencha seção com
notícia fraca, evergreen ou release requentado.

---

## Fase 0 — Radar semanal (acumular, não escrever)

Apurar 30 dias no dia 1º é quando se perde material: post afunda no feed, release sai do ar.
O radar roda **toda semana**, gasta poucos minutos e só acumula candidatos.

```bash
python3 .claude/skills/newsletter-neurocraft/scripts/edicao.py nova --se-preciso
python3 .claude/skills/newsletter-neurocraft/scripts/edicao.py radar list --desde 2026-08-01
```

1. Abre (ou reusa) a pasta do mês corrente.
2. Varre as fontes da semana — camada 1 e as internas, que são as mais perecíveis.
3. **Antes de anotar qualquer coisa**, passa as URLs por `radar check`. O que já foi visto não
   volta para a pauta: já foi publicado ou já foi cortado com motivo registrado.
4. Anota o que sobrou em `pauta.md` como candidato, **sem pontuar e sem escrever**.

Não produza edição aqui. O radar só alimenta a pauta.

## Fase 1 — Abrir a edição

```bash
python3 .claude/skills/newsletter-neurocraft/scripts/edicao.py nova          # mês anterior
python3 .claude/skills/newsletter-neurocraft/scripts/edicao.py nova 2026-08  # mês específico
```

Cria `edicoes/AAAA-MM/` com `edicao.json` e `pauta.md`, e imprime a **janela de apuração**.
Tudo que for apurado daqui em diante é referido a essa janela.

## Fase 2 — Apurar

Comece pelo que o radar semanal já acumulou em `pauta.md`, e apure só o que faltou.

**Consulte o radar antes de apurar.** `radar check <urls>` diz o que já foi publicado ou cortado
em edição anterior, com o motivo. Item já cortado não volta sem fato novo — a nota do eixo
Novidade é 0, e reavaliá-lo do zero todo mês é desperdício que o leitor acaba percebendo.

Rode as buscas em paralelo. **Fontes internas primeiro** — são o diferencial da edição; o que
sai do Google todo mundo já leu.

**Internas** (ver a tabela em `references/fontes.md`)
- Gmail: `search_threads` nas duas contas, filtrando pela janela. Procure anúncios, marcos de
  projeto, movimentos de parceiro, convites de evento.
- Notion: `notion-search` por projetos entregues, cases e notas de reunião do mês.
- Google Drive: `search_files` por decks e relatórios modificados na janela; leia os relevantes.
- Apollo: deals fechados e contas novas (`apollo_deals_search`); vagas abertas nas contas-alvo
  (`apollo_organizations_job_postings`) como sinal antecedente de demanda.

**Externas**
- Camada 1, uma marca por vez: site e LinkedIn de Neurocraft, Bizmetric, Vexta e Datamint.
  Confira a desambiguação em `config/marcas.json` — há homônimos, e citar a empresa errada
  queima a edição inteira.
- Camada 2: o que mudou em Azure, Fabric, AI Foundry, Databricks, Snowflake, Google Cloud,
  Nvidia. Só entra o que altera custo, risco ou prazo do leitor.
- Camada 3: regulação (EU AI Act, ANPD/LGPD, ISO 42001, ANP, ANEEL, ANS) e pesquisa.
- Camada 4: mercado e negócios, sempre com checagem cruzada.

Anote **todo** candidato em `pauta.md`, inclusive o que você já sabe que vai cortar. A pauta é
o registro de auditoria da edição.

## Fase 3 — Pontuar e cortar

Primeiro as lentes de `tese-gtm-brasil.md`, que são eliminatórias e mais baratas que a régua:
capacidade anunciada sem o contexto que a torna útil é release, não notícia — reescreva ou corte
antes de pontuar.

O que sobrou vai para a régua de `linha-editorial.md`: quatro eixos de 0 a 3, **corte em ≥ 8/12
com Evidência ≥ 2**. Preencha a tabela de `pauta.md` com as notas — não pontue de cabeça,
escreva as notas.

Depois:
- Item aprovado → vira item de seção em `edicao.json`.
- Item reprovado → entra em `cortes` com `{"marca", "item", "url", "motivo"}`. **A `url` não é
  opcional na prática:** sem ela o corte não entra no radar e o item volta a ser avaliado do zero
  no mês que vem. O validador avisa quando falta.
- Marca sem nenhum item aprovado → **sem bloco**, e um registro em `cortes` explicando o silêncio.

Se sobraram menos de três itens na edição inteira, pare e avise o usuário: pode ser mês fraco
de verdade (aí a edição é curta mesmo) ou apuração incompleta. Não invente conteúdo para fechar
o volume.

## Fase 4 — Escrever

Preencha `edicoes/AAAA-MM/edicao.json`. Estrutura:

```jsonc
{
  "edicao": "2026-08",
  "janela": { "inicio": "2026-08-01", "fim": "2026-08-31" },
  "assunto": "≤ 60 caracteres, específico",
  "preheader": "complementa o assunto, não repete",
  "editorial": "3 a 5 linhas em primeira pessoa. Uma tese sobre o mês.",
  "secoes": [
    { "tipo": "movimentos", "titulo": "O que mudou em agosto",
      "itens": [ { "titulo": "", "resumo": "", "so_what": "obrigatório aqui",
                   "fonte": {"nome": "", "url": ""}, "data": "2026-08-12" } ] },
    { "tipo": "marca", "marca": "datamint", "titulo": "", "chapeu": "opcional",
      "itens": [ { "titulo": "", "resumo": "", "so_what": "",
                   "fonte": {"nome": "", "url": ""}, "data": "2026-08-07" } ] },
    { "tipo": "deepdive", "titulo": "", "corpo": ["parágrafo", "parágrafo"],
      "fontes": [ {"nome": "", "url": ""} ] },
    { "tipo": "radar",  "titulo": "", "itens": [ /* como marca */ ] },
    { "tipo": "numeros","titulo": "", "itens": [ {"valor": "US$ 5M", "rotulo": "",
                                                  "fonte": {"nome": "", "url": ""}} ] },
    { "tipo": "agenda", "titulo": "", "itens": [ {"titulo": "", "quando": "", "onde": "", "url": ""} ] }
  ],
  "cta": { "texto": "uma única ação", "url": "https://" },
  "cortes": [ { "marca": "vexta", "item": "", "motivo": "" } ]
}
```

Regras de escrita:
- Item fora da janela só entra com `"contexto": true` e um motivo claro para o pano de fundo.
- `so_what` **nomeia uma dor** do inventário de `icp-leitor.md`. Custo, risco e prazo são como se
  expressa a relevância, não o teste dela — "reduz custos" não é um e daí. Se o item não mapeia
  para nenhuma dor da lista, ou ele não interessa, ou a lista está incompleta.
- Automação se enquadra como capacidade liberada, nunca como headcount reduzido.
- Ordene as seções pela relevância do mês, não pela ordem do `config`.
- Alvo de 900 a 1.400 palavras. Um CTA só.
- Se o texto sair padronizado demais, passe pela skill `humanizer` antes de validar.

## Fase 5 — Validar e renderizar

```bash
python3 .claude/skills/newsletter-neurocraft/scripts/edicao.py validar edicoes/2026-08
python3 .claude/skills/newsletter-neurocraft/scripts/edicao.py render  edicoes/2026-08
```

O validador reprova item sem fonte, sem data, com data fora da janela, `so_what` faltando em
movimento, assunto longo demais, bloco de marca vazio e CTA quebrado. **Erro reprova a edição —
corrija o conteúdo, nunca afrouxe o validador.**

Depois, rode `references/checklist-publicacao.md` inteiro. Abra cada link uma vez: link quebrado
é o defeito mais comum e o mais barato de evitar.

## Fase 6 — Entregar

Crie o **rascunho** no Gmail (`create_draft`) com o HTML de `edicao.html`, assunto de `assunto`
e a conta de `publicacao.conta_rascunho`.

**Nunca envie.** `send_message` não faz parte deste fluxo, em nenhuma circunstância — nem se o
agendamento disparar sozinho, nem se a edição estiver perfeita.

Registre a edição na memória entre meses e commite tudo:

```bash
python3 .claude/skills/newsletter-neurocraft/scripts/edicao.py radar sync edicoes/2026-08
```

`radar sync` é idempotente e deriva `edicoes/radar.csv` do próprio JSON — não se mantém o radar
à mão. Commite `edicao.json`, `edicao.html`, `edicao.md`, `pauta.md` e `radar.csv`.

Termine com um resumo curto ao usuário:
1. O que entrou, por seção.
2. **O que foi cortado e por quê** — especialmente marca que ficou de fora.
3. O que precisa de decisão humana: citação de cliente, número sensível, CTA.
4. Qualquer fonte que não pôde ser consultada.

---

## Limites

- Não envia e-mail. Só rascunho.
- Não cita cliente sem autorização escrita registrada na pauta.
- Não publica número sem fonte primária aberta nesta execução.
- Não preenche seção por simetria.
- Não altera `config/marcas.json` sem o usuário pedir.
