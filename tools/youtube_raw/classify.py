"""Decide em qual subpasta cada nota entra.

Tres fontes, nesta ordem de prioridade:

1. `--assign-file` — decisoes explicitas (video_id -> pasta). E por aqui que o
   agente devolve a classificacao semantica dos videos que sobraram.
2. Playlists do Takeout — pertencimento real, sem adivinhacao.
3. `--rules` — palavras-chave por pasta, aplicadas a titulo, canal e descricao.

Sem match em nenhuma, a nota fica na raiz, como pedido.
"""

from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from .playlists import Playlists
from .util import slugify


def sanitize_folder(name: str) -> str:
    """Nome de playlist -> nome de pasta seguro (uma pasta, sem aninhar)."""
    return slugify(name.replace("/", "-").replace("\\", "-"), max_len=60)


def _fold(text: str) -> str:
    """Minuscula e sem acento, para casar palavra-chave sem falso negativo."""
    normalized = unicodedata.normalize("NFKD", text or "")
    return normalized.encode("ascii", "ignore").decode("ascii").lower()


@dataclass
class Decision:
    folder: Optional[str]
    reason: str
    playlists: List[str] = field(default_factory=list)


class Classifier:
    def __init__(
        self,
        playlists: Optional[Playlists] = None,
        rules: Optional[Dict[str, Sequence[str]]] = None,
        assignments: Optional[Dict[str, str]] = None,
    ) -> None:
        self.playlists = playlists
        self.rules = {
            folder: [_fold(word) for word in words] for folder, words in (rules or {}).items()
        }
        self.assignments = assignments or {}

    def folders(self) -> List[str]:
        """Todas as pastas que este classificador pode criar."""
        names = set(self.rules)
        if self.playlists:
            names.update(self.playlists.names)
        names.update(self.assignments.values())
        return sorted(sanitize_folder(name) for name in names if name)

    def classify(self, video_id: str, *texts: Optional[str]) -> Decision:
        member_of = self.playlists.all_for(video_id) if self.playlists else []

        assigned = self.assignments.get(video_id)
        if assigned:
            return Decision(sanitize_folder(assigned), "assign", member_of)

        if member_of:
            return Decision(sanitize_folder(sorted(member_of)[0]), "playlist", member_of)

        if self.rules:
            haystack = _fold(" ".join(text for text in texts if text))
            for folder in sorted(self.rules):
                if any(word and word in haystack for word in self.rules[folder]):
                    return Decision(sanitize_folder(folder), "rule", member_of)

        return Decision(None, "unclassified", member_of)


def load_json_map(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} deveria conter um objeto JSON")
    return payload


def load_rules(path: Path) -> Dict[str, List[str]]:
    """{"IA": ["llm", "transformer"], "Investimentos": ["valuation"]}"""
    raw = load_json_map(path)
    rules: Dict[str, List[str]] = {}
    for folder, words in raw.items():
        if isinstance(words, str):
            words = [words]
        rules[str(folder)] = [str(word) for word in words]
    return rules


def load_assignments(path: Path) -> Dict[str, str]:
    """{"kCc8FmEb1nY": "IA"} — decisoes do agente, uma por video."""
    return {str(key): str(value) for key, value in load_json_map(path).items() if value}
