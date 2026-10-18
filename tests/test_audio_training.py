import json
from pathlib import Path
import tempfile
import unittest

from audio_training.pipeline import chapters, split_chunks, package, select


class AudioTrainingTest(unittest.TestCase):
    def test_chapters_skip_references_and_tables(self):
        article = {"content_html": "<p>Intro.</p><h2>Methods</h2><p>Work safely.</p>"
                   "<table><tr><td>DO NOT NARRATE</td></tr></table>"
                   "<h2>References</h2><ol><li>Not spoken.</li></ol>"}
        self.assertEqual(chapters(article), [
            {"title": "Introduction", "text": "Intro."},
            {"title": "Methods", "text": "Work safely."}
        ])

    def test_numbers_are_not_modified(self):
        source = "Use only the approved 1:20 ratio. Consult the label."
        self.assertEqual(" ".join(split_chunks(source)), source)

    def test_new_voice_changes_cache_key(self):
        article = {"article_id": "ACX-KB-0001", "locale": "en", "title": "Test",
                   "content_html": "<p>Content.</p>", "_source_path": "test"}
        self.assertNotEqual(package(article, "voice-a")["source_sha256"],
                            package(article, "voice-b")["source_sha256"])

    def test_only_live_locked_content_enters_queue(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "production").mkdir()
            (root / "production/live.json").write_text(
                json.dumps({"live_article_ids": ["ACX-KB-0001"]}))
            for id_, status in (("ACX-KB-0001", "english-locked"),
                                ("ACX-KB-0002", "review")):
                location = root / "articles" / "cleaning" / id_
                location.mkdir(parents=True)
                (location / "en.json").write_text(json.dumps({
                    "article_id": id_, "locale": "en",
                    "editorial_status": status, "content_html": "<p>Hello.</p>"}))
            self.assertEqual(len(list(select(root, {"en"}))), 1)


if __name__ == "__main__":
    unittest.main()
