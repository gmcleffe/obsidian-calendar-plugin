"""Montagem da nota Markdown e merge nao-destrutivo com notas ja existentes.

O arquivo tem duas metades:

* tudo antes de `<!-- yt-raw:auto:start -->` pertence a voce e nunca e
  sobrescrito numa reexecucao;
* o bloco entre os marcadores (ficha, descricao, transcricao) e regerado.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Dict, List, Optional, Sequence, Tuple

from .metadata import VideoMeta
from .takeout import WatchRecord
from .transcript import Transcript, render_transcript
from .util import fmt_duration, slugify, tag_slug, yaml_list, yaml_scalar

AUTO_START = "<!-- yt-raw:auto:start -->"
AUTO_END = "<!-- yt-raw:auto:end -->"

# Sentinela para campos que nascem vazios de proposito (ex.: `rating:`).
_EMPTY = object()

# Campos que voce edita a mao e que uma reexecucao nunca deve pisar.
PRESERVED_KEYS = (
    "tags",
    "aliases",
    "status",
    "rating",
    "karpathy_stage",
    "processed",
    "created",
)

KARPATHY_CYCLE = """## 🔁 Ciclo Karpathy

- [ ] 1. Assistir inteiro, sem pausar — pegar o mapa geral
- [ ] 2. Reassistir anotando os conceitos-chave abaixo
- [ ] 3. Reimplementar do zero, sem olhar o material
- [ ] 4. Comparar com o original e listar cada diferença
- [ ] 5. Explicar com as próprias palavras numa nota permanente
"""

HUMAN_TEMPLATE = """# {title}

{cycle}
## ⚡ Resumo em 3 linhas

- 
- 
- 

## 🧠 Conceitos-chave

- 

## 🔨 Reimplementar do zero

- [ ] 

## ❓ Perguntas abertas

- 

## ⏱️ Momentos que valem revisitar

- 

## 🔗 Conexões

- [[ ]]
"""


def _fmt_date(value: Optional[datetime]) -> Optional[str]:
    return value.date().isoformat() if value else None


def build_filename(
    meta: VideoMeta, record: WatchRecord, template: str = "{date} {title} ({video_id})"
) -> str:
    date = _fmt_date(record.last_watched) or _fmt_date(meta.published_at) or ""
    name = template.format(
        date=date,
        title=slugify(meta.title or record.video_id),
        video_id=meta.video_id,
        channel=slugify(meta.channel or ""),
    )
    return slugify(name, max_len=120) + ".md"


def build_frontmatter(
    meta: VideoMeta,
    record: WatchRecord,
    transcript: Optional[Transcript],
    base_tags: Sequence[str],
    channel_tag: bool = True,
    now: Optional[datetime] = None,
    category: Optional[str] = None,
    playlists: Sequence[str] = (),
) -> List[Tuple[str, List[str]]]:
    tags = list(base_tags)
    if channel_tag and meta.channel:
        tags.append(f"canal/{tag_slug(meta.channel)}")
    if category:
        tags.append(f"tema/{tag_slug(category)}")

    fields: List[Tuple[str, object]] = [
        ("title", yaml_scalar(meta.title)),
        ("type", yaml_scalar("source/video")),
        ("source", yaml_scalar("youtube")),
        ("video_id", yaml_scalar(meta.video_id)),
        ("url", yaml_scalar(record.url)),
        ("channel", yaml_scalar(meta.channel) if meta.channel else None),
        ("channel_url", yaml_scalar(meta.channel_url) if meta.channel_url else None),
        ("published", _fmt_date(meta.published_at)),
        ("watched", _fmt_date(record.last_watched)),
        (
            "watched_first",
            _fmt_date(record.first_watched)
            if record.watch_count > 1
            else None,
        ),
        ("watch_count", str(record.watch_count) if record.watch_count else None),
        (
            "duration",
            yaml_scalar(fmt_duration(meta.duration_seconds))
            if meta.duration_seconds
            else None,
        ),
        (
            "duration_seconds",
            str(meta.duration_seconds) if meta.duration_seconds else None,
        ),
        (
            "language",
            yaml_scalar(transcript.language if transcript else meta.language)
            if (transcript and transcript.language) or meta.language
            else None,
        ),
        ("transcript", "true" if transcript else "false"),
        ("thumbnail", yaml_scalar(meta.thumbnail) if meta.thumbnail else None),
        ("metadata_source", yaml_scalar(meta.source)),
        ("category", yaml_scalar(category) if category else None),
        ("playlists", yaml_list(playlists) if playlists else None),
        ("tags", yaml_list(tags)),
        ("karpathy_stage", yaml_scalar("1-capture")),
        ("status", yaml_scalar("raw")),
        ("rating", _EMPTY),
        ("processed", "false"),
        ("created", _fmt_date(now or datetime.now())),
    ]

    entries: List[Tuple[str, List[str]]] = []
    for key, value in fields:
        if value is _EMPTY:
            entries.append((key, [f"{key}:"]))  # campo em branco para voce preencher
        elif value not in (None, ""):
            entries.append((key, [f"{key}: {value}"]))
    return entries


def render_frontmatter(entries: Sequence[Tuple[str, List[str]]]) -> str:
    lines = ["---"]
    for _, raw in entries:
        lines.extend(raw)
    lines.append("---")
    return "\n".join(lines) + "\n"


def build_auto_block(
    meta: VideoMeta,
    record: WatchRecord,
    transcript: Optional[Transcript],
    transcript_window: float = 45.0,
) -> str:
    channel = (
        f"[{meta.channel}]({meta.channel_url})"
        if meta.channel and meta.channel_url
        else (meta.channel or "—")
    )
    watched = _fmt_date(record.last_watched) or "—"
    if record.watch_count > 1:
        watched += f" ({record.watch_count}× — desde {_fmt_date(record.first_watched)})"

    ficha = [
        "> [!info]- Ficha do vídeo",
        f"> **Canal:** {channel}",
        f"> **Assistido:** {watched}",
        f"> **Publicado:** {_fmt_date(meta.published_at) or '—'}",
        f"> **Duração:** {fmt_duration(meta.duration_seconds) or '—'}",
        f"> **Link:** {record.url}",
    ]

    parts = [AUTO_START, "## 📄 Fonte bruta", "", "\n".join(ficha), ""]

    if meta.description:
        parts += [
            "### Descrição do vídeo",
            "",
            "> [!quote]- Descrição original",
            "\n".join(f"> {line}" for line in meta.description.splitlines()),
            "",
        ]

    parts.append("### Transcrição")
    parts.append("")
    if transcript:
        origem = "automática" if transcript.generated else "manual"
        parts.append(
            f"*Legenda {origem} em `{transcript.language or '?'}` — "
            f"{len(transcript.segments)} trechos.*"
        )
        parts.append("")
        parts.append(render_transcript(transcript, meta.video_id, transcript_window))
    else:
        parts.append(
            "*Transcrição indisponível — o vídeo não tem legendas, "
            "`youtube-transcript-api` não está instalado ou não houve rede.*"
        )
    parts += ["", AUTO_END]
    return "\n".join(parts).rstrip() + "\n"


def build_note(
    meta: VideoMeta,
    record: WatchRecord,
    transcript: Optional[Transcript],
    base_tags: Sequence[str],
    channel_tag: bool = True,
    transcript_window: float = 45.0,
    now: Optional[datetime] = None,
    category: Optional[str] = None,
    playlists: Sequence[str] = (),
) -> str:
    frontmatter = render_frontmatter(
        build_frontmatter(
            meta, record, transcript, base_tags, channel_tag, now, category, playlists
        )
    )
    human = HUMAN_TEMPLATE.format(title=meta.title or meta.video_id, cycle=KARPATHY_CYCLE)
    auto = build_auto_block(meta, record, transcript, transcript_window)
    return f"{frontmatter}\n{human}\n---\n\n{auto}"


_FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n?", re.DOTALL)
_KEY_LINE = re.compile(r"^([A-Za-z_][\w-]*):")


def split_frontmatter(text: str) -> Tuple[List[Tuple[str, List[str]]], str]:
    """Separa o frontmatter em pares (chave, linhas cruas) e devolve o corpo.

    Guardamos as linhas cruas de proposito: assim um valor escrito a mao
    volta para o arquivo exatamente como estava.
    """
    match = _FRONTMATTER.match(text)
    if not match:
        return [], text

    entries: List[Tuple[str, List[str]]] = []
    for line in match.group(1).splitlines():
        key_match = _KEY_LINE.match(line)
        if key_match:
            entries.append((key_match.group(1), [line]))
        elif entries:
            entries[-1][1].append(line)  # continuacao (lista ou bloco)
    return entries, text[match.end() :]


def merge_note(existing: str, generated: str) -> str:
    """Regera o bloco automatico preservando texto e frontmatter editados."""
    old_fm, old_body = split_frontmatter(existing)
    new_fm, new_body = split_frontmatter(generated)

    old_by_key: Dict[str, List[str]] = {key: raw for key, raw in old_fm}
    merged_fm: List[Tuple[str, List[str]]] = []
    for key, raw in new_fm:
        if key in PRESERVED_KEYS and key in old_by_key:
            merged_fm.append((key, old_by_key[key]))
        else:
            merged_fm.append((key, raw))
    known = {key for key, _ in new_fm}
    merged_fm.extend((key, raw) for key, raw in old_fm if key not in known)

    start = old_body.find(AUTO_START)
    end = old_body.find(AUTO_END)
    new_auto = new_body[new_body.find(AUTO_START) :].rstrip() + "\n"

    if start == -1 or end == -1 or end < start:
        # Nota sem marcadores (criada a mao?): anexa o bloco no fim.
        body = old_body.rstrip() + "\n\n" + new_auto
    else:
        body = old_body[:start] + new_auto + old_body[end + len(AUTO_END) :].rstrip("\n")
        body = body.rstrip() + "\n"

    separator = "" if body.startswith("\n") else "\n"
    return render_frontmatter(merged_fm) + separator + body
