"""Verify tracked canonical files and logical catalogues without downloading PDFs."""
import json
import subprocess
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://raw.githubusercontent.com/nandurpm/poly-pmna-pdf-files/main/"


def verify(root=ROOT):
    entries = {}
    output = subprocess.check_output(["git", "-C", str(root), "ls-tree", "-rlz", "HEAD"])
    for item in output.split(b"\0"):
        if not item:
            continue
        meta, path = item.split(b"\t", 1)
        mode, kind, sha, size = meta.decode().split()
        if kind == "blob":
            entries[path.decode()] = (sha, int(size), mode)
    aliases = json.loads((root / "manifests/pdf-aliases.json").read_text())["aliases"]
    original_paths = set()
    for alias in aliases:
        path, canonical = alias["path"], alias["canonicalPath"]
        if path in original_paths or path in entries:
            raise ValueError(f"Duplicate alias or reintroduced file: {path}")
        original_paths.add(path)
        if entries.get(canonical) != (alias["gitBlob"], alias["bytes"], "100644"):
            raise ValueError(f"Missing or changed retained file: {canonical}")
    pdfs = {path: entry for path, entry in entries.items() if path.lower().endswith(".pdf")}
    if len({entry[0] for entry in pdfs.values()}) != len(pdfs):
        raise ValueError("Duplicate PDF contents remain")
    alias_map = {a["path"]: a for a in aliases}
    for target in [root / "manifests/archive-index.json", *sorted((root / "manifests").glob("sitttr-*.json"))]:
        data = json.loads(target.read_text())
        for doc in data.get("documents", []):
            logical = doc["path"]
            canonical = doc.get("canonicalPath", logical)
            expected = alias_map.get(logical, {}).get("canonicalPath", logical)
            if canonical != expected or canonical not in pdfs:
                raise ValueError(f"Invalid catalogue path: {logical}")
            if doc["pdfUrl"] != BASE + quote(canonical, safe="/"):
                raise ValueError(f"Invalid download URL: {logical}")
            if doc["bytes"] != pdfs[canonical][1]:
                raise ValueError(f"Incorrect document bytes: {logical}")
    docs = json.loads((root / "manifests/archive-index.json").read_text())["documents"]
    logical = [d["path"] for d in docs]
    if len(logical) != len(set(logical)) or set(logical) != set(pdfs) | original_paths:
        raise ValueError("Catalogue lost or duplicated a logical document")
    print(f"Verified {len(pdfs)} unique PDFs and {len(aliases)} aliases; {len(docs)} catalogue entries")


if __name__ == "__main__":
    verify()
