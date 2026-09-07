"""Enriquecimento de metadados do video.

Duas fontes, ambas opcionais — sem rede o pipeline usa o que veio do Takeout:

1. YouTube Data API v3 (`YOUTUBE_API_KEY`): duracao, descricao, tags, data de
   publicacao. Uma chamada a cada 50 videos.
2. oEmbed publico (sem chave): titulo canonico, canal e thumbnail.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Iterable, List, Optional
from urllib.parse import urlencode

from .util import FetchError, http_get_json, parse_datetime, parse_iso8601_duration

OEMBED_URL = "https://www.youtube.com/oembed"
DATA_API_URL = "https://www.googleapis.com/youtube/v3/videos"
API_BATCH_SIZE = 50


@dataclass
class VideoMeta:
    video_id: str
    title: Optional[str] = None
    channel: Optional[str] = None
    channel_url: Optional[str] = None
    published_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    language: Optional[str] = None
    thumbnail: Optional[str] = None
    source: str = "takeout"


def fetch_oembed(video_id: str, timeout: float = 20.0) -> VideoMeta:
    query = urlencode(
        {"url": f"https://www.youtube.com/watch?v={video_id}", "format": "json"}
    )
    payload = http_get_json(f"{OEMBED_URL}?{query}", timeout=timeout)
    return VideoMeta(
        video_id=video_id,
        title=payload.get("title"),
        channel=payload.get("author_name"),
        channel_url=payload.get("author_url"),
        thumbnail=payload.get("thumbnail_url"),
        source="oembed",
    )


def fetch_data_api(
    video_ids: Iterable[str], api_key: str, timeout: float = 20.0
) -> Dict[str, VideoMeta]:
    ids = list(dict.fromkeys(video_ids))
    result: Dict[str, VideoMeta] = {}

    for start in range(0, len(ids), API_BATCH_SIZE):
        batch = ids[start : start + API_BATCH_SIZE]
        query = urlencode(
            {
                "part": "snippet,contentDetails",
                "id": ",".join(batch),
                "key": api_key,
            }
        )
        payload = http_get_json(f"{DATA_API_URL}?{query}", timeout=timeout)
        for item in payload.get("items", []):
            snippet = item.get("snippet", {})
            content = item.get("contentDetails", {})
            channel_id = snippet.get("channelId")
            result[item["id"]] = VideoMeta(
                video_id=item["id"],
                title=snippet.get("title"),
                channel=snippet.get("channelTitle"),
                channel_url=(
                    f"https://www.youtube.com/channel/{channel_id}" if channel_id else None
                ),
                published_at=parse_datetime(snippet.get("publishedAt") or ""),
                duration_seconds=parse_iso8601_duration(content.get("duration") or ""),
                description=snippet.get("description") or None,
                tags=list(snippet.get("tags") or []),
                language=snippet.get("defaultAudioLanguage")
                or snippet.get("defaultLanguage"),
                thumbnail=(snippet.get("thumbnails", {}).get("high", {}) or {}).get("url"),
                source="api",
            )
    return result


class MetadataResolver:
    """Resolve metadados com degradacao: API -> oEmbed -> so o Takeout."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        enabled: bool = True,
        timeout: float = 20.0,
        log=lambda message: None,
    ) -> None:
        self.api_key = api_key or os.environ.get("YOUTUBE_API_KEY") or None
        self.enabled = enabled
        self.timeout = timeout
        self.log = log
        self.errors: List[str] = []

    def resolve(self, video_ids: List[str]) -> Dict[str, VideoMeta]:
        if not self.enabled or not video_ids:
            return {}

        resolved: Dict[str, VideoMeta] = {}
        if self.api_key:
            try:
                resolved = fetch_data_api(video_ids, self.api_key, self.timeout)
                self.log(f"Data API: {len(resolved)}/{len(video_ids)} videos resolvidos")
            except FetchError as exc:
                self.errors.append(f"Data API indisponivel ({exc})")
                self.log(f"! Data API falhou, caindo para oEmbed: {exc}")

        pending = [vid for vid in video_ids if vid not in resolved]
        oembed_failures = 0
        for video_id in pending:
            try:
                resolved[video_id] = fetch_oembed(video_id, self.timeout)
            except FetchError as exc:
                oembed_failures += 1
                if oembed_failures == 1:
                    self.errors.append(f"oEmbed indisponivel ({exc})")
        if oembed_failures:
            self.log(
                f"! oEmbed falhou em {oembed_failures} video(s); "
                "as notas usam os dados do Takeout"
            )
        return resolved


def merge_meta(record, meta: Optional[VideoMeta]) -> VideoMeta:
    """Combina o registro do Takeout com o que a rede trouxe.

    A rede vence no titulo (o Takeout perde a formatacao original), mas nunca
    apaga um campo que so o Takeout tem.
    """
    merged = VideoMeta(video_id=record.video_id, source="takeout")
    if meta:
        merged = VideoMeta(**{**meta.__dict__, "tags": list(meta.tags)})
    merged.title = merged.title or record.title or record.video_id
    merged.channel = merged.channel or record.channel
    merged.channel_url = merged.channel_url or record.channel_url
    return merged
