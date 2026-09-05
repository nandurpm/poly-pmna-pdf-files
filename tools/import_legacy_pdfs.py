"""Preserve every tracked consumer PDF without replacing canonical notes."""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def migrate(source, archive, push=False):
    commit = git(source, "rev-parse", "HEAD").decode().strip()
    records = []
    for raw in git(source, "ls-files", "-z").split(b"\0"):
        if not raw or not raw.lower().endswith(b".pdf"):
            continue
        relative = raw.decode()
        path = source / relative
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"Missing or unsafe source: {relative}")
        with path.open("rb") as stream:
            if stream.read(5) != b"%PDF-":
                raise ValueError(f"Invalid PDF: {relative}")
        expected = git(source, "rev-parse", f"HEAD:{relative}").decode().strip()
        actual = git(source, "hash-object", str(path)).decode().strip()
        if actual != expected:
            raise ValueError(f"Source differs from tracked blob: {relative}")
        destination = archive / "legacy" / "diploma-notes" / commit / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists() and git(archive, "hash-object", str(destination)).decode().strip() != expected:
            raise ValueError(f"Refusing to overwrite archived version: {destination}")
        shutil.copyfile(path, destination)
        if git(archive, "hash-object", str(destination)).decode().strip() != expected:
            raise ValueError(f"Copy verification failed: {relative}")
        with destination.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        records.append({"sourcePath": relative, "archivePath": destination.relative_to(archive).as_posix(),
                        "gitBlob": expected, "sha256": digest, "bytes": destination.stat().st_size})
    output = archive / "manifests" / "legacy-diploma-notes.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"sourceCommit": commit, "documents": records}, indent=2) + "\n")
    if push:
        # The originals total over 3 GB. Keep each push below GitHub's pack limit,
        # even if PDF compression provides no savings. Publish the manifest last.
        pending = git(archive, "ls-files", "--others", "--exclude-standard", "-z", "legacy").split(b"\0")
        batch, size = [], 0

        def publish(paths):
            if not paths:
                return
            git(archive, "add", "--", *paths)
            git(archive, "commit", "-m", "Preserve verified legacy PDF batch")
            git(archive, "push", "origin", "HEAD:main")

        for raw in pending:
            if not raw:
                continue
            path = raw.decode()
            length = (archive / path).stat().st_size
            if batch and size + length > 400_000_000:
                publish(batch)
                batch, size = [], 0
            batch.append(path)
            size += length
        publish(batch)
    print(f"Preserved and verified {len(records)} PDFs from {commit}")


if __name__ == "__main__":
    migrate(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), "--push" in sys.argv[3:])
