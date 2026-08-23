"""Leitura das playlists exportadas pelo Takeout.

O Takeout traz `playlists/<Nome>-videos.csv`, um arquivo por playlist. Isso da
duas coisas de graca: a taxonomia de pastas (os nomes das playlists) e a
associacao video -> playlist, sem precisar adivinhar nada.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence

VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")

# Playlists do sistema: sao caixas de entrada, nao assuntos. Nao viram pasta.
DEFAULT_IGNORED = (
    "watch later",
    "assistir mais tarde",
    "ver mais tarde",
    "likes",
    "liked videos",
    "videos marcados como gostei",
    "vídeos marcados como gostei",
    "favorites",
    "favoritos",
    "uploads from",
)

_SUFFIX = re.compile(r"-videos$", re.IGNORECASE)


@dataclass
class Playlists:
    names: List[str] = field(default_factory=list)
    by_video: Dict[str, List[str]] = field(default_factory=dict)

    def folder_for(self, video_id: str) -> Optional[str]:
        """Pasta do video. Em mais de uma playlist, vence a primeira alfabetica."""
        matches = self.by_video.get(video_id)
        return sorted(matches)[0] if matches else None

    def all_for(self, video_id: str) -> List[str]:
        return sorted(self.by_video.get(video_id, []))


def discover_playlists_dir(root: Path) -> Optional[Path]:
    """Acha a pasta `playlists` dentro de um Takeout descompactado."""
    if root.is_dir() and root.name.lower() in ("playlists", "playlist"):
        return root
    if root.is_file():
        root = root.parent
    # Busca rasa de proposito: no Takeout a pasta fica no maximo dois niveis
    # abaixo, e varrer o disco inteiro acharia diretorios sem relacao.
    for pattern in ("*/", "*/*/"):
        for candidate in sorted(root.glob(pattern)):
            if candidate.name.lower() in ("playlists", "playlist"):
                return candidate
    return None


def _playlist_name(path: Path) -> str:
    return _SUFFIX.sub("", path.stem).strip()


def _is_ignored(name: str, ignored: Sequence[str]) -> bool:
    lowered = name.strip().lower()
    return any(lowered.startswith(pattern) for pattern in ignored)


def read_playlist_csv(path: Path) -> List[str]:
    """Extrai os IDs de video de um `<Nome>-videos.csv`.

    Alguns exports colocam um bloco de metadados da playlist antes da tabela de
    videos, entao procuramos a linha de cabecalho que contem "Video ID".
    """
    video_ids: List[str] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        in_table = False
        for row in csv.reader(handle):
            if not row:
                in_table = False  # linha em branco separa os blocos
                continue
            first = row[0].strip()
            if not in_table:
                if any("video id" in cell.strip().lower() for cell in row):
                    in_table = True
                continue
            if VIDEO_ID.match(first):
                video_ids.append(first)
    return video_ids


def load_playlists(
    directory: Path, ignored: Sequence[str] = DEFAULT_IGNORED
) -> Playlists:
    playlists = Playlists()
    for path in sorted(directory.glob("*.csv")):
        name = _playlist_name(path)
        if not name or _is_ignored(name, ignored):
            continue
        video_ids = read_playlist_csv(path)
        if not video_ids:
            continue
        playlists.names.append(name)
        for video_id in video_ids:
            playlists.by_video.setdefault(video_id, []).append(name)
    return playlists
