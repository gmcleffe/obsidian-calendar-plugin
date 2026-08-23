# youtube_raw — histórico do YouTube → notas `0_RAW`

Pipeline que lê o export do Google Takeout e escreve uma nota Markdown por
vídeo assistido, na pasta `0_RAW` do vault. Cada nota traz metadados no
frontmatter, a transcrição literal e um andaime vazio para o ciclo Karpathy
(assistir → reimplementar do zero → comparar → explicar).

O agente `youtube-raw` (`.claude/agents/youtube-raw.md`) opera este pipeline em
linguagem natural. Este README é para rodar na mão.

## Por que Takeout e não a API

A YouTube Data API não expõe histórico de reprodução desde 2016. Playlists
(`Assistir mais tarde`, `Curtidos`) até dá, o histórico não. Takeout é o
caminho.

1. https://takeout.google.com → **Desmarcar tudo** → marcar **YouTube**
2. "Todos os dados do YouTube incluídos" → deixar só **histórico**
3. "Vários formatos" → Histórico: **JSON** (o HTML também é lido, mas a data
   depende do locale e pode sair vazia)
4. Exportar e descompactar

O arquivo é `watch-history.json` (`histórico-de-visualização.json` em pt-BR).

## Uso

```bash
# sempre comece por aqui
python3 -m tools.youtube_raw \
  --takeout ~/Takeout/YouTube\ e\ YouTube\ Music/histórico \
  --vault ~/Obsidian/MeuVault \
  --since 2026-01-01 \
  --dry-run

# valendo
python3 -m tools.youtube_raw \
  --takeout ~/Takeout/YouTube\ e\ YouTube\ Music/histórico \
  --vault ~/Obsidian/MeuVault \
  --since 2026-01-01 --limit 20
```

`--takeout` aceita o arquivo ou a pasta (procura `watch-history.*` recursivamente).
Rode da raiz do repositório. `--help` lista todas as opções.

### Filtros úteis

| Flag | Efeito |
| --- | --- |
| `--since` / `--until` | janela de datas em que o vídeo foi assistido |
| `--channel` / `--exclude-channel` | substring do nome do canal, repetível |
| `--match REGEX` | regex aplicada ao título |
| `--video-id ID` | processa só esses IDs, repetível |
| `--min-duration SEGUNDOS` | descarta clipes curtos (precisa de `--api-key`) |
| `--limit N` | teto de segurança |

### Subpastas por playlist

O Takeout traz `playlists/*.csv`. O pipeline usa os nomes das playlists como
subpastas e o pertencimento real como classificação — encontrado sozinho ao
lado do histórico.

| Flag | Efeito |
| --- | --- |
| `--playlists PATH` | aponta a pasta `playlists` manualmente |
| `--no-auto-playlists` | desliga a busca automática |
| `--list-playlists` | lista as playlists encontradas e sai |
| `--rules FILE` | `{"IA": ["llm", "transformer"]}` para quem não está em playlist |
| `--assign-file FILE` | `{"<video_id>": "<Pasta>"}`, decisões explícitas, vence tudo |
| `--list-unclassified FILE` | grava os vídeos sem pasta em JSON, para classificar e devolver |

Prioridade: `--assign-file` > playlist > `--rules` > raiz. `Watch later`,
`Likes` e `Favoritos` são ignoradas — são caixa de entrada, não assunto.

Com `--update`, um vídeo reclassificado tem a nota **movida** para a pasta
nova (texto preservado), não duplicada.

### Enriquecimento

| Fonte | Traz | Requisito |
| --- | --- | --- |
| Takeout | título, canal, quando assistiu | — |
| oEmbed | título canônico, canal, thumbnail | rede |
| Data API v3 | duração, descrição, tags, data de publicação | `YOUTUBE_API_KEY` ou `--api-key` |
| youtube-transcript-api | transcrição com timestamps | `pip install -r tools/youtube_raw/requirements.txt` |

Tudo degrada: sem chave cai para oEmbed, sem rede cai para o Takeout, sem o
pacote de transcrição a nota sai sem essa seção. `--offline` desliga a rede.

## Reexecuções não destroem seu texto

O que você escreve fica **fora** do bloco delimitado por
`<!-- yt-raw:auto:start -->` / `<!-- yt-raw:auto:end -->`, e só esse bloco é
regerado.

- padrão: vídeo já registrado é **pulado**
- `--update`: regera o bloco automático, preserva seu texto e os campos
  `tags`, `aliases`, `status`, `rating`, `karpathy_stage`, `processed`,
  `created` e qualquer chave que você tenha adicionado ao frontmatter
- `--force`: reescreve a nota inteira e **descarta o que você escreveu**

O registro fica em `0_RAW/.youtube-raw.state.json` (dotfile, o Obsidian ignora).
Apagou uma nota de propósito? Ela continua no registro e não volta — para
recriar, `--video-id <ID> --update`.

## Anatomia da nota

```
---
title, type, source, video_id, url, channel, channel_url,
published, watched, watched_first, watch_count,
duration, duration_seconds, language, transcript, thumbnail,
metadata_source, tags, karpathy_stage, status, rating, processed, created
---

# Título
## 🔁 Ciclo Karpathy      ← checklist das 5 etapas
## ⚡ Resumo em 3 linhas   ┐
## 🧠 Conceitos-chave      │
## 🔨 Reimplementar do zero├ seu trabalho, nunca sobrescrito
## ❓ Perguntas abertas     │
## ⏱️ Momentos             │
## 🔗 Conexões             ┘
---
<!-- yt-raw:auto:start -->
## 📄 Fonte bruta          ← ficha, descrição e transcrição; regerado
<!-- yt-raw:auto:end -->
```

Fila de estudo no Obsidian:

````markdown
```dataview
TABLE channel, duration, watched
FROM "0_RAW"
WHERE source = "youtube" AND processed = false
SORT watched DESC
```
````

## Testes

```bash
python3 -m unittest discover -s tools/youtube_raw/tests -t .
```

Só stdlib, sem rede.

## Limites conhecidos

- `watch-history.json` é lido inteiro na memória. Históricos muito grandes
  (centenas de MB) pedem uma máquina com folga.
- Vídeos removidos, privados e anúncios não têm `/watch?v=` no Takeout e são
  descartados.
- O histórico do YouTube Music vem em arquivo separado e é ignorado.
- Transcrição depende de o vídeo ter legenda; muitos não têm.
