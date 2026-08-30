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

## Régua de relevância

Cada candidato a item recebe nota **0 a 3** em quatro eixos:

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
2. **Abertura do editor** — 3 a 5 linhas. Uma tese sobre o mês, em primeira pessoa. Não é sumário.
3. **O que mudou neste mês** — 3 a 5 movimentos do setor. Cada um com um "**e daí?**" explícito.
4. **Blocos por marca** — condicionais. Neurocraft, Bizmetric, Vexta, Datamint, na ordem em que a relevância mandar.
5. **Deep dive** — um tema por edição, 400 a 600 palavras, com posição assumida. Rotativo.
6. **Radar regulatório** — condicional. EU AI Act, LGPD/ANPD, ANP, ANEEL, ANS, ISO 42001.
7. **Números do mês** — 1 a 3 métricas, cada uma com fonte.
8. **Agenda** — condicional. Eventos e webinars dos próximos 60 dias.
9. **CTA único** — uma ação. Nunca duas.

Alvo total: **900 a 1.400 palavras.** Acima disso, corte — não resuma.

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
