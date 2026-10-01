# Newsletter Neurocraft — setembro de 2026

**Assunto:** O modelo virou commodity. E o contexto, é de quem?  
**Preheader:** Microsoft, Petrobras e Datamint apontaram para o mesmo gargalo em setembro. Falta saber quem guarda a resposta.

Setembro sai no primeiro dia de outubro. Desta vez, sem precisar pedir desculpa ao calendário.

O mês teve uma coincidência mais útil do que qualquer lançamento. Num painel em São Paulo, o CIO da Petrobras disse que a inteligência da empresa mora nos seus 1.800 sistemas legados. Em Barcelona, a Microsoft abriu os anúncios da FabCon dizendo que, com modelos cada vez mais disponíveis, o que diferencia uma empresa é o conhecimento que só ela tem. No Rio, a Datamint escreveu que é a fronteira do que o sistema pode fazer, mais que a sofisticação do modelo, que torna a autonomia aceitável.

Se o gargalo é o contexto, a pergunta de compra muda de lugar. Deixa de ser qual modelo usar e passa a ser onde fica escrito o que a sua operação sabe — e quem consegue levar isso embora.

## O que mudou em setembro

### A Microsoft levou o modelo semântico para dentro do Copilot

Na FabCon de Barcelona, em 28 de setembro, a Microsoft liberou o Fabric IQ no Copilot Chat e no Cowork, sem custo adicional de tokens. O Fabric IQ é a camada que junta os dados do OneLake, as métricas dos modelos semânticos do Power BI e o contexto operacional de ontologias. Entraram em preview o IQ sharing, para compartilhar dados e contexto governados com clientes e parceiros, e um agente de engenharia de dados que executa migrações dentro de limites definidos pelo engenheiro.

**E daí:** Para quem já tem Power BI, a definição de métrica que ninguém via — o que conta como "disponibilidade", quando uma parada é "não programada" — passa a decidir a resposta que o Copilot dá à diretoria. Se essa definição muda de um relatório para outro, agora isso aparece na frente de todo mundo. O trabalho de semântica, que raramente aparece em apresentação para a diretoria, virou o que sustenta o resto.

_Fonte: [Microsoft Azure Blog (Arun Ulag)](https://azure.microsoft.com/en-us/blog/fabcon-and-sqlcon-2026-in-barcelona-building-the-data-foundation-for-microsoft-copilot-and-agents/) · 28/09/2026_

### Petrobras: mais de 70 agentes rodando, e a inteligência mora no legado

Em painel promovido pela Deloitte em São Paulo, o CIO da Petrobras, Cassiano Ebert, disse que a companhia roda mais de 70 agentes de IA ao longo da cadeia e convive com 1.800 sistemas legados — e que é esse legado que abriga a inteligência da empresa. O caminho passou pelo Petronemo, assistente construído internamente, de forma soberana, sobre 30 anos de dados, com profissionais seniores participando do ajuste do modelo.

**E daí:** A frase desmonta o argumento de quem trata o sistema antigo como passivo a desligar. Ali está o julgamento técnico de décadas, e quem o produziu está perto de se aposentar. A Petrobras chamou os seniores para dentro do ajuste do modelo enquanto eles ainda estão lá para isso. A pergunta para a sua operação é quanto tempo essa janela ainda tem.

_Fonte: [TI INSIDE Online](https://tiinside.com.br/02/09/2026/pessoas-processos-e-dados-sao-cruciais-para-sucesso-da-ia-afirma-cio-da-petrobras/) · 02/09/2026_

### Na ROG.e, um em cada cinco trabalhos foi de transformação digital

A ROG.e fechou em 24 de setembro com 83 mil visitantes e 924 trabalhos técnicos apresentados. Dos 1.208 submetidos, segundo o IBP, 250 eram do eixo de Transformação Digital e Inovação, o segundo maior do congresso. O prêmio do eixo foi para Yuri Leal da Silva e Ian Fiori, da Petrobras, por otimização de plataformas offshore a partir de monitoramento de dados.

**E daí:** Volume de paper não é adoção: 250 estudos não dizem quantos viraram rotina de operação. O prêmio indica o critério que a própria engenharia está usando — ganho em plataforma que já produz, medido sobre dado de monitoramento. É um bom filtro para a pilha de pilotos do orçamento de 2027: o que melhora um ativo em operação passa na frente do que depende de sensor novo.

_Fonte: [Brasil Energia](https://brasilenergia.com.br/brasilenergia/rio-oil-gas-energy-2026/roge-2026-83-mil-visitantes-e-projecao-de-r-100-bi-em-contratos) · 25/09/2026_


## Datamint

_Parceira de go-to-market da Neurocraft no Brasil_

### A autonomia que não pode mudar a própria regra

Em publicação de 15 de setembro, a Datamint descreveu como o Asset 360 trabalha. Primeiro reconstrói o estado do ativo, juntando sensores, projetos, ordens de serviço e histórico numa leitura única, com cada dado rastreável até a origem. Depois organiza o contexto, propõe o curso de ação e executa apenas o que foi previamente autorizado. Segundo a empresa, o sistema não tem autoridade para alterar as próprias regras, e é essa fronteira, mais que o modelo, que torna a autonomia aceitável.

**E daí:** É uma resposta concreta à pergunta que deixamos em agosto, sobre quem aprova o quê. A autonomia vira contrato: o que foi homologado executa, o resto espera alguém. Leve a pergunta ao seu fornecedor atual — o sistema consegue alterar a regra que o autoriza? Se a resposta for "depende da configuração", peça para ver quem configura e onde isso fica registrado.

_Fonte: [Datamint (LinkedIn)](https://pt.linkedin.com/posts/datamint_datamint-ai-for-industrial-asset-management-activity-7505609165323812864-W___) · 15/09/2026_


## Deep dive · De quem é o contexto?

Durante dois anos, a pergunta de compra em IA foi qual modelo usar. Setembro tirou o valor dela. O próprio texto da Microsoft promete um ciclo de aprendizado que não deixa a organização dependente de um único provedor de modelo — um jeito educado de dizer que o modelo deixou de ser onde se ganha.

Repare no que se deslocou. A dependência do modelo diminui; cresce a dependência de quem guarda o significado do dado. O modelo semântico do Power BI, a ontologia do Fabric IQ, a Genie Ontology da Databricks, o modelo semântico de ativos da Datamint: cada plataforma está construindo o lugar onde passa a morar a definição do que é um ativo, uma falha, uma parada. É ali que décadas de conhecimento da sua operação vão ser escritas. Quem escreve no formato do fornecedor costuma descobrir o custo na hora de sair.

Há sinal bom. O IQ sharing da Microsoft aceita ontologias em RDF, padrão aberto do W3C — o tipo de compromisso que facilita levar o contexto embora. A mesma página informa que o suporte nativo, no IQ sharing, às ontologias do próprio Fabric IQ e aos modelos semânticos do Power BI ainda está no roadmap. Escrevemos isso trabalhando sobre a pilha da Microsoft: o retrato é de um mercado em que a portabilidade do significado ainda está sendo decidida, plataforma por plataforma, e quem decide cedo decide no contrato.

O CIO da Petrobras deu o outro lado do argumento. Se a inteligência mora em 1.800 sistemas legados, a primeira tarefa é tirá-la de lá sem perder nada no caminho. Migrar esse contexto para uma camada nova, num formato que só a camada nova lê, é trocar um cadeado velho por um novo.

Três perguntas separam contexto seu de contexto alugado. Primeira: onde fica escrita a definição dos meus ativos, e em que formato? Se for proprietário, peça o caminho de exportação por escrito. Segunda: se eu trocar de plataforma em três anos, a ontologia vai junto — com as relações e o histórico de mudanças — ou só as tabelas? Terceira: quem pode alterar uma definição, e essa alteração fica registrada como decisão, com autor e data?

E uma pergunta que não é para o fornecedor. Se o engenheiro que sabe por que aquela bomba é tratada como crítica sair amanhã, essa razão está escrita em algum lugar além da cabeça dele?

_Fonte: [Microsoft — New Microsoft data innovations unlock what only your business knows](https://blogs.microsoft.com/blog/2026/09/28/new-microsoft-data-innovations-unlock-what-only-your-business-knows/)_
_Fonte: [Microsoft Azure Blog — IQ sharing e ontologias RDF](https://azure.microsoft.com/en-us/blog/fabcon-and-sqlcon-2026-in-barcelona-building-the-data-foundation-for-microsoft-copilot-and-agents/)_
_Fonte: [Databricks — Genie Ontology (parceria com a Microsoft, 23/07)](https://www.databricks.com/company/newsroom/press-releases/databricks-and-microsoft-expand-partnership-help-enterprises-bring)_
_Fonte: [TI INSIDE Online — CIO da Petrobras](https://tiinside.com.br/02/09/2026/pessoas-processos-e-dados-sao-cruciais-para-sucesso-da-ia-afirma-cio-da-petrobras/)_

## Radar regulatório

### A UE adiou o prazo do alto risco, não a obrigação

O Digital Omnibus (Regulamento UE 2026/1744) entrou em vigor em 27 de julho e empurrou as obrigações dos sistemas de alto risco do Anexo III do AI Act — lista que inclui infraestrutura crítica — para 2 de dezembro de 2027. Os sistemas embutidos em produtos já regulados, do Anexo I, ficaram para 2 de agosto de 2028. As regras de transparência do Artigo 50 valem desde 2 de agosto de 2026.

**E daí:** Para quem opera infraestrutura crítica com cliente ou matriz na Europa, são 16 meses a mais para a avaliação de conformidade, e nenhum de pausa: a classificação não mudou, e o que for de alto risco em 2027 já é de alto risco no projeto de hoje. Contrato que cita "a data aplicável do AI Act" passou a apontar para o calendário novo — vale reler o que foi assinado entre maio e julho.

_Fonte: [Comissão Europeia — AI Act Service Desk](https://ai-act-service-desk.ec.europa.eu/en/ai-act/timeline/timeline-implementation-eu-ai-act) · 27/07/2026_


## Número do mês

- **70 mil b/d** — o que ganhos de eficiência operacional acrescentaram, aproximadamente, à produção da Petrobras no 2º trimestre de 2026, ante o mesmo período de 2025

_Fonte: [eixos](https://eixos.com.br/petroleo-e-gas/petroleiras-apostam-em-tecnologia-para-acelerar-novos-projetos-e-extrair-mais-oleo-de-campos-maduros/)_


---

**[Mapear onde mora o contexto da sua operação](https://neurocraft.ai/)**

---

## Cortes (não vai no e-mail)

- **neurocraft** — Regra do silêncio. Nenhum post da Neurocraft ou de Marcos Almeida datado de setembro foi encontrado; o mais recente é de 27/08.
- **neurocraft** — Publicado em 27/08, fora da janela, e trata de lançamentos que aguardam liberação de Guilherme Cleffe (decisão de 30/09: publicar em momento apropriado). Público no LinkedIn — a restrição é de timing, não de sigilo.
- **vexta** — Regra do silêncio. Últimos posts encontrados são de 18 e 23/08. Além disso, conteúdo da Vexta aguarda liberação de Guilherme Cleffe (30/09).
- **bizmetric** — Régua 9/12 (Impacto 1, Proximidade 2, Novidade 3, Evidência 3), mas reprovado na lente de relevância: expansão para a Austrália não muda decisão de leitor no Brasil ou nos EUA. Escrever um e daí aqui seria esticar.
- **bizmetric** — Presença em evento, sem fato novo para o leitor. Mesma lente do item acima.
- **datamint** — Post de terceiro no LinkedIn (fonte vetada) e sem fato novo: retoma a rodada de junho, já coberta em agosto.
- **datamint** — Publicado em 24/07, fora da janela. O número é de pilotos, sem cliente nem base divulgados: Evidência 1. Bom tema para deep dive de economia da decisão se houver caso documentado.
- **Databricks Data + AI World Tour São Paulo (16/09), com cerca de 4.000 líderes de dados e IA** — Público de evento de fornecedor não muda decisão do leitor. Novidade 3, Impacto 1.
- **TRACKFY | WAKECAP na ROG.e: 30% menos tempo de evacuação, ROI de até 9,3 vezes** — Números do próprio fornecedor em release, sem cliente nem base: Evidência 1. Reprovado.
- **SONDA leva IA, drones e visão computacional à ROG.e** — Lente 1: capacidade anunciada sem o contexto que a torna útil. Release, não notícia.
- **Petronemo segundo a Deloitte: 400 engenheiros de confiabilidade, economia estimada de R$ 20 milhões até 2029** — Página de case do fornecedor que construiu a solução, sem data. Usado só como contexto; os números não entram sem fonte da própria Petrobras.
- **Marco Legal da IA (PL 2338/2023) na Câmara** — Sem fato novo em setembro: segue aguardando parecer do relator. A declaração de que a votação fica para depois das eleições é de 24/08 e veio de fonte secundária. Reavaliar em novembro.
- **Presidente da Petrobras na ROG.e: exploração ativa e refino para até 100% do diesel nacional** — Fora do escopo da newsletter (Proximidade 0): estratégia de E&P e refino, sem dado nem decisão.
