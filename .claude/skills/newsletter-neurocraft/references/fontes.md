# Registro de fontes — newsletter Neurocraft

Curadoria em quatro camadas. A regra é simples: **quanto mais alta a camada, maior o peso
editorial e menor a necessidade de checagem cruzada.** Nada entra na edição sem uma fonte
das camadas 1 a 3, ou uma fonte interna com dono identificado.

---

## Camada 0 — Fontes internas (matéria-prima exclusiva)

É o que ninguém mais pode publicar. É o que faz a newsletter valer o clique. Priorize sempre.

| Fonte | O que extrair | Como acessar | Cuidado |
|---|---|---|---|
| **Gmail — `Guilherme.Cleffe@neurocraft.ai`** | Anúncios, updates de conta, marcos de projeto, movimentos de parceiros | Connector Gmail, busca por janela do mês | Conta corporativa precisa estar conectada (ver *Pré-requisitos* no SKILL.md) |
| **Gmail — `gmcleffe@gmail.com`** | Threads de parceria, convites de evento, releases recebidos | Connector Gmail | Descartar tudo que for pessoal |
| **Notion** | Projetos entregues, cases, roadmap, notas de reunião | `notion-search`, `notion-query-data-sources` | Nada marcado como confidencial/NDA sai daqui sem aprovação escrita |
| **Google Drive** | Decks de cliente, one-pagers, relatórios de entrega, material de parceiro | `search_files` + `read_file_content`, filtrando por data de modificação | Decks de cliente quase sempre têm dado sensível: extrair a *lição*, não o número |
| **Apollo / CRM** | Deals fechados no mês, contas novas, setores aquecidos | `apollo_deals_search`, `apollo_accounts_*` | Nunca citar nome de conta em pipeline aberto |
| **Apollo — job postings** | Vagas abertas nas contas-alvo = sinal antecedente de demanda | `apollo_organizations_job_postings` | Sinal agregado ("3 das 10 maiores operadoras abriram vaga de eng. de dados"), nunca nominal |

> **Sinal mais subestimado:** contratações. Quando uma operadora abre cinco vagas de engenharia
> de dados, ela está comprando plataforma nos próximos dois trimestres. Isso é conteúdo de
> C-level e sai de graça do Apollo.

---

## Camada 1 — Fontes primárias das marcas

Verdade de primeira mão sobre as quatro marcas. Publicar sem checagem cruzada é aceitável aqui.

- **Neurocraft** — <https://neurocraft.ai/> · [LinkedIn](https://www.linkedin.com/company/neurocraft-data-services-inc)
- **Bizmetric** — <https://www.bizmetric.ai/> · blog em <https://www.bizmetric.com/> · [LinkedIn](https://www.linkedin.com/company/bizmetric)
- **Vexta** — <https://vexta.lat/en/> · [LinkedIn](https://www.linkedin.com/company/vexta-ai)
- **Datamint** — <https://datamint.com.br/pt/> · [LinkedIn](https://www.linkedin.com/company/datamint)

Perfis pessoais que costumam anunciar antes da página da empresa: Marcos de Almeida (CEO
Neurocraft), Hélio Côrtes Vieira Lopes (co-fundador Datamint), Guilherme Cleffe.

> **Desambiguação obrigatória.** Existem várias empresas chamadas "Vexta" (Vexta Cloud/Kuwait,
> Vexta Ltd, VextaCFO) e várias chamadas "Neurocraft" (neurocraft.tech, NeuroCraft AI/NY). Também
> existe a brasileira **Neurotech**, que não tem relação nenhuma. Confirme o domínio antes de citar.

---

## Camada 2 — Plataformas e parceiros de tecnologia

O roadmap dessas plataformas *é* o roadmap do cliente. Anúncio de GA, mudança de preço ou
descontinuação aqui vira decisão de orçamento no cliente — este é o material com maior taxa
de leitura numa newsletter para C-level.

| Plataforma | Fonte | Relevante para |
|---|---|---|
| Microsoft Azure / Fabric / AI Foundry | Azure Updates, blogs de Fabric e Foundry, Build e Ignite | Neurocraft, Bizmetric |
| Databricks | Blog, release notes, Data + AI Summit | Bizmetric, Neurocraft |
| Snowflake | Blog, release notes | Bizmetric, Neurocraft |
| Google Cloud | Blog de dados e IA, Next | Datamint |
| Nvidia | Omniverse, IA industrial, GTC | Datamint, Vexta |
| Cognite, Neo4j, Redis, Oracle | Blogs de produto | Datamint, Bizmetric |

**Filtro:** anúncio de plataforma só entra se você conseguir escrever, em uma frase, o que muda
no orçamento ou no risco do leitor. "A Microsoft lançou X" não é notícia. "A Microsoft lançou X
e isso torna dispensável a camada Y que você paga hoje" é.

---

## Camada 3 — Setor, regulação e pesquisa

**Regulatório e governança** (alta prioridade — é o que tira o sono do C-level)
- EU AI Act — texto e cronograma de aplicação (`artificialintelligenceact.eu`, EUR-Lex)
- NIST AI Risk Management Framework · ISO/IEC 42001
- ANPD / LGPD — resoluções e consultas públicas
- Reguladores setoriais: ANP, ANEEL, EPE (energia); ANA (saneamento); ANS (saúde); ANM (mineração)

**Pesquisa e analistas**
- Stanford HAI AI Index · McKinsey State of AI · MIT Sloan Management Review
- Releases públicos de Gartner e Forrester (o relatório pago não; o release sim)
- ARC Advisory Group (automação industrial)

**Setoriais**
- Energia e O&G: Oil & Gas Journal, Offshore Technology, IBP, Agência ANP
- Manufatura e ativos: Plant Services, Reliabilityweb, IEEE Spectrum (energia/indústria)
- Mineração: Mining.com · Saneamento: Trata Brasil, ANA

---

## Camada 4 — Mercado e negócios

Para contexto de investimento, M&A e movimento competitivo. Sempre checagem cruzada.

- **Brasil:** Brazil Journal, NeoFeed, TI Inside, Valor Econômico, Exame
- **Global:** Reuters, Bloomberg / Bloomberg Línea, WSJ (energia e tecnologia), The Information

---

## Fontes vetadas

- Conteúdo de agregador de IA sem link para a fonte primária.
- Press release republicado sem data verificável.
- Qualquer coisa atrás de paywall que você não leu de fato — não parafraseie manchete.
- Post de LinkedIn de terceiro sobre notícia de terceiro (é boato até provar o contrário).
- Documento de cliente sob NDA, número de contrato, nome de conta em pipeline aberto.

---

## Manutenção deste registro

Revisar a cada trimestre. Ao adicionar fonte, registrar: **por que ela existe** (que lacuna
cobre) e **quem é o dono** da checagem. Fonte que não gerou um item aprovado em seis meses sai.
