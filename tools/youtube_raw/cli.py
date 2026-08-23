"""CLI: Takeout -> notas .md em 0_RAW.

    python3 -m tools.youtube_raw --takeout <caminho> --vault <caminho> [opcoes]
"""

from __future__ import annotations

import argparse
import re
import time
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional, Sequence

from .ledger import LEDGER_NAME, Ledger
from .metadata import MetadataResolver, VideoMeta, merge_meta
from .render import build_filename, build_note, merge_note
from .takeout import WatchRecord, aggregate, load_history
from .transcript import fetch_transcript
from .util import fmt_duration

DEFAULT_TAGS = ("youtube", "source/video", "karpathy/inbox")
DEFAULT_LANGS = ("pt", "pt-BR", "en")
DEFAULT_FILENAME = "{date} {title} ({video_id})"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 -m tools.youtube_raw",
        description="Gera notas .md em 0_RAW a partir do historico do YouTube (Google Takeout).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    source = parser.add_argument_group("entrada e saida")
    source.add_argument(
        "--takeout",
        required=True,
        type=Path,
        help="watch-history.json (ou .html), ou a pasta do Takeout para busca automatica",
    )
    source.add_argument("--vault", required=True, type=Path, help="raiz do vault do Obsidian")
    source.add_argument("--raw-dir", default="0_RAW", help="pasta de destino (padrao: 0_RAW)")
    source.add_argument(
        "--filename-template",
        default=DEFAULT_FILENAME,
        help="campos: {date} {title} {video_id} {channel} (padrao: %(default)s)",
    )

    selection = parser.add_argument_group("selecao de videos")
    selection.add_argument("--since", type=_parse_date, help="assistidos a partir de AAAA-MM-DD")
    selection.add_argument("--until", type=_parse_date, help="assistidos ate AAAA-MM-DD")
    selection.add_argument("--limit", type=int, help="processa no maximo N videos")
    selection.add_argument(
        "--channel", action="append", default=[], help="so canais que contenham este texto"
    )
    selection.add_argument(
        "--exclude-channel", action="append", default=[], help="descarta canais que contenham este texto"
    )
    selection.add_argument("--match", help="regex aplicada ao titulo do video")
    selection.add_argument(
        "--video-id", action="append", default=[], help="processa apenas estes IDs"
    )
    selection.add_argument(
        "--min-duration",
        type=int,
        default=0,
        help="descarta videos mais curtos que N segundos (exige metadados da Data API)",
    )

    enrich = parser.add_argument_group("enriquecimento")
    enrich.add_argument("--api-key", help="chave da YouTube Data API v3 (ou env YOUTUBE_API_KEY)")
    enrich.add_argument("--offline", action="store_true", help="nao acessa a rede")
    enrich.add_argument("--no-transcript", action="store_true", help="nao baixa transcricoes")
    enrich.add_argument(
        "--transcript-lang", nargs="+", default=list(DEFAULT_LANGS), help="idiomas preferidos"
    )
    enrich.add_argument(
        "--transcript-window",
        type=float,
        default=45.0,
        help="segundos por paragrafo da transcricao (padrao: %(default)s)",
    )
    enrich.add_argument(
        "--sleep", type=float, default=0.4, help="pausa entre requisicoes, em segundos"
    )

    output = parser.add_argument_group("escrita")
    output.add_argument(
        "--tag", action="append", default=[], help=f"tags do frontmatter (padrao: {', '.join(DEFAULT_TAGS)})"
    )
    output.add_argument("--no-channel-tag", action="store_true", help="nao adiciona canal/<nome>")
    output.add_argument(
        "--update",
        action="store_true",
        help="regera o bloco automatico de notas ja existentes, preservando o que voce escreveu",
    )
    output.add_argument(
        "--force",
        action="store_true",
        help="reescreve a nota inteira, DESCARTANDO o que voce escreveu nela",
    )
    output.add_argument("--dry-run", action="store_true", help="mostra o plano sem escrever nada")
    output.add_argument("--report", type=Path, help="grava um relatorio .md da execucao")
    output.add_argument("-v", "--verbose", action="store_true")
    return parser


def _parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError(f"data invalida: {value} (use AAAA-MM-DD)")


def resolve_takeout_path(path: Path) -> Path:
    if path.is_file():
        return path
    if path.is_dir():
        for pattern in ("**/watch-history.json", "**/watch-history.html"):
            found = sorted(path.glob(pattern))
            if found:
                return found[0]
        raise FileNotFoundError(f"nenhum watch-history.json/html encontrado em {path}")
    raise FileNotFoundError(f"caminho inexistente: {path}")


def filter_records(records: Sequence[WatchRecord], args) -> List[WatchRecord]:
    wanted_ids = set(args.video_id)
    include = [text.lower() for text in args.channel]
    exclude = [text.lower() for text in args.exclude_channel]
    pattern = re.compile(args.match, re.IGNORECASE) if args.match else None

    selected = []
    for record in records:
        if wanted_ids and record.video_id not in wanted_ids:
            continue

        watched = record.last_watched
        if args.since or args.until:
            if watched is None:
                continue
            if args.since and watched.date() < args.since:
                continue
            if args.until and watched.date() > args.until:
                continue

        channel = (record.channel or "").lower()
        if include and not any(text in channel for text in include):
            continue
        if exclude and any(text in channel for text in exclude):
            continue
        if pattern and not pattern.search(record.title or ""):
            continue

        selected.append(record)
    return selected


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    log = print
    debug = print if args.verbose else (lambda *a, **k: None)

    try:
        history_path = resolve_takeout_path(args.takeout)
    except FileNotFoundError as exc:
        log(f"erro: {exc}")
        return 2

    raw_dir = args.vault / args.raw_dir
    log(f"Historico : {history_path}")
    log(f"Destino   : {raw_dir}")

    try:
        records = aggregate(load_history(history_path))
    except (ValueError, OSError) as exc:
        log(f"erro ao ler o historico: {exc}")
        return 2
    log(f"Videos unicos no historico: {len(records)}")

    selected = filter_records(records, args)
    log(f"Depois dos filtros: {len(selected)}")

    ledger = Ledger(raw_dir / LEDGER_NAME)
    todo: List[WatchRecord] = []
    skipped_existing = 0
    for record in selected:
        known = ledger.get(record.video_id)
        if known and not (args.update or args.force):
            skipped_existing += 1
            debug(f"  - ja existe, pulando: {record.video_id} ({known['path']})")
            continue
        todo.append(record)
    if skipped_existing:
        log(f"Ja registrados (use --update para atualizar): {skipped_existing}")

    if args.limit is not None:
        todo = todo[: args.limit]
    if not todo:
        log("Nada a fazer.")
        return 0
    log(f"A processar: {len(todo)}")

    resolver = MetadataResolver(
        api_key=args.api_key, enabled=not args.offline, timeout=20.0, log=debug
    )
    metas = resolver.resolve([record.video_id for record in todo])

    written, updated, failed, too_short = [], [], [], 0
    try:
        for index, record in enumerate(todo, start=1):
            meta: VideoMeta = merge_meta(record, metas.get(record.video_id))

            if args.min_duration and meta.duration_seconds:
                if meta.duration_seconds < args.min_duration:
                    too_short += 1
                    debug(f"  - curto demais ({fmt_duration(meta.duration_seconds)}): {meta.title}")
                    continue

            transcript = None
            if not args.no_transcript and not args.offline:
                transcript = fetch_transcript(record.video_id, args.transcript_lang)
                if args.sleep:
                    time.sleep(args.sleep)

            note = build_note(
                meta,
                record,
                transcript,
                base_tags=args.tag or list(DEFAULT_TAGS),
                channel_tag=not args.no_channel_tag,
                transcript_window=args.transcript_window,
            )

            known = ledger.get(record.video_id)
            target = raw_dir / (known["path"] if known else build_filename(
                meta, record, args.filename_template
            ))
            exists = target.exists()

            marker = "~" if exists else "+"
            log(f"[{index}/{len(todo)}] {marker} {target.name}")

            if args.dry_run:
                (updated if exists else written).append(target.name)
                continue

            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                if exists and not args.force:
                    content = merge_note(target.read_text(encoding="utf-8"), note)
                else:
                    content = note
                target.write_text(content, encoding="utf-8")
            except OSError as exc:
                failed.append(f"{record.video_id}: {exc}")
                log(f"    ! falhou: {exc}")
                continue

            ledger.record(
                record.video_id,
                str(target.relative_to(raw_dir)),
                has_transcript=bool(transcript),
            )
            (updated if exists else written).append(target.name)
    except KeyboardInterrupt:
        log("\nInterrompido — salvando o progresso.")
    finally:
        if not args.dry_run:
            ledger.save()

    log("")
    log(f"Criadas    : {len(written)}")
    log(f"Atualizadas: {len(updated)}")
    if too_short:
        log(f"Descartadas por duracao: {too_short}")
    if failed:
        log(f"Falhas     : {len(failed)}")
    for problem in resolver.errors:
        log(f"aviso: {problem}")
    if args.dry_run:
        log("(dry-run: nenhum arquivo foi escrito)")

    if args.report and not args.dry_run:
        _write_report(args.report, written, updated, failed, resolver.errors)
        log(f"Relatorio  : {args.report}")

    return 1 if failed else 0


def _write_report(
    path: Path,
    written: Sequence[str],
    updated: Sequence[str],
    failed: Sequence[str],
    warnings: Sequence[str],
) -> None:
    lines = [
        f"# Execucao youtube-raw — {datetime.now().isoformat(timespec='seconds')}",
        "",
        f"- Criadas: {len(written)}",
        f"- Atualizadas: {len(updated)}",
        f"- Falhas: {len(failed)}",
        "",
    ]
    for title, items in (
        ("## Criadas", written),
        ("## Atualizadas", updated),
        ("## Falhas", failed),
        ("## Avisos", warnings),
    ):
        if items:
            lines.append(title)
            lines.extend(f"- {item}" for item in items)
            lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
