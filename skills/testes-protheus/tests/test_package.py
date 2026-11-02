"""Exportação e limites do scanner. author: daniel.montagna."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate_package import validate
from export_skill import export


class PackageTests(unittest.TestCase):
    def fixture(self, root):
        (root / "SKILL.md").write_text("---\nname: testes-protheus\ndescription: Use quando testar Protheus.\n---\n\nauthor: daniel.montagna\n", encoding="utf-8")

    def test_minimal_valid_and_export(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "skill"
            root.mkdir()
            self.fixture(root)
            self.assertEqual(validate(root), [])
            zip_path = Path(temp) / "skill.zip"
            manifest = export(root, zip_path)
            self.assertEqual(len(manifest["files"]), 1)
            self.assertTrue(zip_path.is_file())

    def test_backup_blocks(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root)
            (root / "old.py.bak").write_text("old", encoding="utf-8")
            self.assertTrue(validate(root))

    def test_config_secret_blocks(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root)
            (root / "assets").mkdir()
            (root / "assets" / "private.json").write_text(json.dumps(dict(zip(["Password"], ["not-a-real-secret"]))), encoding="utf-8")
            self.assertTrue(validate(root))

    def test_broken_reference_blocks(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root)
            with (root / "SKILL.md").open("a", encoding="utf-8") as stream:
                stream.write("[missing](references/missing.md)")
            self.assertTrue(validate(root))

    def test_local_link_blocks(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root)
            with (root / "SKILL.md").open("a", encoding="utf-8") as stream:
                stream.write("[private](" + "C:" + "/Users/person/project/file.md)")
            self.assertTrue(validate(root))

    def test_private_endpoint_blocks(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root)
            with (root / "SKILL.md").open("a", encoding="utf-8") as stream:
                stream.write("http" + "://internal-server:1234/webapp/")
            self.assertTrue(validate(root))

    def test_export_cannot_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "skill"
            root.mkdir()
            self.fixture(root)
            output = Path(temp) / "skill.zip"
            export(root, output)
            with self.assertRaises(FileExistsError):
                export(root, output)

    def test_output_inside_package_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root)
            with self.assertRaises(ValueError):
                export(root, root / "nested.zip")


if __name__ == "__main__":
    unittest.main()
