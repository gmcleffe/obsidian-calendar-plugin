"""Registro do que ja virou nota, para reexecucoes serem idempotentes.

Arquivo oculto dentro da pasta 0_RAW: o Obsidian ignora dotfiles.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

LEDGER_NAME = ".youtube-raw.state.json"
SCHEMA = 1


class Ledger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.entries: Dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return  # ledger corrompido: recomeca do zero em vez de quebrar
        if isinstance(payload, dict):
            self.entries = payload.get("videos", {}) or {}

    def get(self, video_id: str) -> Optional[dict]:
        return self.entries.get(video_id)

    def record(self, video_id: str, relative_path: str, has_transcript: bool) -> None:
        previous = self.entries.get(video_id, {})
        self.entries[video_id] = {
            "path": relative_path,
            "transcript": has_transcript,
            "first_written": previous.get(
                "first_written", datetime.now(timezone.utc).isoformat(timespec="seconds")
            ),
            "last_written": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"schema": SCHEMA, "videos": self.entries}
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.replace(self.path)
