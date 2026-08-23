"""Testes offline do pipeline: `python3 -m unittest discover -s tools/youtube_raw/tests`."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from tools.youtube_raw import cli, render, takeout, transcript, util
from tools.youtube_raw.metadata import VideoMeta, merge_meta

FIXTURES = Path(__file__).parent / "fixtures"


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
        return cli.main(
            [
                "--takeout",
                str(FIXTURES / "watch-history.json"),
                "--vault",
                str(vault),
                "--offline",
                *extra,
            ]
        )

    def test_writes_notes_then_skips_them_on_a_second_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            self.assertEqual(self.run_cli(vault), 0)
            notes = sorted(p.name for p in (vault / "0_RAW").glob("*.md"))
            self.assertEqual(len(notes), 2)

            before = {p: p.read_text() for p in (vault / "0_RAW").glob("*.md")}
            self.assertEqual(self.run_cli(vault), 0)
            after = {p: p.read_text() for p in (vault / "0_RAW").glob("*.md")}
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
            self.assertEqual(len(list((vault / "0_RAW").glob("*.md"))), 1)

            note = next((vault / "0_RAW").glob("*.md"))
            note.write_text(note.read_text().replace("- [ ] \n", "- [ ] minha tarefa\n"))
            self.run_cli(vault, "--update")
            self.assertIn("minha tarefa", note.read_text())
            self.assertEqual(len(list((vault / "0_RAW").glob("*.md"))), 2)


if __name__ == "__main__":
    unittest.main()
