"""Testes offline do pipeline: `python3 -m unittest discover -s tools/youtube_raw/tests`."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from unittest import mock
from datetime import datetime, timezone
from pathlib import Path

from tools.youtube_raw import classify, cli, enrich, playlists, render, takeout, transcript, util
from tools.youtube_raw.metadata import VideoMeta, merge_meta

FIXTURES = Path(__file__).parent / "fixtures"


def run_quiet(argv):
    """Roda a CLI engolindo o log, para a saida da suite ficar legivel."""
    with contextlib.redirect_stdout(io.StringIO()):
        return cli.main(argv)


class TakeoutTests(unittest.TestCase):
    def test_extract_video_id_handles_every_url_shape(self):
        for url in (
            "https://www.youtube.com/watch?v=kCc8FmEb1nY",
            "https://www.youtube.com/watch?t=10&v=kCc8FmEb1nY",
            "https://youtu.be/kCc8FmEb1nY?t=5",
            "https://www.youtube.com/shorts/kCc8FmEb1nY",
            "https://www.youtube.com/live/kCc8FmEb1nY",
        ):
            self.assertEqual(takeout.extract_video_id(url), "kCc8FmEb1nY", url)

    def test_non_video_urls_are_ignored(self):
        self.assertIsNone(
            takeout.extract_video_id("https://www.youtube.com/results?search_query=x")
        )
        self.assertIsNone(takeout.extract_video_id(None))

    def test_json_history_skips_ads_searches_and_removed_videos(self):
        records = takeout.aggregate(takeout.load_history(FIXTURES / "watch-history.json"))
        self.assertEqual(
            sorted(record.video_id for record in records),
            ["P2LTAUO1TdA", "kCc8FmEb1nY"],
        )

    def test_rewatches_collapse_into_one_record(self):
        records = {
            record.video_id: record
            for record in takeout.aggregate(
                takeout.load_history(FIXTURES / "watch-history.json")
            )
        }
        gpt = records["kCc8FmEb1nY"]
        self.assertEqual(gpt.watch_count, 2)
        self.assertEqual(gpt.first_watched.date().isoformat(), "2026-07-02")
        self.assertEqual(gpt.last_watched.date().isoformat(), "2026-08-20")

    def test_watched_prefix_stripped_in_several_locales(self):
        self.assertEqual(takeout.strip_watched_prefix("Watched Foo"), "Foo")
        self.assertEqual(takeout.strip_watched_prefix("Assistiu a Foo"), "Foo")
        self.assertEqual(takeout.strip_watched_prefix("Foo"), "Foo")

    def test_html_history_is_parsed_too(self):
        records = takeout.aggregate(takeout.load_history(FIXTURES / "watch-history.html"))
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].video_id, "kCc8FmEb1nY")
        self.assertEqual(records[0].channel, "Andrej Karpathy")


class UtilTests(unittest.TestCase):
    def test_slugify_strips_characters_obsidian_cannot_use(self):
        self.assertEqual(util.slugify('a/b:c*d?e"f<g>h|i#j^k[l]m'), "a b c d e f g h i j k l m")

    def test_slugify_keeps_accents(self):
        self.assertEqual(util.slugify("Álgebra linear"), "Álgebra linear")

    def test_iso_duration(self):
        self.assertEqual(util.parse_iso8601_duration("PT1H56M20S"), 6980)
        self.assertIsNone(util.parse_iso8601_duration("bogus"))

    def test_yaml_scalar_escapes_quotes(self):
        self.assertEqual(util.yaml_scalar('say "hi"'), '"say \\"hi\\""')


class TranscriptTests(unittest.TestCase):
    def test_segments_group_into_paragraphs(self):
        segments = [
            {"start": 0.0, "text": "um"},
            {"start": 10.0, "text": "dois"},
            {"start": 50.0, "text": "tres"},
        ]
        self.assertEqual(
            transcript.group_segments(segments, window=45.0),
            [(0.0, "um dois"), (50.0, "tres")],
        )

    def test_rendered_paragraphs_link_to_the_right_second(self):
        text = transcript.render_transcript(
            transcript.Transcript("vid", segments=[{"start": 95.0, "text": "oi"}]), "vid"
        )
        self.assertIn("[01:35](https://youtu.be/vid?t=95)", text)


def _record(**overrides):
    base = dict(
        video_id="kCc8FmEb1nY",
        url="https://www.youtube.com/watch?v=kCc8FmEb1nY",
        title="Let's build GPT",
        channel="Andrej Karpathy",
        channel_url="https://www.youtube.com/channel/UC",
        watched_at=[datetime(2026, 8, 20, tzinfo=timezone.utc)],
    )
    base.update(overrides)
    return takeout.WatchRecord(**base)


class RenderTests(unittest.TestCase):
    def setUp(self):
        self.record = _record()
        self.meta = merge_meta(
            self.record,
            VideoMeta(
                video_id="kCc8FmEb1nY",
                title="Let's build GPT: from scratch",
                channel="Andrej Karpathy",
                duration_seconds=6980,
                published_at=datetime(2023, 1, 17, tzinfo=timezone.utc),
                description="linha 1\nlinha 2",
                source="api",
            ),
        )

    def build(self, with_transcript=True):
        note_transcript = (
            transcript.Transcript(
                "kCc8FmEb1nY",
                language="en",
                generated=True,
                segments=[{"start": 0.0, "text": "hello"}],
            )
            if with_transcript
            else None
        )
        return render.build_note(
            self.meta, self.record, note_transcript, base_tags=("youtube", "karpathy/inbox")
        )

    def test_note_has_frontmatter_karpathy_cycle_and_raw_block(self):
        note = self.build()
        self.assertTrue(note.startswith("---\n"))
        self.assertIn('video_id: "kCc8FmEb1nY"', note)
        self.assertIn('duration: "01:56:20"', note)
        self.assertIn("published: 2023-01-17", note)
        self.assertIn("## 🔁 Ciclo Karpathy", note)
        self.assertIn("## 🔨 Reimplementar do zero", note)
        self.assertIn(render.AUTO_START, note)
        self.assertIn(render.AUTO_END, note)
        self.assertIn("> linha 1", note)

    def test_channel_tag_is_derived_from_the_channel_name(self):
        self.assertIn('"canal/andrej-karpathy"', self.build())

    def test_transcript_flag_reflects_reality(self):
        self.assertIn("transcript: true", self.build(with_transcript=True))
        self.assertIn("transcript: false", self.build(with_transcript=False))

    def test_filename_template(self):
        name = render.build_filename(self.meta, self.record)
        self.assertEqual(name, "2026-08-20 Let's build GPT from scratch (kCc8FmEb1nY).md")

    def test_merge_keeps_user_prose_and_preserved_frontmatter(self):
        original = self.build().replace("- [ ] \n", "- [ ] escrever o bigram model\n")
        original = original.replace('status: "raw"', 'status: "em-progresso"')
        original = original.replace("rating:", "rating: 5")
        original = original.replace("processed: false", 'processed: false\nmeu_campo: "guardar"')

        self.record.watched_at.append(datetime(2026, 8, 22, tzinfo=timezone.utc))
        merged = render.merge_note(original, self.build())

        self.assertIn("escrever o bigram model", merged)
        self.assertIn('status: "em-progresso"', merged)
        self.assertIn("rating: 5", merged)
        self.assertIn('meu_campo: "guardar"', merged)
        self.assertIn("watched: 2026-08-22", merged)  # campo automatico foi atualizado
        self.assertEqual(merged.count(render.AUTO_START), 1)

    def test_merge_is_idempotent(self):
        first = render.merge_note(self.build(), self.build())
        self.assertEqual(first, render.merge_note(first, self.build()))

    def test_merge_appends_block_to_a_handwritten_note(self):
        merged = render.merge_note("---\nstatus: \"raw\"\n---\n\nminhas notas\n", self.build())
        self.assertIn("minhas notas", merged)
        self.assertIn(render.AUTO_START, merged)


class CliTests(unittest.TestCase):
    def setUp(self):
        self.parser = cli.build_parser()
        self.records = takeout.aggregate(
            takeout.load_history(FIXTURES / "watch-history.json")
        )

    def parse(self, *argv):
        return self.parser.parse_args(
            ["--takeout", "x", "--vault", "y", *argv]
        )

    def test_channel_filter(self):
        args = self.parse("--channel", "karpathy")
        self.assertEqual(
            [r.video_id for r in cli.filter_records(self.records, args)], ["kCc8FmEb1nY"]
        )

    def test_exclude_channel_filter(self):
        args = self.parse("--exclude-channel", "karpathy")
        self.assertEqual(
            [r.video_id for r in cli.filter_records(self.records, args)], ["P2LTAUO1TdA"]
        )

    def test_date_window(self):
        args = self.parse("--since", "2026-08-21")
        self.assertEqual(
            [r.video_id for r in cli.filter_records(self.records, args)], ["P2LTAUO1TdA"]
        )

    def test_title_regex(self):
        args = self.parse("--match", r"^Let's build")
        self.assertEqual(
            [r.video_id for r in cli.filter_records(self.records, args)], ["kCc8FmEb1nY"]
        )

    def test_video_id_filter(self):
        args = self.parse("--video-id", "P2LTAUO1TdA")
        self.assertEqual(
            [r.video_id for r in cli.filter_records(self.records, args)], ["P2LTAUO1TdA"]
        )


class EndToEndTests(unittest.TestCase):
    def run_cli(self, vault: Path, *extra):
        return run_quiet(
            [
                "--takeout",
                str(FIXTURES / "watch-history.json"),
                "--vault",
                str(vault),
                "--offline",
                *extra,
            ]
        )

    def notes(self, vault: Path):
        return sorted((vault / "0_RAW").rglob("*.md"))

    def test_writes_notes_then_skips_them_on_a_second_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            self.assertEqual(self.run_cli(vault), 0)
            self.assertEqual(len(self.notes(vault)), 2)

            before = {p: p.read_text() for p in self.notes(vault)}
            self.assertEqual(self.run_cli(vault), 0)
            after = {p: p.read_text() for p in self.notes(vault)}
            self.assertEqual(before, after)

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            self.assertEqual(self.run_cli(vault, "--dry-run"), 0)
            self.assertFalse(list(vault.rglob("*.md")))
            self.assertFalse(list(vault.rglob("*.json")))

    def test_limit_and_update_flow(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            self.run_cli(vault, "--limit", "1")
            self.assertEqual(len(self.notes(vault)), 1)

            note = self.notes(vault)[0]
            note.write_text(note.read_text().replace("- [ ] \n", "- [ ] minha tarefa\n"))
            self.run_cli(vault, "--update")
            self.assertIn("minha tarefa", note.read_text())
            self.assertEqual(len(self.notes(vault)), 2)


if __name__ == "__main__":
    unittest.main()


class PlaylistTests(unittest.TestCase):
    def setUp(self):
        self.playlists = playlists.load_playlists(FIXTURES / "playlists")

    def test_system_playlists_do_not_become_folders(self):
        self.assertEqual(self.playlists.names, ["IA", "Investimentos"])

    def test_metadata_preamble_before_the_video_table_is_skipped(self):
        self.assertEqual(
            self.playlists.by_video["P2LTAUO1TdA"], ["Investimentos"]
        )

    def test_discovery_finds_the_playlists_folder_from_the_takeout_root(self):
        found = playlists.discover_playlists_dir(FIXTURES)
        self.assertEqual(found, FIXTURES / "playlists")

    def test_discovery_returns_none_when_there_is_nothing_to_find(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(playlists.discover_playlists_dir(Path(tmp)))


class ClassifierTests(unittest.TestCase):
    def setUp(self):
        self.playlists = playlists.load_playlists(FIXTURES / "playlists")

    def test_playlist_membership_decides_the_folder(self):
        decision = classify.Classifier(playlists=self.playlists).classify(
            "kCc8FmEb1nY", "titulo"
        )
        self.assertEqual((decision.folder, decision.reason), ("IA", "playlist"))

    def test_explicit_assignment_beats_the_playlist(self):
        decision = classify.Classifier(
            playlists=self.playlists, assignments={"kCc8FmEb1nY": "Inovação"}
        ).classify("kCc8FmEb1nY", "titulo")
        self.assertEqual((decision.folder, decision.reason), ("Inovação", "assign"))
        self.assertEqual(decision.playlists, ["IA"])

    def test_keyword_rules_catch_videos_outside_every_playlist(self):
        decision = classify.Classifier(
            playlists=self.playlists, rules={"Inovação": ["startup"]}
        ).classify("naoexiste00", "Como uma STARTUP escala")
        self.assertEqual((decision.folder, decision.reason), ("Inovação", "rule"))

    def test_keyword_matches_on_a_word_boundary_not_a_substring(self):
        # "smr" dentro de "#asmr" e "rag" dentro de "drag" eram falsos positivos.
        c = classify.Classifier(rules={"Deep Tech": ["smr"], "AI": ["rag"]})
        self.assertIsNone(c.classify("v", "IBANEZ PRESTIGE #asmr").folder)
        self.assertIsNone(c.classify("v", "drag racing highlights").folder)
        self.assertEqual(c.classify("v", "building a smr reactor").folder, "Deep Tech")

    def test_keyword_matches_a_title_that_ends_with_the_term(self):
        # " ai " com espaços perdia "...Keystone of AI"; a fronteira pega.
        c = classify.Classifier(rules={"AI": ["ai"]})
        for title in ("Ontologies: The Keystone of AI", "What is AI?", "The age of AI, explained"):
            self.assertEqual(c.classify("v", title).folder, "AI", title)
        self.assertIsNone(c.classify("v", "She said it was fine").folder)

    def test_single_word_terms_do_not_match_the_channel_name(self):
        # O canal "The Ai Democracy" jogava até clipe de Bruce Lee em AI.
        c = classify.Classifier(rules={"AI": ["ai"]})
        self.assertIsNone(c.classify("v", "Bruce Lee, Amazing Speed", "The Ai Democracy").folder)

    def test_multi_word_terms_still_match_the_channel_name(self):
        c = classify.Classifier(rules={"Eng": ["the pragmatic engineer"]})
        self.assertEqual(
            c.classify("v", "Scaling Uber with Thuan Pham", "The Pragmatic Engineer").folder,
            "Eng",
        )

    def test_rules_ignore_accents_and_case(self):
        decision = classify.Classifier(rules={"Inovação": ["inovacao"]}).classify(
            "naoexiste00", "Painel sobre INOVAÇÃO no Brasil"
        )
        self.assertEqual(decision.folder, "Inovação")

    def test_no_match_means_root(self):
        decision = classify.Classifier(playlists=self.playlists).classify(
            "naoexiste00", "Receita de bolo"
        )
        self.assertIsNone(decision.folder)
        self.assertEqual(decision.reason, "unclassified")

    def test_folder_names_are_filesystem_safe(self):
        self.assertEqual(classify.sanitize_folder("IA / Machine Learning"), "IA - Machine Learning")


class ClassifiedRunTests(unittest.TestCase):
    def run_cli(self, vault: Path, *extra):
        return run_quiet(
            [
                "--takeout",
                str(FIXTURES / "watch-history.json"),
                "--vault",
                str(vault),
                "--playlists",
                str(FIXTURES / "playlists"),
                "--offline",
                *extra,
            ]
        )

    def test_notes_land_in_the_playlist_folders(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            self.assertEqual(self.run_cli(vault), 0)
            written = sorted(
                str(p.relative_to(vault / "0_RAW")) for p in (vault / "0_RAW").rglob("*.md")
            )
            self.assertEqual(
                written,
                [
                    "IA/2026-08-20 Let's build GPT from scratch, in code, spelled out (kCc8FmEb1nY).md",
                    "Investimentos/2026-08-21 Álgebra linear mudança de base (P2LTAUO1TdA).md",
                ],
            )

    def test_category_and_playlists_reach_the_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            self.run_cli(vault)
            note = (vault / "0_RAW" / "IA").glob("*.md").__next__().read_text()
            self.assertIn('category: "IA"', note)
            self.assertIn('playlists: ["IA"]', note)
            self.assertIn('"tema/ia"', note)

    def test_unclassified_videos_stay_at_the_root_and_get_listed(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault, listing = Path(tmp), Path(tmp) / "pendentes.json"
            run_quiet(
                [
                    "--takeout", str(FIXTURES / "watch-history.json"),
                    "--vault", str(vault),
                    "--no-auto-playlists", "--offline",
                    "--list-unclassified", str(listing),
                ]
            )
            self.assertEqual(len(list((vault / "0_RAW").glob("*.md"))), 2)
            pending = json.loads(listing.read_text())
            self.assertEqual(
                sorted(item["video_id"] for item in pending),
                ["P2LTAUO1TdA", "kCc8FmEb1nY"],
            )
            self.assertTrue(all(item["title"] for item in pending))

    def test_reclassifying_moves_the_note_instead_of_duplicating_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            self.run_cli(vault, "--video-id", "kCc8FmEb1nY")
            original = next((vault / "0_RAW" / "IA").glob("*.md"))
            original.write_text(
                original.read_text().replace("- [ ] \n", "- [ ] meu texto\n")
            )

            assign = vault / "assign.json"
            assign.write_text(json.dumps({"kCc8FmEb1nY": "Inovação"}))
            self.run_cli(vault, "--video-id", "kCc8FmEb1nY", "--assign-file", str(assign), "--update")

            self.assertFalse(list((vault / "0_RAW" / "IA").glob("*.md")))
            moved = list((vault / "0_RAW" / "Inovação").glob("*.md"))
            self.assertEqual(len(moved), 1)
            content = moved[0].read_text()
            self.assertIn("meu texto", content)
            self.assertIn('category: "Inovação"', content)


HAS_TRANSCRIPT_API = importlib.util.find_spec("youtube_transcript_api") is not None


@unittest.skipUnless(HAS_TRANSCRIPT_API, "youtube-transcript-api não instalado")
class RealTranscriptApiTests(unittest.TestCase):
    """Exercita fetch_transcript contra os objetos reais da biblioteca.

    Sem rede: montamos um TranscriptList de verdade e devolvemos um
    FetchedTranscript de verdade. Se a biblioteca mudar a API — nomes de
    método, atributos, formato dos snippets — isto quebra aqui em vez de
    quebrar silenciosamente na máquina do usuário.
    """

    CAPTIONS = {
        "captionTracks": [
            {
                "baseUrl": "https://example.invalid/captions",
                "name": {"runs": [{"text": "English (auto-generated)"}]},
                "languageCode": "en",
                "kind": "asr",
            }
        ],
        "translationLanguages": [],
    }

    def _patched(self, snippets):
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._transcripts import (
            FetchedTranscript,
            FetchedTranscriptSnippet,
            Transcript,
            TranscriptList,
        )

        listing = TranscriptList.build(mock.Mock(), "kCc8FmEb1nY", self.CAPTIONS)
        fetched = FetchedTranscript(
            snippets=[
                FetchedTranscriptSnippet(text=text, start=start, duration=2.0)
                for start, text in snippets
            ],
            video_id="kCc8FmEb1nY",
            language="English",
            language_code="en",
            is_generated=True,
        )
        return (
            mock.patch.object(YouTubeTranscriptApi, "list", return_value=listing),
            mock.patch.object(Transcript, "fetch", return_value=fetched),
        )

    def test_fetch_reads_snippet_objects_not_just_dicts(self):
        list_patch, fetch_patch = self._patched(
            [(0.0, "hello"), (12.0, "world"), (95.0, "again")]
        )
        with list_patch, fetch_patch:
            result = transcript.fetch_transcript("kCc8FmEb1nY", ["pt", "en"])

        self.assertIsNotNone(result)
        self.assertEqual(result.language, "en")
        self.assertTrue(result.generated)
        self.assertEqual([s["text"] for s in result.segments], ["hello", "world", "again"])

    def test_transcript_reaches_the_note_with_working_timestamp_links(self):
        list_patch, fetch_patch = self._patched([(0.0, "hello"), (95.0, "again")])
        with list_patch, fetch_patch:
            fetched = transcript.fetch_transcript("kCc8FmEb1nY", ["en"])

        note = render.build_note(
            merge_meta(_record(), None), _record(), fetched, base_tags=("youtube",)
        )
        self.assertIn("transcript: true", note)
        self.assertIn('language: "en"', note)
        self.assertIn("[01:35](https://youtu.be/kCc8FmEb1nY?t=95)", note)
        self.assertIn("Legenda automática", note)

    def test_network_failure_degrades_to_no_transcript(self):
        from youtube_transcript_api import YouTubeTranscriptApi

        with mock.patch.object(
            YouTubeTranscriptApi, "list", side_effect=OSError("sem rede")
        ):
            self.assertIsNone(transcript.fetch_transcript("kCc8FmEb1nY", ["en"]))


class EnrichTests(unittest.TestCase):
    """Estágio 2: preencher as seções de análise a partir da transcrição."""

    def _note(self, transcript_line: str = "", conceitos: str = "- \n") -> str:
        meta = merge_meta(_record(), None)
        note = render.build_note(meta, _record(), None, base_tags=("youtube",))
        if transcript_line:
            # Substitui o aviso: uma nota que ainda diz "indisponível" é pulada
            # de propósito, então o fixture precisa removê-lo.
            start = note.find("*Transcrição indisponível")
            end = note.find("\n", note.find("rede.*", start))
            note = note[:start] + transcript_line + note[end:]
        return note.replace("## 🧠 Conceitos-chave\n\n- \n", f"## 🧠 Conceitos-chave\n\n{conceitos}")

    DATA = {
        "resumo": ["Tese um.", "Tese dois."],
        "conceitos": ["Conceito inventado"],
        "reimplementar": ["Construir o mínimo"],
        "perguntas": ["E se falhar?"],
        "momentos": ["02:30 — o ponto"],
        "conexoes": ["[[Um Conceito]]"],
    }

    def test_scaffold_counts_as_empty_but_your_text_does_not(self):
        for scaffold in ("\n- \n- \n", "\n- [ ] \n", "\n- [[ ]]\n", "\n"):
            self.assertTrue(enrich.section_is_empty(scaffold), repr(scaffold))
        for written in ("\n- meu texto\n", "\n- [[Conceito Real]]\n", "\n- [x] feito\n"):
            self.assertFalse(enrich.section_is_empty(written), repr(written))

    def test_fills_every_empty_section(self):
        filled, written = enrich.apply_sections(self._note(), self.DATA)
        self.assertEqual(len(written), 6)
        self.assertIn("- Tese um.", filled)
        self.assertIn("- [[Um Conceito]]", filled)

    def test_reimplementar_gets_checkboxes(self):
        filled, _ = enrich.apply_sections(self._note(), self.DATA)
        self.assertIn("- [ ] Construir o mínimo", filled)
        self.assertIn("- E se falhar?", filled)  # as demais, bullets simples

    def test_never_overwrites_a_section_you_wrote(self):
        note = self._note(conceitos="- MEU TEXTO\n")
        filled, written = enrich.apply_sections(note, self.DATA)
        self.assertIn("- MEU TEXTO", filled)
        self.assertNotIn("Conceito inventado", filled)
        self.assertNotIn("conceitos", written)

    def test_empty_list_leaves_the_section_alone(self):
        data = dict(self.DATA, reimplementar=[])
        filled, written = enrich.apply_sections(self._note(), data)
        self.assertNotIn("reimplementar", written)
        self.assertIn("## 🔨 Reimplementar do zero\n\n- [ ] \n", filled)

    def test_transcript_is_read_back_out_of_the_note(self):
        note = self._note("**[00:00](https://youtu.be/x?t=0)** palavra " * 50)
        _, body = render.split_frontmatter(note)
        self.assertIn("palavra", enrich.extract_transcript(body))

    def test_a_note_still_marked_unavailable_is_treated_as_having_none(self):
        note = self._note()
        _, body = render.split_frontmatter(note)
        self.assertEqual(enrich.extract_transcript(body), "")

    def test_a_note_without_a_transcript_is_not_summarized(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "0_RAW"
            folder.mkdir(parents=True)
            (folder / "sem.md").write_text(self._note(), encoding="utf-8")

            def explode(**_):
                raise AssertionError("não pode chamar a API sem transcrição")

            client = mock.Mock()
            client.messages.create = explode
            with contextlib.redirect_stdout(io.StringIO()) as out:
                code = enrich.main(["--vault", tmp, "--raw-dir", "0_RAW"], client=client)
            self.assertEqual(code, 0)
            self.assertIn("Sem transcrição (puladas): 1", out.getvalue())

    def test_frontmatter_records_that_claude_wrote_it(self):
        stamped = enrich.stamp_frontmatter(self._note(), "claude-opus-5")
        self.assertIn("enriched: true", stamped)
        self.assertIn('enriched_model: "claude-opus-5"', stamped)
        # e não duplica ao reprocessar
        self.assertEqual(enrich.stamp_frontmatter(stamped, "claude-opus-5").count("enriched: true"), 1)

    def test_request_uses_opus_5_json_schema_and_a_cached_system(self):
        captured = {}

        class Stub:
            class messages:
                @staticmethod
                def create(**kw):
                    captured.update(kw)
                    payload = json.dumps(EnrichTests.DATA)
                    return mock.Mock(content=[mock.Mock(type="text", text=payload)])

        note = enrich.Note(Path("x.md"), "", "T", "C", "palavra " * 200)
        enrich.summarize(Stub(), note)
        self.assertEqual(captured["model"], "claude-opus-5")
        self.assertEqual(captured["thinking"], {"type": "adaptive"})
        self.assertEqual(captured["output_config"]["format"]["type"], "json_schema")
        self.assertEqual(captured["system"][0]["cache_control"], {"type": "ephemeral"})
        self.assertNotIn("budget_tokens", json.dumps(captured, default=str))
