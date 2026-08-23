"""Leitura do historico de reproducao exportado pelo Google Takeout.

O Takeout entrega `watch-history.json` (preferido) ou `watch-history.html`.
O JSON tem data confiavel e o HTML depende do locale da exportacao, entao o
JSON e sempre a melhor entrada.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional

from .util import parse_datetime

# Prefixos que o Takeout adiciona ao titulo, por locale.
_WATCHED_PREFIXES = (
    "Watched ",
    "Assistiu a ",
    "Assistiu ",
    "Você assistiu a ",
    "Viste ",
    "Has visto ",
    "Ha visto ",
    "Vous avez regardé ",
    "Hai guardato ",
    "Bekeken ",
    "Angesehen: ",
)

_VIDEO_ID = re.compile(
    r"(?:youtube\.com/(?:watch\?(?:.*&)?v=|shorts/|live/|embed/|v/)|youtu\.be/)"
    r"(?P<id>[A-Za-z0-9_-]{11})"
)


def extract_video_id(url: Optional[str]) -> Optional[str]:
    """Devolve o ID de 11 caracteres de qualquer forma de URL do YouTube."""
    if not url:
        return None
    match = _VIDEO_ID.search(url)
    return match.group("id") if match else None


def strip_watched_prefix(title: str) -> str:
    for prefix in _WATCHED_PREFIXES:
        if title.startswith(prefix):
            return title[len(prefix) :].strip()
    return title.strip()


@dataclass
class WatchRecord:
    """Um video do historico, com todas as vezes que foi assistido agregadas."""

    video_id: str
    url: str
    title: str = ""
    channel: Optional[str] = None
    channel_url: Optional[str] = None
    watched_at: List[datetime] = field(default_factory=list)

    @property
    def watch_count(self) -> int:
        return len(self.watched_at)

    @property
    def first_watched(self) -> Optional[datetime]:
        return min(self.watched_at) if self.watched_at else None

    @property
    def last_watched(self) -> Optional[datetime]:
        return max(self.watched_at) if self.watched_at else None

    def merge(self, other: "WatchRecord") -> None:
        self.watched_at.extend(other.watched_at)
        # A primeira ocorrencia costuma ser a mais recente e a mais completa.
        self.title = self.title or other.title
        self.channel = self.channel or other.channel
        self.channel_url = self.channel_url or other.channel_url


def _is_ad(entry: dict) -> bool:
    details = entry.get("details") or []
    return any("Ads" in (item.get("name") or "") for item in details)


def parse_json_history(path: Path) -> Iterator[WatchRecord]:
    """Itera entradas de `watch-history.json`, ignorando anuncios e buscas."""
    with path.open("r", encoding="utf-8") as handle:
        entries = json.load(handle)
    if not isinstance(entries, list):
        raise ValueError(f"{path} nao contem uma lista de eventos do Takeout")

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("header") not in (None, "YouTube"):
            continue
        if _is_ad(entry):
            continue
        video_id = extract_video_id(entry.get("titleUrl"))
        if not video_id:
            # Buscas, videos removidos e privados nao tem /watch?v=.
            continue

        subtitles = entry.get("subtitles") or []
        channel = subtitles[0].get("name") if subtitles else None
        channel_url = subtitles[0].get("url") if subtitles else None
        watched = parse_datetime(entry.get("time") or "")

        yield WatchRecord(
            video_id=video_id,
            url=f"https://www.youtube.com/watch?v={video_id}",
            title=strip_watched_prefix(entry.get("title") or ""),
            channel=channel,
            channel_url=channel_url,
            watched_at=[watched] if watched else [],
        )


class _HistoryHTMLParser(HTMLParser):
    """Extrai os blocos `content-cell` do watch-history.html."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.cells: List[dict] = []
        self._depth = 0
        self._cell: Optional[dict] = None
        self._href: Optional[str] = None

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = dict(attrs)
        if tag == "div":
            classes = attributes.get("class", "")
            if self._cell is None and "content-cell" in classes and "mdl-typography--body-1" in classes:
                self._cell = {"links": [], "text": []}
                self._depth = 1
                return
            if self._cell is not None:
                self._depth += 1
        elif tag == "a" and self._cell is not None:
            self._href = attributes.get("href")

    def handle_endtag(self, tag: str) -> None:
        if self._cell is None:
            return
        if tag == "a":
            self._href = None
        elif tag == "div":
            self._depth -= 1
            if self._depth == 0:
                self.cells.append(self._cell)
                self._cell = None

    def handle_data(self, data: str) -> None:
        if self._cell is None:
            return
        text = data.replace("\xa0", " ").strip()
        if not text:
            return
        if self._href:
            self._cell["links"].append((self._href, text))
        else:
            self._cell["text"].append(text)


_HTML_DATE_FORMATS = (
    "%b %d, %Y, %I:%M:%S %p",
    "%d de %b. de %Y, %H:%M:%S",
    "%d/%m/%Y %H:%M:%S",
    "%d.%m.%Y, %H:%M:%S",
)


def _parse_html_date(text: str) -> Optional[datetime]:
    """Best effort: o formato depende do locale da exportacao."""
    cleaned = re.sub(r"\s+(?:GMT|UTC)[+-]?\d*(?::\d+)?$", "", text).strip()
    for fmt in _HTML_DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
    return None


def parse_html_history(path: Path) -> Iterator[WatchRecord]:
    parser = _HistoryHTMLParser()
    parser.feed(unescape(path.read_text(encoding="utf-8", errors="replace")))
    parser.close()

    for cell in parser.cells:
        video_link = next(
            ((href, text) for href, text in cell["links"] if extract_video_id(href)),
            None,
        )
        if not video_link:
            continue
        video_id = extract_video_id(video_link[0])
        channel_link = next(
            (
                (href, text)
                for href, text in cell["links"]
                if "/channel/" in href or "/@" in href or "/user/" in href
            ),
            None,
        )
        watched = None
        for chunk in reversed(cell["text"]):
            watched = _parse_html_date(chunk)
            if watched:
                break

        yield WatchRecord(
            video_id=video_id,
            url=f"https://www.youtube.com/watch?v={video_id}",
            title=strip_watched_prefix(video_link[1]),
            channel=channel_link[1] if channel_link else None,
            channel_url=channel_link[0] if channel_link else None,
            watched_at=[watched] if watched else [],
        )


def load_history(path: Path) -> Iterator[WatchRecord]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return parse_json_history(path)
    if suffix in (".html", ".htm"):
        return parse_html_history(path)
    raise ValueError(
        f"formato nao suportado: {path.name} (esperado watch-history.json ou .html)"
    )


def aggregate(records: Iterable[WatchRecord]) -> List[WatchRecord]:
    """Colapsa reexibicoes: um video vira uma nota com watch_count > 1."""
    merged: Dict[str, WatchRecord] = {}
    for record in records:
        existing = merged.get(record.video_id)
        if existing is None:
            merged[record.video_id] = record
        else:
            existing.merge(record)
    ordered = sorted(
        merged.values(),
        key=lambda item: (item.last_watched is not None, item.last_watched),
        reverse=True,
    )
    return ordered
