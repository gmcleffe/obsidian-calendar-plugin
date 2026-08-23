"""Estagio 2: preenche as secoes de analise a partir da transcricao.

A captura (`python3 -m tools.youtube_raw`) continua sem LLM: ela so registra o
que o video E. Este modulo e a etapa separada e explicita que le a transcricao
ja gravada na nota e escreve resumo, conceitos e o que reimplementar.

    python3 -m tools.youtube_raw.enrich --vault <...> --raw-dir Notas --folder AI

Regra que nao se quebra: **so preenche secao vazia**. Se voce escreveu algo,
fica como esta. E sem transcricao a nota e pulada — resumir a partir do titulo
seria inventar o conteudo do video.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from .render import AUTO_START, split_frontmatter

MODEL = "claude-opus-5"

# Cada secao da nota e o campo do JSON que a preenche.
SECTIONS = {
    "## ⚡ Resumo em 3 linhas": "resumo",
    "## 🧠 Conceitos-chave": "conceitos",
    "## 🔨 Reimplementar do zero": "reimplementar",
    "## ❓ Perguntas abertas": "perguntas",
    "## ⏱️ Momentos que valem revisitar": "momentos",
    "## 🔗 Conexões": "conexoes",
}
CHECKBOX_SECTIONS = {"## 🔨 Reimplementar do zero"}

SYSTEM = """Você extrai conhecimento de transcrições de vídeo para um sistema de \
estudo baseado no método Karpathy: assistir, reimplementar do zero, comparar, explicar.

Regras invioláveis:
- Escreva SOMENTE o que a transcrição sustenta. Nunca complete com conhecimento \
próprio sobre o tema, o canal ou o palestrante.
- Se a transcrição for curta demais, cortada ou não sustentar uma seção, devolva \
lista vazia para ela. Lista vazia é uma resposta correta; inventar não é.
- Cite números, nomes e afirmações exatamente como aparecem. Não arredonde nem suavize.
- Escreva no idioma da transcrição.
- Sem preâmbulo, sem "neste vídeo", sem elogio ao conteúdo. Frases densas e diretas.

O que cada seção quer:
- resumo: 3 frases com a tese central, não uma descrição do formato do vídeo.
- conceitos: os conceitos que alguém precisa entender para reproduzir o raciocínio. \
Nomeie o conceito e diga o que ele afirma.
- reimplementar: tarefas concretas de construir do zero, só se o conteúdo for \
técnico o bastante. Vídeo de opinião ou entrevista costuma devolver lista vazia.
- perguntas: o que o vídeo levanta e não responde, ou onde a afirmação carece de evidência.
- momentos: timestamps que valem revisitar, no formato "MM:SS — o que acontece ali". \
Use apenas timestamps presentes na transcrição.
- conexoes: conceitos para virar nota própria no Obsidian, como [[Nome do Conceito]]."""

SCHEMA = {
    "type": "object",
    "properties": {
        key: {"type": "array", "items": {"type": "string"}}
        for key in SECTIONS.values()
    },
    "required": list(SECTIONS.values()),
    "additionalProperties": False,
}


@dataclass
class Note:
    path: Path
    text: str
    title: str
    channel: Optional[str]
    transcript: str

    @property
    def has_transcript(self) -> bool:
        return len(self.transcript.split()) >= 100


def _frontmatter_value(entries, key: str) -> Optional[str]:
    for name, raw in entries:
        if name == key:
            value = raw[0].split(":", 1)[1].strip()
            return value.strip('"') or None
    return None


def extract_transcript(body: str) -> str:
    """Texto da transcricao, sem os marcadores de timestamp em markdown."""
    marker = "### Transcrição"
    start = body.find(marker, body.find(AUTO_START))
    if start == -1:
        return ""
    chunk = body[start + len(marker) :]
    chunk = chunk.split("<!-- yt-raw:auto:end -->")[0]
    if "Transcrição indisponível" in chunk:
        return ""
    return chunk.strip()


def load_note(path: Path) -> Note:
    text = path.read_text(encoding="utf-8")
    entries, body = split_frontmatter(text)
    return Note(
        path=path,
        text=text,
        title=_frontmatter_value(entries, "title") or path.stem,
        channel=_frontmatter_value(entries, "channel"),
        transcript=extract_transcript(body),
    )


def section_bounds(body: str, heading: str) -> Optional[tuple]:
    start = body.find(heading)
    if start == -1:
        return None
    after = start + len(heading)
    nxt = body.find("\n## ", after)
    end = body.find("\n---", after)
    stop = min(x for x in (nxt, end, len(body)) if x != -1)
    return after, stop


# Andaime que o template deixa: bullet, checkbox e wikilink vazio.
_PLACEHOLDER = re.compile(r"^\s*(?:[-*]\s*)?(?:\[[ xX]\]\s*)?(?:\[\[\s*\]\])?\s*$")


def section_is_empty(content: str) -> bool:
    """Vazia = so o andaime do template, sem texto seu."""
    return all(_PLACEHOLDER.match(line) for line in content.strip().splitlines())


def render_items(items: Sequence[str], checkbox: bool) -> str:
    if not items:
        return "\n\n- \n"
    prefix = "- [ ] " if checkbox else "- "
    return "\n\n" + "\n".join(f"{prefix}{item.strip()}" for item in items) + "\n"


def apply_sections(text: str, data: Dict[str, List[str]]) -> tuple:
    """Preenche apenas as secoes vazias. Devolve (novo_texto, secoes_escritas)."""
    written = []
    for heading, key in SECTIONS.items():
        items = [item for item in data.get(key, []) if item and item.strip()]
        if not items:
            continue
        bounds = section_bounds(text, heading)
        if bounds is None:
            continue
        start, stop = bounds
        if not section_is_empty(text[start:stop]):
            continue  # voce escreveu aqui: nao encostamos
        text = text[:start] + render_items(items, heading in CHECKBOX_SECTIONS) + text[stop:]
        written.append(key)
    return text, written


def stamp_frontmatter(text: str, model: str) -> str:
    entries, body = split_frontmatter(text)
    keys = {name for name, _ in entries}
    additions = []
    if "enriched" not in keys:
        additions += [
            ("enriched", ["enriched: true"]),
            ("enriched_at", [f"enriched_at: {date.today().isoformat()}"]),
            ("enriched_model", [f'enriched_model: "{model}"']),
        ]
    else:
        entries = [
            (name, [f"enriched_at: {date.today().isoformat()}"] if name == "enriched_at" else raw)
            for name, raw in entries
        ]
    lines = ["---"]
    for _, raw in entries + additions:
        lines.extend(raw)
    lines.append("---")
    return "\n".join(lines) + "\n" + body.lstrip("\n")


def summarize(client, note: Note, model: str = MODEL) -> Dict[str, List[str]]:
    """Uma chamada por nota. O system fica em cache entre as chamadas."""
    response = client.messages.create(
        model=model,
        max_tokens=8000,
        system=[{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
        thinking={"type": "adaptive"},
        output_config={"effort": "medium", "format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[
            {
                "role": "user",
                "content": (
                    f"Vídeo: {note.title}\n"
                    f"Canal: {note.channel or 'desconhecido'}\n\n"
                    f"Transcrição:\n{note.transcript}"
                ),
            }
        ],
    )
    text = next(block.text for block in response.content if block.type == "text")
    return json.loads(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 -m tools.youtube_raw.enrich",
        description="Preenche as seções de análise das notas a partir da transcrição.",
    )
    parser.add_argument("--vault", required=True, type=Path)
    parser.add_argument("--raw-dir", default="0_RAW")
    parser.add_argument("--folder", help="restringe a uma subpasta, ex.: AI")
    parser.add_argument("--limit", type=int, help="processa no máximo N notas")
    parser.add_argument("--model", default=MODEL)
    parser.add_argument(
        "--redo", action="store_true", help="reprocessa notas já enriquecidas"
    )
    parser.add_argument("--dry-run", action="store_true", help="mostra o plano e sai")
    return parser


def main(argv: Optional[Sequence[str]] = None, client=None) -> int:
    args = build_parser().parse_args(argv)
    log = print

    root = args.vault / args.raw_dir / (args.folder or "")
    if not root.is_dir():
        log(f"erro: pasta inexistente: {root}")
        return 2

    candidates, sem_transcricao, ja_feitas = [], 0, 0
    for path in sorted(root.rglob("*.md")):
        if path.name.startswith("_"):
            continue
        note = load_note(path)
        if "enriched: true" in note.text and not args.redo:
            ja_feitas += 1
            continue
        if not note.has_transcript:
            sem_transcricao += 1
            continue
        candidates.append(note)

    log(f"Pasta         : {root}")
    log(f"Com transcrição: {len(candidates)}")
    if sem_transcricao:
        log(f"Sem transcrição (puladas): {sem_transcricao}")
    if ja_feitas:
        log(f"Já enriquecidas (use --redo): {ja_feitas}")

    if args.limit is not None:
        candidates = candidates[: args.limit]
    if not candidates:
        log("Nada a fazer. Rode a captura com transcrição antes deste estágio.")
        return 0
    if args.dry_run:
        log(f"(dry-run) {len(candidates)} notas seriam enriquecidas")
        return 0

    if client is None:
        try:
            import anthropic
        except ImportError:
            log("erro: falta o SDK. Rode: pip install anthropic")
            return 2
        client = anthropic.Anthropic()

    ok, failed = 0, []
    for index, note in enumerate(candidates, start=1):
        try:
            data = summarize(client, note, args.model)
        except Exception as exc:  # rede, rate limit, JSON invalido
            failed.append(f"{note.path.name}: {type(exc).__name__}: {exc}")
            log(f"[{index}/{len(candidates)}] ! {note.path.name} — {exc}")
            continue
        text, written = apply_sections(note.text, data)
        if not written:
            log(f"[{index}/{len(candidates)}] = {note.path.name} (nada vazio para preencher)")
            continue
        note.path.write_text(stamp_frontmatter(text, args.model), encoding="utf-8")
        ok += 1
        log(f"[{index}/{len(candidates)}] + {note.path.name} — {', '.join(written)}")

    log("")
    log(f"Enriquecidas: {ok}")
    if failed:
        log(f"Falhas      : {len(failed)}")
    return 1 if failed and not ok else 0


if __name__ == "__main__":
    sys.exit(main())
