# Edição de outubro — três versões comparadas

1. **Rascunho do agente** (commit `d39bf6e`).
2. **Enviado por Guilherme Cleffe** em 09/11/2026, 16h11 (Brasília), via Outlook.
3. **Revisão de Marcos de Almeida** em 10/11/2026, feita **depois** do envio aos clientes. O HTML
   está em `revisao-marcos.html`.

`edicao.json` registra a versão 3, que é a referência visual daqui em diante.

## A. O que Guilherme mudou antes de enviar (1 → 2)

| Onde | Rascunho | Enviado |
|---|---|---|
| Assunto | Sua próxima PoC de IA pode sair por conta da Microsoft | **[Neurocraft.ai newsletter]** Sua próxima PoC **conosco** pode sair por conta da Microsoft **(Sim! Custo zero!)** |
| Abertura | "Uma pergunta direta: quanto do seu orçamento de 2027…" | "Quer investir em dados e IA, mas o orçamento de 2027 está apertado? **Nós podemos ajudar!**" |
| Editorial | "…não o fornecedor" | "…não o **parceiro**" |
| Assinatura | "Guilherme Cleffe, GTM Latam" | removida |
| Mapa, centro | "A PoC que parou por orçamento pode ser financiada" | "…por orçamento**,** agora pode ser financiada" |
| ECIF | "Quem indica a conta é a própria Microsoft. O parceiro precisa estar habilitado" | frase da indicação removida; "O parceiro **(nós no caso)** precisa estar habilitado" |
| ECIF, e daí | "…parou por falta de orçamento… a quem tem a verba" | "…**não avançou**… a quem tem acesso a **estes recursos**" |
| Azure, e daí | "Quanto, depende do escopo" | "**Quanto? Depende** do escopo" |
| Como fazemos | título sem interrogação; "ativo crítico ou uma falha" | "Como fazemos a sua PoC**?**"; "ativo crítico, **redução de custos** ou uma falha" |
| Status | "Nosso **status premium** junto à Microsoft" | "Nosso **track record** junto à Microsoft" |

**Perdido no envio** (o HTML foi colado do Gmail no Outlook):

- todo o visual: cores, hierarquia e larguras; o texto virou Aptos 11pt preto;
- o **gráfico do a16z**: ficou só a legenda "Redesenhado pela Neurocraft";
- o preheader e o botão de CTA (o e-mail fechou sem chamada para ação);
- **todos os links passaram a apontar para `google.com/url?q=…&source=gmail`**, um
  redirecionador do Gmail que pode abrir uma tela de aviso.

O envio também gerou uma devolução definitiva (550 5.4.1): um destinatário não existe mais. O
endereço não fica neste repositório, porque ele é público.

## B. O que Marcos mudou em relação ao enviado (2 → 3)

### Visual

- Cabeçalho em degradê azul-marinho (#0A1630 → #1B3F8B), com logo **"NeuroCraft.ai"** em Georgia
  dourada (#E8B84A/#F6D77B) e "Newsletter · Nov 2026", ou seja, o **mês de envio**.
- Hero com chapéu dourado ("Orçamento 2027"), título grande, subtítulo dourado e **botão de CTA já
  no topo** ("Quero avaliar minha PoC →").
- **Emojis como marcadores** de seção e de cartão: 🗺️ 💰 🛠️ 📊 ⚡ 👉 🎯 🔗 🎧 📄 🔌 ⚙️ ✉️ 🚀.
- Mapa em cartões coloridos, uma cor por tema: azul Microsoft, dourado NeuroCraft, laranja a16z
  e verde McKinsey. A tese do mês vira o título do mapa.
- **Faixa de números** nova em fundo escuro: 30+ · ~2% · +24%.
- Cada seção ganha uma etiqueta colorida ("Microsoft · ECIF", "Microsoft · Azure Accelerate",
  "NeuroCraft", "a16z · State of Markets II", "McKinsey · …").
- ECIF e Azure Accelerate viram duas seções.
- "Como fazemos" vira um cartão dourado com **passos numerados 1-2-3** e a condição em caixa escura.
- **Gráfico do a16z em barras HTML**, no lugar do PNG hospedado, posicionado logo depois do fato e
  antes do "e daí".
- McKinsey em dois cartões: 🔌 Demanda e ⚙️ Eficiência.
- "E daí:" vira **"👉 E daí?"**, em caixa.
- Fecho com bloco de CTA: pergunta "Qual problema você quer testar em 2027?", apoio "Responda em uma
  linha…", botão "✉️ Falar com o Guilherme" e link para neurocraft.ai.
- Rodapé escuro com o logo, o e-mail do remetente como `mailto:` e "© 2026 NeuroCraft ·
  Orchestrated Supervised Agentic AI".
- Container de 640px, com media query para o celular.

### Texto

- Grafia **"NeuroCraft"** em todo o e-mail (antes "Neurocraft"). O assunto não foi tocado.
- Editorial na primeira pessoa do plural: "Essa verba…" vira "**Existe uma** verba…" e
  "Abaixo explico" vira "Abaixo **explicamos**".
- "Nós podemos ajudar!" vira "Nós podemos ajudar. 🚀".
- Vírgula do centro do mapa removida; "(nós no caso)" vira "(nós**,** no caso)"; "estes recursos"
  vira "**esses** recursos".
- Preheader novo: "Orçamento de 2027 apertado? A Microsoft pode financiar a sua PoC de dados e IA.
  Veja como funciona."
- CTA `mailto:` com assunto "Quero avaliar uma PoC **financiada**" e **corpo pré-preenchido**
  ("Olá Guilherme, O problema que queremos testar é: ").
- McKinsey: frase dividida em dois cartões, sem mudança de conteúdo.
- O rótulo "contexto" sumiu das fontes.

### Links

- a16z: `a16z.news/p/state-of-markets-ii` passou a `a16z.com/state-of-markets-ii/`, que é a página
  oficial. Entrou também o **podcast** "The $1 Trillion AI Buildout".
- McKinsey: entrou a página de **principais conclusões** no blog, e o PDF ficou como secundário.
- Azure Accelerate: entraram o post do **Cloud Accelerate Factory** (techcommunity) e
  "Programas Azure para parceiros e clientes" (partner.microsoft.com).
- ECIF (Fifty Five and Five) e "Fontes: TD SYNNEX · Microsoft Azure Blog" viraram **texto sem
  link**.

## C. Pontos a corrigir na revisão do Marcos

Todos os links foram conferidos em 10/11/2026 e abrem.

1. **A data da McKinsey está errada.** A página de conclusões foi publicada em **27/10/2026**, mas
   aparece como 30/09. Em `edicao.json` ficou 27/10.
2. **O link "Programas Azure para parceiros e clientes" está defasado.** A página de
   partner.microsoft.com se chama "Azure Migrate and Modernize and Azure Innovate", os programas que
   o Azure Accelerate substituiu. Ficou fora de `edicao.json`.
3. **Fontes sem link.** Ir contra a preferência de 09/11 (link para o original) não ajuda quem
   quer conferir. Em `edicao.json` os links voltaram.
4. **Grafia "NeuroCraft".** Ela coincide com a de uma empresa homônima em Nova York (ver
   `fontes.md`). O logo sempre com ".ai" resolve a ambiguidade; adotado assim.
