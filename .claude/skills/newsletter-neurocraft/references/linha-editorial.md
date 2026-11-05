# Linha editorial — newsletter Neurocraft

## A promessa ao leitor

> Dez minutos por mês que poupam ao executivo a leitura de trinta fontes, e que terminam com
> pelo menos uma decisão possível.

Se uma edição não permite ao leitor decidir nada, ela falhou — mesmo bem escrita.

## Público

C-level e líderes de dados e operações: CEO, COO, CIO, CDO, VP de engenharia e de manutenção,
em energia e oil & gas, manufatura, saneamento, saúde, AEC e setor público. Brasil, EUA e LatAm.

Consequências práticas:
- Escreva para quem aprova orçamento, não para quem escreve o pipeline.
- Toda sigla técnica ganha meia linha de explicação na primeira aparição, ou sai.
- Custo, risco e prazo são a moeda. Arquitetura só aparece quando muda um dos três.

## Filtro anterior à régua: as lentes do GTM Brasil

Antes de pontuar, passe o candidato pelas lentes de `tese-gtm-brasil.md`. Elas são
eliminatórias e mais baratas que a régua:

- **Contexto** — o item explica que contexto faz a tecnologia funcionar, ou só anuncia
  capacidade? Capacidade sem contexto é release, não notícia. Não pontue: reescreva ou corte.
- **Relevância** — o item ataca uma dor nomeável do leitor?
- **Canal real** — a solução encaixa em como o time brasileiro de fato trabalha?

## Régua de relevância

Cada candidato que passou pelas lentes recebe nota **0 a 3** em quatro eixos:

| Eixo | Pergunta | 0 | 3 |
|---|---|---|---|
| **Impacto** | Muda decisão, orçamento ou risco do leitor? | Curiosidade | Muda o plano do trimestre |
| **Proximidade** | Está no que Neurocraft e as marcas realmente fazem? | Fora do escopo | Núcleo da oferta |
| **Novidade** | Aconteceu na janela do mês? | Evergreen | Inédito e datado |
| **Evidência** | Tem fonte primária verificável? | Boato | Fonte primária com data |

**Corte: entra apenas item com total ≥ 8/12 E nota de Evidência ≥ 2.**
Nota de Evidência 0 ou 1 reprova o item independentemente do total.

## A regra do silêncio

> Se a Datamint (ou qualquer marca) não teve nada relevante no mês — dela ou do setor dela —
> **não publique nada sobre ela.**

Não existe bloco obrigatório. Não se inventa notícia para preencher seção. Uma edição com
duas marcas e três itens fortes vale mais do que quatro marcas e doze itens mornos, e é a
única forma de o leitor continuar acreditando na seleção no mês seguinte.

O item cortado não some: vai para o array `cortes` do JSON da edição, com o motivo. Isso vira
memória editorial — e evita que o mesmo item seja reavaliado do zero no mês seguinte.

## Estrutura da edição

Só a abertura e o CTA são fixos. Todo o resto é condicional.

1. **Assunto e preheader** — assunto ≤ 60 caracteres, específico. O preheader complementa, não repete.
2. **Abertura do editor** — 2 a 3 linhas, tom formal. A tese do mês e como ler a edição.
2a. **Mapa do mês** — um nó central com a tese e 2 a 4 ramos de frases curtas. Resume a edição;
   não traz fato que não esteja fonteado mais abaixo.
3. **O que mudou neste mês** — 3 a 5 movimentos do setor. Cada um com um "**e daí?**" explícito
   que nomeia a dor do leitor (ver *O que é um "e daí"*, abaixo).
4. **Blocos por marca** — condicionais. Neurocraft, Bizmetric, Vexta, Datamint, na ordem em que a relevância mandar.
5. **Deep dive** — um tema por edição, 200 a 400 palavras, com posição assumida. Rotativo.
   Perguntas para o fornecedor em linhas numeradas, não em parágrafo.
6. **Radar regulatório** — condicional. EU AI Act, LGPD/ANPD, ANP, ANEEL, ANS, ISO 42001.
7. **Números do mês** — 1 a 3 métricas, cada uma com fonte.
8. **Agenda** — condicional. Eventos e webinars dos próximos 60 dias.
9. **CTA único** — uma ação. Nunca duas.

Alvo total: **600 a 1.000 palavras.** Acima disso, corte — não resuma.

## Tom e formato — preferência de 08/10/2026

> Definida por Guilherme Cleffe em 08/10/2026, "por enquanto". Vale até ele dizer o contrário.

- **Formal e objetivo.** Sem humor, sem piada com o calendário, sem ironia. A edição de agosto
  abriu com "ainda em tempo"; esse registro está suspenso.
- **Curto e visual.** Resumo de item em 2 a 3 frases; "e daí" em 1 a 2. O mapa do mês carrega a
  leitura rápida; as seções servem a quem quer o detalhe.
- **Cobertura de evento por notícias.** Quando o mês tiver um grande evento do setor (ROG.e, OTC,
  Febraban Tech), cubra o que aconteceu por meio da imprensa e dos comunicados oficiais — vários
  itens curtos, cada um com fonte — em vez de um único item genérico sobre o evento.

## O que é um "e daí"

O critério #1 de decisão do profissional brasileiro **não é preço nem ROI** — é relevância para
o problema que ele tem (Panorama do GTM no Brasil 2026, HubSpot). Isso governa todo `so_what`:

- **Nomeie a dor primeiro.** Custo, risco e prazo são como se expressa a relevância, não o teste
  dela. Um item pode passar sem citar dinheiro, desde que ataque uma dor reconhecível.
- **Um "e daí" que só argumenta economia genérica e não nomeia a dor não passa.** "Reduz custos"
  não é um e daí; "elimina a varredura manual de 300 poços por semana" é.
- **Automação se enquadra como capacidade liberada, nunca como headcount reduzido** — e diga no
  que o tempo é reinvestido. O que trava a compra é medo de perder controle, não de perder posto.

## Rotação do deep dive

Evita a edição virar release de produto. Sugestão de ciclo trimestral:

1. **Mês 1 — Tecnologia aplicada:** um problema industrial real e a arquitetura que o resolve.
2. **Mês 2 — Governança e risco:** regulação, auditabilidade, o que muda no compliance.
3. **Mês 3 — Economia da decisão:** custo, ROI, o que medir para saber se a IA pagou.

## Voz

**É:** direta, técnica quando precisa, específica, com opinião. Frase curta. Verbo forte.
Número com fonte. Admite incerteza quando ela existe.

**Não é:** promocional, superlativa, cheia de "em um cenário cada vez mais dinâmico".

Proibido em qualquer edição:
- Adjetivo sem evidência: "revolucionário", "inovador", "de ponta", "líder de mercado".
- Frase de três itens paralelos como muleta de ritmo, repetida a cada parágrafo.
- Abertura por definição de dicionário ("A inteligência artificial é...").
- "Não é apenas X, é Y" — a construção antitética vazia.
- Conclusão que não conclui ("resta acompanhar os desdobramentos").
- Emoji no corpo. No assunto, no máximo um, e só se houver motivo.

## Temas vetados

Lista curta e datada. Só sai daqui com liberação expressa de quem vetou. A versão que o validador
aplica mecanicamente está em `config/vetos.json` — ao vetar ou liberar, atualize os dois.

| Tema | Desde | Quem | Regra |
|---|---|---|---|
| **Datamint (nome)** | 08/10/2026 | Guilherme Cleffe | **Não mencionar o nome** em nenhuma seção, fonte ou link, por enquanto. Item cujo único lastro é a Datamint sai da edição. |
| **NeuroEarthIQ, NeuroMineIQ e Vexta** | 30/09/2026 | Guilherme Cleffe | Aguardam o momento apropriado de publicação. Públicos no LinkedIn: restrição de timing, não de sigilo. |
| **Venezuela e PDVSA** | 30/09/2026 | Marcos de Almeida (16/09), aplicado por Guilherme (30/09) | **Não entra na edição**, em nenhum enquadramento. Sanções e compliance em aberto. Primeiro tentamos tom estritamente informativo; a conclusão foi que reescrever reduz o risco mas não o elimina — enquanto a questão estiver aberta, o assunto fica fora. |

Tema vetado não é tema esquecido: registre o candidato em `cortes` com o motivo, para que a
decisão seja revisável quando a situação mudar.

## Somente material público — preferência permanente

> Definida por Guilherme Cleffe em 30/09/2026. Vale até ele dizer o contrário.

A edição publica **apenas informação pública e não sensível**. Nada interno ou confidencial entra,
mesmo quando o conteúdo seria bom e mesmo quando não há impedimento jurídico.

Na prática:

- **Fonte pública verificável ou não entra.** Se o único caminho para a informação é Gmail, Notion,
  Drive ou CRM, ela não é publicável — vira insumo de contexto, nunca item da edição.
- **Anúncio de produto e lançamento próprio depende de liberação explícita**, mesmo já publicado
  em canal público. A empresa controla o momento da amplificação, não só o do anúncio.
- **Na dúvida, fora.** Registre em `cortes` com o motivo e siga. Custa uma edição mais curta;
  o inverso custa a relação.
- Se um item cortado por esta regra já for público, **diga isso no resumo ao usuário** — ele pode
  estar decidindo por timing achando que decide por sigilo. São coisas diferentes.

## Conflito de interesse e sigilo

- Nome de cliente só com autorização escrita registrada na pauta.
- Número de contrato, receita e volume de dados de cliente: nunca.
- Conteúdo de parceiro é sinalizado como tal. A newsletter não finge neutralidade que não tem.
- Ao citar um concorrente, cite-o corretamente. Erro sobre concorrente destrói a credibilidade
  da edição inteira.

## Métricas que importam

Acompanhar mensalmente, não semanalmente:

| Métrica | Referência inicial | Onde olha |
|---|---|---|
| Taxa de abertura | 35–45% (B2B, lista própria) | Ferramenta de envio |
| Clique único (CTR) | 3–6% | Ferramenta de envio |
| Respostas por edição | **> 2** | Caixa de entrada |
| Descadastros | < 0,5% | Ferramenta de envio |
| Reuniões atribuídas | 1 por trimestre já justifica | CRM |

**A métrica principal é resposta, não abertura.** Uma newsletter B2B para C-level que gera
conversa está funcionando; uma com 60% de abertura e zero resposta é decoração.
