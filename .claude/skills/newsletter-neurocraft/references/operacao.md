# Operação da newsletter

Como rodar isto todo mês sem que vire dívida.

## Calendário do ciclo

Com envio no **dia 5** (configurável em `config/marcas.json`):

| Quando | O quê | Quem |
|---|---|---|
| Dia 1 | Agente abre a edição e apura (fases 1–2) | Agente |
| Dia 2 | Pontuação e corte; pauta fechada (fase 3) | Agente + editor |
| Dia 2 | **Aprovação de citações de cliente** | Editor humano |
| Dia 3 | Redação, validação, render (fases 4–5) | Agente |
| Dia 4 | Revisão humana do rascunho; teste de entrega | Editor humano |
| Dia 5 | Envio | Editor humano |
| Dia 12 | Leitura de métricas; itens salvos para o mês seguinte | Editor |

O gargalo real não é escrever — é a aprovação de citação de cliente. Puxe-a para o dia 2 e o
ciclo inteiro cabe em cinco dias.

## Papéis

- **Agente** — apura, pontua, escreve, valida, renderiza, cria o rascunho. Não envia.
- **Editor** (Guilherme) — decide cortes polêmicos, aprova citação de cliente, aperta enviar.
- **Aprovador de conta** — quando a edição cita cliente nominalmente, o dono da conta confirma
  por escrito. Sem isso, o nome sai.

## Automação mensal

Agendar um disparo mensal que abra a edição sozinha (dia 1, 09h em São Paulo → 12h UTC):

```
cron: 0 12 1 * *
```

Duas formas, e a escolha importa:

- **Sessão nova a cada disparo** — a produção começa limpa todo mês, sem contexto acumulado.
  É a opção certa aqui. O prompt do agendamento precisa ser autossuficiente: "rode a skill
  `newsletter-neurocraft` para o mês anterior e me entregue o rascunho".
- **Sessão persistente** — só se você quiser continuidade editorial entre edições. Custa
  contexto e tende a repetir ângulo. Não recomendado para conteúdo.

O agendamento **nunca** deve ter permissão de envio de e-mail. Rascunho é o teto.

## Lista e entregabilidade

O que arruína newsletter B2B, em ordem de frequência:

1. **Domínio sem autenticação.** SPF, DKIM e DMARC configurados no `neurocraft.ai` antes do
   primeiro envio em volume. Sem isso, a edição vai para spam e você nunca descobre.
2. **Enviar da conta pessoal.** Disparo em massa por Gmail comum queima o domínio. Use
   ferramenta de envio dedicada; o Gmail aqui é só onde o rascunho é revisado.
3. **Lista comprada.** Além do risco jurídico, destrói a taxa de entrega. Base própria: clientes,
   parceiros, contatos de reunião com consentimento registrado.
4. **Sem descadastro visível.** Exigência de LGPD (base legal, finalidade, revogação simples)
   e de CAN-SPAM para os contatos nos EUA. O rodapé do template já tem os dois links —
   substitua os marcadores `%%unsubscribe_url%%` e `%%preferences_url%%` pelos da ferramenta.
5. **Higiene.** Remova hard bounce no mesmo ciclo. Contato sem abrir seis edições seguidas sai
   ou vai para uma cadência trimestral.

## Segmentação — quando, e não antes

Comece com **uma lista só**. Segmentar cedo multiplica trabalho e mata a cadência. Divida por
setor (energia/O&G, manufatura, saneamento, saúde, público) só quando as duas coisas forem
verdade: mais de 500 contatos ativos **e** conteúdo específico suficiente para diferenciar de
fato as edições. Antes disso, a personalização mora no corpo do texto, não na lista.

## Reaproveitamento

Cada edição rende, sem trabalho novo relevante:
- 3 a 5 posts de LinkedIn (um por item aprovado, com o "e daí" como abertura).
- 1 artigo no site a partir do deep dive.
- Material de conversa para o time comercial — o "e daí" é literalmente um abridor de reunião.

Faça isso **depois** do envio. Publicar antes tira do assinante o motivo de abrir o e-mail.

## WhatsApp: canal de reaproveitamento, não de envio

79% dos times brasileiros prospectam por WhatsApp, à frente de e-mail (52%), ligação (37%) e
LinkedIn (16%) — Panorama do GTM no Brasil 2026, HubSpot. Isso **não** significa disparar a
newsletter por lá: para C-level, envio mensal não solicitado em WhatsApp queima a relação mais
rápido do que constrói lista, e a régua de consentimento é mais dura que a do e-mail.

O que significa: o item que mais interessa a cada conta vira **uma mensagem de uma linha, enviada
individualmente por quem já tem a conversa aberta**, com o link da edição. É o oposto de disparo —
é o "e daí" usado como abridor de conversa, um a um. Essa é a leitura correta do dado para B2B
de ticket alto.

Se em algum momento houver lista com opt-in explícito para WhatsApp, trate como canal próprio,
com formato próprio e frequência menor. Nunca como espelho do e-mail.

## Primeiros 90 dias

- **Mês 1** — envie mesmo curto. Duas marcas e três itens fortes já servem. O objetivo é
  estabelecer a cadência, não impressionar.
- **Mês 2** — meça resposta, não abertura. Ligue para dois que responderam e pergunte o que
  leram até o fim.
- **Mês 3** — corte a seção que ninguém clicou. Newsletter melhora por subtração.

Depois do terceiro ciclo, revise `linha-editorial.md` com o que a prática mostrou. A régua
inicial é um chute educado; os dados dos três primeiros meses valem mais que ela.
