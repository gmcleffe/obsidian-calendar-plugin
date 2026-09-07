---
name: YTtoMD
description: Exporta o histórico do YouTube para notas .md no vault do Google Drive, escreve um diagnóstico do lote (o que ensina, e os gaps contra os objetivos declarados) e cria um evento de 1h no Google Agenda com o diagnóstico anexo. Use quando o usuário pedir /YTtoMD, "processar meus vídeos", "exportar o YouTube", "atualizar o 0_RAW" ou "diagnóstico do que assisti".
---

Uma execução = um lote = um evento. Cada vez que este skill roda, ele processa
só os vídeos novos desde a última vez, escreve **um** diagnóstico e cria **um**
evento de 1h no horário em que você acionou.

## Configuração

Leia `.claude/skills/YTtoMD/config.json`. Se não existir, crie a partir de
`config.example.json` perguntando os caminhos ao usuário. Campos:

| Campo | O que é |
| --- | --- |
| `takeout` | pasta `YouTube and YouTube Music` do Takeout descompactado |
| `vault` | raiz no Drive, ex.: `G:/Meu Drive/0_RAW/Youtube` |
| `raw_dir` | subpasta das notas, ex.: `Notas` |
| `drive_folder_id` | id da pasta do Drive onde o diagnóstico é gravado |
| `objetivos` | caminho do arquivo de objetivos |
| `timezone` | ex.: `America/Sao_Paulo` |

`drive_folder_id`: resolva uma vez com `Google_Drive search_files`
(`title = 'Youtube' and mimeType = 'application/vnd.google-apps.folder'`) e
grave no config. Não resolva de novo a cada execução.

## Passo 1 — objetivos (obstrutivo)

Leia o arquivo de `objetivos`. **Sem ele não há diagnóstico**: "gaps" só
significa alguma coisa contra um alvo declarado. Se não existir, copie
`OBJETIVOS-template.md` para lá, diga ao usuário que precisa ser preenchido, e
**pare**. Não invente objetivos por ele, e não siga adiante sem eles.

## Passo 2 — captura

```bash
python -m tools.youtube_raw \
  --takeout "<takeout>" --vault "<vault>" --raw-dir "<raw_dir>" \
  --rules "<vault>/<raw_dir>/_regras-classificacao.json" \
  --report "<scratch>/relatorio.md"
```

O ledger cuida de só pegar o que é novo. Se o usuário passou `--since`,
`--limit` ou `--folder` no comando, repasse.

**Se não houver vídeo novo: pare aqui.** Diga isso e não crie evento. Um evento
vazio na agenda é lixo.

## Passo 3 — ler o lote

Leia as notas criadas (o relatório lista os nomes). De cada uma pegue título,
canal, categoria e a transcrição, se houver.

Anote quantas têm transcrição. Isso governa o passo seguinte.

## Passo 4 — o diagnóstico

Você escreve, lendo as notas e os objetivos. Não chame API nenhuma.

Grave em `<vault>/<raw_dir>/_Diagnosticos/YYYY-MM-DD HHMM — Diagnóstico.md`,
com esta estrutura:

```markdown
---
type: diagnostico/youtube
gerado: <ISO 8601>
videos: <n>
com_transcricao: <n>
---

# Diagnóstico — <n> vídeos

## O que este lote ensina
(3 a 6 bullets. O que o CONJUNTO ensina, não resumo vídeo a vídeo.)

## Onde isso toca seus objetivos
(Por objetivo declarado: o que deste lote avança nele, com [[link para a nota]].
Objetivo que o lote não tocou: diga "nada neste lote".)

## Gaps
(O que seus objetivos exigem e este lote NÃO cobre. Pré-requisitos que os
vídeos assumem e não explicam. Concreto e verificável, nunca genérico.)

## Próximo passo
(Uma ação. A menor coisa que fecha o gap mais caro.)

## Notas deste lote
(Lista com [[wikilinks]], agrupada por pasta.)
```

Regras de honestidade, e elas mandam mais que a vontade de entregar algo bonito:

- **Sem transcrição, sem afirmação sobre conteúdo.** Com título e canal você
  sabe o TEMA, não o que foi dito. Diga isso explicitamente: "N de M notas sem
  transcrição — o diagnóstico abaixo cobre só as M com". Nunca resuma um vídeo
  pelo título.
- **Gap é falta observada, não palpite sobre o usuário.** "Seus objetivos citam
  avaliação de agentes; nenhum dos 12 vídeos trata de eval" é um gap. "Você
  provavelmente tem dificuldade com X" não é.
- Se o lote inteiro estiver sem transcrição, o diagnóstico vira um mapa de temas
  e você diz isso no título da seção. É honesto e ainda útil.

## Passo 5 — Google Drive

Suba o diagnóstico com `Google_Drive create_file`:

- `parentId`: o `drive_folder_id` do config
- `textContent`: o markdown
- `contentMimeType`: `text/markdown`
- `disableConversionToGoogleType`: **`true`** — sem isso o Drive converte para
  Google Docs e você perde o markdown e a extensão `.md`
- `title`: o mesmo nome do arquivo

Guarde a URL que voltar: é ela que vira o anexo. O Drive Desktop sincroniza o
arquivo para `G:` sozinho, então ele aparece no Obsidian também — um arquivo só,
nos dois lugares. Não grave uma segunda cópia local.

## Passo 6 — Google Agenda

`Google_Calendar create_event`:

- `summary`: `📺 YouTube → Obsidian — <n> vídeos`
- `startTime`: **agora**, no timezone do config
- `endTime`: agora + 1 hora
- `description`: "O que este lote ensina", "Gaps" e "Próximo passo" do
  diagnóstico, em HTML (`<b>`, `<ul>`, `<li>` funcionam; markdown não renderiza)
- `attachments`: `[{fileUrl: <url do passo 5>, title: <nome do arquivo>}]`
- `availability`: `AVAILABILITY_FREE` — é registro, não compromisso; não deve
  te marcar como ocupado
- `eventType`: `DEFAULT`

Se o `create_file` falhar, **crie o evento mesmo assim**, sem anexo, com o
diagnóstico na descrição, e diga ao usuário que o anexo faltou. Perder o anexo
é aceitável; perder o diagnóstico não.

## Passo 7 — relatar

Diga: quantas notas novas, em que pastas, quantas sem transcrição, o link do
evento e o do diagnóstico. Se algum passo falhou, diga qual e o que ficou de
fora.

## Nunca

- Criar evento quando não houve vídeo novo.
- Criar evento sem ter gravado o diagnóstico antes.
- Escrever resumo de vídeo sem transcrição.
- Rodar com `--force` na captura — descarta o que o usuário escreveu nas notas.
- Inventar objetivo para preencher a seção de gaps.
