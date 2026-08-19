#!/usr/bin/env python3
"""Normalize SITTTR PDF folders and keep repository manifests in sync."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE_DIR = ROOT / "sitttr"
MANIFEST_DIR = ROOT / "manifests"
REVISIONS = ("revision-2015", "revision-2021", "revision-2026")
CATEGORIES = ("model-question-papers", "syllabus")
SEMESTERS = tuple(f"semester-{number}" for number in range(1, 7)) + ("semester-unspecified",)
RAW_PREFIX = "https://raw.githubusercontent.com/nandurpm/poly-pmna-pdf-files/main/"


def replace_strings(value: object, moves: dict[str, str]) -> tuple[object, int]:
    """Recursively replace moved repository paths and their raw URLs in JSON data."""
    if isinstance(value, dict):
        updated: dict[str, object] = {}
        count = 0
        for key, item in value.items():
            replaced, changed = replace_strings(item, moves)
            updated[key] = replaced
            count += changed
        return updated, count
    if isinstance(value, list):
        updated_list = []
        count = 0
        for item in value:
            replaced, changed = replace_strings(item, moves)
            updated_list.append(replaced)
            count += changed
        return updated_list, count
    if isinstance(value, str):
        for old, new in moves.items():
            if value == old or value == RAW_PREFIX + old:
                return (new if value == old else RAW_PREFIX + new), 1
        return value, 0
    return value, 0


def update_manifests(moves: dict[str, str]) -> int:
    if not moves or not MANIFEST_DIR.exists():
        return 0
    changed_files = 0
    for path in sorted(MANIFEST_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        updated, changes = replace_strings(data, moves)
        if changes:
            path.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            changed_files += 1
    return changed_files


def main() -> None:
    print("Starting poly-pmna-pdf-files SITTTR directory audit and reorganization...")
    moves: dict[str, str] = {}
    total_files = 0

    for revision in REVISIONS:
        revision_path = BASE_DIR / revision
        if not revision_path.exists():
            continue
        for category in CATEGORIES:
            category_path = revision_path / category
            if not category_path.exists():
                continue
            for department_path in sorted(path for path in category_path.iterdir() if path.is_dir()):
                for semester in SEMESTERS:
                    (department_path / semester).mkdir(exist_ok=True)
                for item_path in sorted(department_path.iterdir()):
                    if not item_path.is_file() or item_path.suffix.lower() != ".pdf":
                        continue
                    destination = department_path / "semester-unspecified" / item_path.name
                    if destination.exists():
                        continue
                    old_relative = item_path.relative_to(ROOT).as_posix()
                    new_relative = destination.relative_to(ROOT).as_posix()
                    shutil.move(str(item_path), str(destination))
                    moves[old_relative] = new_relative
                    total_files += 1

    manifest_files = update_manifests(moves)
    print(f"Moved {total_files} loose PDFs and updated {manifest_files} manifest files.")


if __name__ == "__main__":
    main()
