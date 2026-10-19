import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import notes


class NotesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = notes.NotesDB(Path(self.tmp.name) / "test.db")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_add_and_list(self):
        note_id = self.db.add("First", "Body text", ["work"])
        rows = self.db.list()
        self.assertEqual(rows[0]["id"], note_id)
        self.assertEqual(rows[0]["tags"], "work")

    def test_multiple_tags(self):
        self.db.add("Title", tags=["a", "b"])
        self.assertEqual(self.db.list()[0]["tags"], "a,b")

    def test_search_body(self):
        self.db.add("Backup", "Test restores monthly")
        self.assertEqual(len(self.db.search("restore")), 1)

    def test_search_tag(self):
        self.db.add("Deploy", tags=["ops"])
        self.assertEqual(len(self.db.search("ops")), 1)

    def test_search_no_match(self):
        self.db.add("Deploy")
        self.assertEqual(self.db.search("zzz"), [])

    def test_delete_cascades_tags(self):
        note_id = self.db.add("Temp", tags=["x"])
        self.assertTrue(self.db.delete(note_id))
        self.assertEqual(self.db.stats(), {"notes": 0, "tags": 0})

    def test_delete_missing(self):
        self.assertFalse(self.db.delete(99))

    def test_duplicate_tag_ignored(self):
        note_id = self.db.add("T")
        self.db.add_tag(note_id, "same")
        self.db.add_tag(note_id, "same")
        self.assertEqual(self.db.stats()["tags"], 1)

    def test_cli_add_and_list(self):
        import contextlib
        import io
        db_path = Path(self.tmp.name) / "cli.db"
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = notes.main(["--db", str(db_path), "add", "CLI note", "--tag", "test"])
            notes.main(["--db", str(db_path), "list"])
        self.assertEqual(code, 0)
        self.assertIn("CLI note", out.getvalue())
        self.assertIn("[test]", out.getvalue())


if __name__ == "__main__":
    unittest.main()
