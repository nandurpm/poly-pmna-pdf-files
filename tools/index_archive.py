"""Index every PDF; publish versioned lesson uploads after PDF validation."""
import hashlib
import json
import re
import subprocess
from pathlib import Path, PurePosixPath
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://raw.githubusercontent.com/nandurpm/poly-pmna-pdf-files/main/"
NOTE = re.compile(r"notes/(2021|2026)/([A-Za-z0-9]+)/v([1-9][0-9]*)/\2\.pdf", re.I)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def alias_documents(root, physical):
    """Retain each catalogue identity while serving one verified physical PDF."""
    target = root / "manifests/pdf-aliases.json"
    if not target.exists():
        return []
    manifest = json.loads(target.read_text(encoding="utf-8"))
    if manifest.get("schemaVersion") != 1:
        raise ValueError("Unsupported PDF alias schema")
    records = manifest["aliases"]
    paths = set()
    for record in records:
        for key in ("path", "canonicalPath"):
            value = record[key]
            p = PurePosixPath(value)
            if (not value or p.is_absolute() or ".." in p.parts or "\\" in value
                    or str(p) != value or p.suffix.lower() != ".pdf"
                    or not (root / value).resolve().is_relative_to(root.resolve())):
                raise ValueError(f"Unsafe PDF alias: {value}")
        if record["path"] in paths or record["path"] == record["canonicalPath"]:
            raise ValueError("Duplicate or self-referencing PDF alias")
        paths.add(record["path"])
    documents = []
    verified = {}
    for record in records:
        original, canonical = record["path"], record["canonicalPath"]
        if canonical in paths or canonical not in physical:
            raise ValueError(f"Missing or chained PDF alias target: {canonical}")
        if original in physical:
            raise ValueError(f"Duplicate PDF was reintroduced: {original}")
        if canonical not in verified:
            path = root / canonical
            digest = hashlib.sha1()
            digest.update(b"blob " + str(path.stat().st_size).encode() + b"\0")
            with path.open("rb") as stream:
                while chunk := stream.read(1024 * 1024):
                    digest.update(chunk)
            verified[canonical] = (path.stat().st_size, digest.hexdigest())
        if verified[canonical] != (record["bytes"], record["gitBlob"]):
            raise ValueError(f"PDF alias content changed: {canonical}")
        documents.append({"path": original,
                          "title": PurePosixPath(original).stem.replace("-", " "),
                          "pdfUrl": BASE + quote(canonical, safe="/"),
                          "bytes": record["bytes"], "canonicalPath": canonical})
    return documents


def index(root=ROOT):
    documents = []
    latest = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if ".git" in path.parts or path.is_symlink() or not path.is_file() or path.suffix.lower() != ".pdf":
            continue
        with path.open("rb") as stream:
            if stream.read(5) != b"%PDF-":
                raise ValueError(f"Not a PDF (or unresolved LFS pointer): {relative}")
        item = {"path": relative, "title": path.stem.replace("-", " "),
                "pdfUrl": BASE + quote(relative, safe="/"), "bytes": path.stat().st_size}
        documents.append(item)
        match = NOTE.fullmatch(relative)
        if match:
            revision, code, version = match.groups()
            key = (revision, code.upper())
            if key not in latest or int(version) > latest[key][0]:
                latest[key] = (int(version), path, item)

    documents.extend(alias_documents(root, {item["path"]: item for item in documents}))
    documents.sort(key=lambda item: item["path"])

    # Validate all selected notes before writing any manifests.
    manifests = {}
    for revision in ("2021", "2026"):
        target = root / "manifests" / f"notes-{revision}.json"
        manifest = json.loads(target.read_text()) if target.exists() else {"revision": revision, "subjects": []}
        records = {str(s["code"]).upper(): dict(s) for s in manifest["subjects"]}
        for code, record in records.items():
            if (revision, code) not in latest:
                record["status"] = "missing"
                record.pop("pdfUrl", None)
        for (rev, code), (version, path, item) in latest.items():
            if rev != revision:
                continue
            with path.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            old = records.get(code, {})
            if old.get("sha256") == digest and old.get("pages", 0) > 0:
                pages = old["pages"]
            else:
                result = subprocess.run(["pdfinfo", str(path)], check=True, capture_output=True, text=True)
                match = re.search(r"^Pages:\s+(\d+)", result.stdout, re.M)
                if not match or int(match[1]) < 1:
                    raise ValueError(f"No readable pages: {path}")
                pages = int(match[1])
            records[code] = {**old, "code": code, "title": old.get("title") or f"Course {code}",
                "revision": revision, "version": f"v{version}", "status": "published",
                "pdfUrl": item["pdfUrl"], "bytes": item["bytes"], "sha256": digest, "pages": pages}
        manifest.update(schemaVersion=2, storage="git-tree", pdfBaseUrl=BASE.rstrip("/"),
                        subjects=[records[k] for k in sorted(records)])
        manifests[target] = manifest
    for target, manifest in manifests.items():
        write_json(target, manifest)
    write_json(root / "manifests" / "archive-index.json", {"schemaVersion": 1, "documents": documents})
    print(f"Indexed {len(documents)} PDFs; {len(latest)} versioned lesson subjects")


if __name__ == "__main__":
    index()
