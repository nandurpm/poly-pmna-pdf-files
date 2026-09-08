import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from test_archive_index import module, pdf


class AliasTests(unittest.TestCase):
    def setup_archive(self, root):
        target = root / "sitttr/one.pdf"
        pdf(target)
        content = target.read_bytes()
        record = {"path": "sitttr/department-two/two.pdf",
                  "canonicalPath": "sitttr/one.pdf", "bytes": len(content),
                  "gitBlob": hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()}
        (root / "manifests").mkdir()
        self.write_alias(root, [record])
        return record

    def write_alias(self, root, records):
        (root / "manifests/pdf-aliases.json").write_text(
            json.dumps({"schemaVersion": 1, "aliases": records}))

    def test_department_entries_survive_and_reindex_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = self.setup_archive(root)
            index = module("index_archive").index
            index(root)
            target = root / "manifests/archive-index.json"
            original = target.read_bytes()
            docs = json.loads(original)["documents"]
            self.assertEqual(len(docs), 2)
            self.assertEqual({d["path"] for d in docs},
                             {record["path"], record["canonicalPath"]})
            self.assertEqual(len({d["pdfUrl"] for d in docs}), 1)
            self.assertFalse((root / record["path"]).exists())
            index(root)
            self.assertEqual(target.read_bytes(), original)

    def test_corrupt_target_does_not_publish(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = self.setup_archive(root)
            index = module("index_archive").index
            index(root)
            target = root / "manifests/archive-index.json"
            before = target.read_bytes()
            canonical = root / record["canonicalPath"]
            canonical.write_bytes(canonical.read_bytes() + b"changed")
            with self.assertRaises(ValueError):
                index(root)
            self.assertEqual(target.read_bytes(), before)

    def test_missing_target_duplicate_alias_and_unsafe_path_rejected(self):
        for defect in ("missing", "duplicate", "traversal", "chain", "reintroduced"):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                record = self.setup_archive(root)
                records = [record]
                if defect == "missing":
                    (root / record["canonicalPath"]).unlink()
                elif defect == "duplicate":
                    records.append(dict(record))
                elif defect == "traversal":
                    record["path"] = "../escape.pdf"
                elif defect == "chain":
                    record["canonicalPath"] = record["path"]
                else:
                    pdf(root / record["path"])
                self.write_alias(root, records)
                with self.assertRaises(ValueError):
                    module("index_archive").index(root)
                self.assertFalse((root / "manifests/archive-index.json").exists())


if __name__ == "__main__":
    unittest.main()
