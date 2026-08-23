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
import re
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


def compile_keyword(word: str) -> Optional[re.Pattern]:
    """Palavra-chave -> regex com fronteira de palavra.

    Substring simples errava dos dois lados: `smr` casava dentro de `#asmr`, e
    ` ai ` (com espacos, a gambiarra para evitar isso) perdia um titulo que
    termina em "...of AI". A fronteira resolve os dois casos.
    """
    folded = _fold(word).strip()
    if not folded:
        return None
    prefix = r"\b" if folded[0].isalnum() else ""
    suffix = r"\b" if folded[-1].isalnum() else ""
    return re.compile(prefix + re.escape(folded) + suffix)


def _is_specific(word: str) -> bool:
    """Termo composto e especifico o bastante para casar contra o nome do canal.

    Um termo de uma palavra so nao serve: o canal "The Ai Democracy" jogaria
    todo video dele em AI, inclusive um clipe do Bruce Lee.
    """
    return len(_fold(word).split()) > 1


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
        self.rules = {}
        for folder, words in (rules or {}).items():
            compiled = []
            for word in words:
                pattern = compile_keyword(word)
                if pattern is not None:
                    compiled.append((pattern, _is_specific(word)))
            if compiled:
                self.rules[folder] = compiled
        self.assignments = assignments or {}

    def folders(self) -> List[str]:
        """Todas as pastas que este classificador pode criar."""
        names = set(self.rules)
        if self.playlists:
            names.update(self.playlists.names)
        names.update(self.assignments.values())
        return sorted(sanitize_folder(name) for name in names if name)

    def classify(
        self,
        video_id: str,
        title: Optional[str] = None,
        channel: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Decision:
        member_of = self.playlists.all_for(video_id) if self.playlists else []

        assigned = self.assignments.get(video_id)
        if assigned:
            return Decision(sanitize_folder(assigned), "assign", member_of)

        if member_of:
            return Decision(sanitize_folder(sorted(member_of)[0]), "playlist", member_of)

        # O que o video E: titulo e descricao. Toda palavra-chave vale aqui.
        content = _fold(" ".join(text for text in (title, description) if text))
        # Quem publicou: so termos compostos, para o nome do canal nao arrastar
        # videos fora do assunto.
        source = _fold(channel or "")

        for folder in sorted(self.rules):
            for pattern, specific in self.rules[folder]:
                if pattern.search(content) or (specific and pattern.search(source)):
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
