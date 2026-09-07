"""Download e formatacao de transcricoes.

Depende de `youtube-transcript-api`, que e opcional: sem o pacote (ou sem
rede) a nota e gerada mesmo assim, apenas sem a secao de transcricao.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Sequence, Tuple

from .util import fmt_timestamp


@dataclass
class Transcript:
    video_id: str
    language: Optional[str] = None
    generated: Optional[bool] = None
    segments: List[dict] = field(default_factory=list)

    def __bool__(self) -> bool:
        return bool(self.segments)


def _normalize(raw: Iterable) -> List[dict]:
    """Aceita dicts (API 0.x) e objetos FetchedTranscriptSnippet (API 1.x)."""
    segments = []
    for item in raw:
        if isinstance(item, dict):
            start, text = item.get("start", 0.0), item.get("text", "")
        else:
            start, text = getattr(item, "start", 0.0), getattr(item, "text", "")
        text = " ".join(str(text).split())
        if text:
            segments.append({"start": float(start), "text": text})
    return segments


def fetch_transcript(
    video_id: str, languages: Sequence[str] = ("pt", "pt-BR", "en")
) -> Optional[Transcript]:
    """Prefere legenda manual no idioma pedido; cai para gerada, depois qualquer uma."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return None

    listing = None
    try:
        # API >= 1.0 (baseada em instancia).
        api = YouTubeTranscriptApi()
        listing = api.list(video_id)
    except AttributeError:
        pass
    except Exception:
        return None

    if listing is None:
        try:
            listing = YouTubeTranscriptApi.list_transcripts(video_id)  # API 0.x
        except Exception:
            return None

    wanted = list(languages)
    candidate = None
    for finder in ("find_manually_created_transcript", "find_generated_transcript"):
        try:
            candidate = getattr(listing, finder)(wanted)
            break
        except Exception:
            continue
    if candidate is None:
        candidate = next(iter(listing), None)
    if candidate is None:
        return None

    try:
        fetched = candidate.fetch()
    except Exception:
        return None

    raw = fetched.to_raw_data() if hasattr(fetched, "to_raw_data") else fetched
    segments = _normalize(raw)
    if not segments:
        return None

    return Transcript(
        video_id=video_id,
        language=getattr(candidate, "language_code", None),
        generated=getattr(candidate, "is_generated", None),
        segments=segments,
    )


def group_segments(
    segments: Sequence[dict], window: float = 45.0
) -> List[Tuple[float, str]]:
    """Junta legendas curtas em paragrafos de ~`window` segundos."""
    if not segments:
        return []

    paragraphs: List[Tuple[float, str]] = []
    start = segments[0]["start"]
    buffer: List[str] = []

    for segment in segments:
        if buffer and segment["start"] - start >= window:
            paragraphs.append((start, " ".join(buffer)))
            start, buffer = segment["start"], []
        buffer.append(segment["text"])

    if buffer:
        paragraphs.append((start, " ".join(buffer)))
    return paragraphs


def render_transcript(transcript: Transcript, video_id: str, window: float = 45.0) -> str:
    """Paragrafos com timestamp clicavel que abre o video no ponto certo."""
    lines = []
    for start, text in group_segments(transcript.segments, window):
        link = f"https://youtu.be/{video_id}?t={int(start)}"
        lines.append(f"**[{fmt_timestamp(start)}]({link})** {text}")
    return "\n\n".join(lines)
