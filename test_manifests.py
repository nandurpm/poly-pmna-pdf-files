#!/usr/bin/env python3
"""Targeted tests for SITTTR manifest JSON files and Python scripts."""
import json
import os
import sys
import py_compile
import hashlib
from pathlib import Path

ROOT = Path(__file__).parent
MANIFESTS_DIR = ROOT / "manifests"
FAILED = 0
PASSED = 0


def pass_(msg):
    global PASSED
    PASSED += 1
    print(f"  ✓ {msg}")


def fail(msg):
    global FAILED
    FAILED += 1
    print(f"  ✗ {msg}")


def load_json(path):
    with open(path) as f:
        return json.load(f)


# ─── 1. All JSON manifests parse without error ───────────────────────────
print("\n[1] JSON parse validity")
json_files = list(MANIFESTS_DIR.glob("*.json"))
json_files += list((MANIFESTS_DIR / "reports").glob("*.json"))
for jf in json_files:
    try:
        load_json(jf)
        pass_(f"parses: {jf.relative_to(ROOT)}")
    except json.JSONDecodeError as e:
        fail(f"parse error in {jf.relative_to(ROOT)}: {e}")

# ─── 2. Manifest schema: required fields present ─────────────────────────
print("\n[2] Manifest document schema (required fields)")
# SITTTR manifests use "documents" with one schema
REQUIRED_DOC_FIELDS_SITTTR = {
    "revision", "documentType", "courseCode", "courseName",
    "path", "pdfUrl", "sha256", "status",
}
REQUIRED_TOP_FIELDS_SITTTR = {"schemaVersion", "documents"}

# Notes manifests use "subjects" with a different schema
REQUIRED_DOC_FIELDS_NOTES = {
    "code", "title", "revision", "version", "status", "pdfUrl", "sha256",
}
REQUIRED_TOP_FIELDS_NOTES = {"schemaVersion", "subjects"}

sitttr_files = [MANIFESTS_DIR / f for f in [
    "sitttr-2015.json", "sitttr-2021.json", "sitttr-2026.json",
    "sitttr-index.json", "sitttr-general.json",
]]
sitttr_files = [f for f in sitttr_files if f.exists()]
notes_files = [MANIFESTS_DIR / f for f in ["notes-2021.json", "notes-2026.json"]]
notes_files = [f for f in notes_files if f.exists()]

for mf in sitttr_files:
    data = load_json(mf)
    rel = mf.relative_to(ROOT)
    missing_top = REQUIRED_TOP_FIELDS_SITTTR - set(data.keys())
    if missing_top:
        fail(f"{rel}: missing top-level fields {missing_top}")
    else:
        pass_(f"{rel}: top-level fields OK")

    docs = data.get("documents", [])
    if not docs:
        continue

    bad_docs = 0
    for i, doc in enumerate(docs):
        missing = REQUIRED_DOC_FIELDS_SITTTR - set(doc.keys())
        if missing:
            if bad_docs == 0:
                fail(f"{rel}: doc[{i}] missing fields {missing}")
            bad_docs += 1
    if bad_docs == 0:
        pass_(f"{rel}: all {len(docs)} docs have required fields")
    elif bad_docs > 1:
        fail(f"{rel}: {bad_docs} total docs with missing fields")

for mf in notes_files:
    data = load_json(mf)
    rel = mf.relative_to(ROOT)
    missing_top = REQUIRED_TOP_FIELDS_NOTES - set(data.keys())
    if missing_top:
        fail(f"{rel}: missing top-level fields {missing_top}")
    else:
        pass_(f"{rel}: top-level fields OK")

    subjects = data.get("subjects", [])
    if not subjects:
        continue

    bad = 0
    for i, s in enumerate(subjects):
        missing = REQUIRED_DOC_FIELDS_NOTES - set(s.keys())
        if missing:
            if bad == 0:
                fail(f"{rel}: subject[{i}] missing fields {missing}")
            bad += 1
    if bad == 0:
        pass_(f"{rel}: all {len(subjects)} subjects have required fields")
    elif bad > 1:
        fail(f"{rel}: {bad} total subjects with missing fields")

# ─── 3. No duplicate paths within manifests ──────────────────────────────
print("\n[3] No duplicate file paths within a manifest")
all_manifest_files = sitttr_files + notes_files
for mf in all_manifest_files:
    data = load_json(mf)
    docs = data.get("documents", [])
    if docs:
        paths = [d.get("path", "") for d in docs]
    else:
        subjects = data.get("subjects", [])
        paths = [s.get("pdfUrl", "") for s in subjects]
    dupes = [p for p in set(paths) if paths.count(p) > 1]
    if dupes:
        fail(f"{mf.relative_to(ROOT)}: {len(dupes)} duplicate paths (e.g. {dupes[0]})")
    else:
        pass_(f"{mf.relative_to(ROOT)}: no duplicate paths ({len(paths)} entries)")


# ─── 4. File paths in manifests point to existing files on disk ──────────
print("\n[4] Manifest file paths exist on disk")
for mf in all_manifest_files:
    data = load_json(mf)
    docs = data.get("documents", [])
    subjects = data.get("subjects", [])
    entries = docs if docs else subjects
    if not entries:
        continue
    # Build local file paths from entries
    local_paths = []
    for e in entries[:20]:
        if "path" in e:
            local_paths.append(ROOT / e["path"])
        elif "pdfUrl" in e:
            prefix = "https://raw.githubusercontent.com/nandurpm/poly-pmna-pdf-files/main/"
            if e["pdfUrl"].startswith(prefix):
                local_paths.append(ROOT / e["pdfUrl"][len(prefix):])
            else:
                local_paths.append(ROOT / "NOMATCH")
    missing = [lp for lp in local_paths if not lp.exists()]
    if missing:
        fail(f"{mf.relative_to(ROOT)}: {len(missing)}/{len(local_paths)} sampled paths missing on disk "
             f"(e.g. {missing[0]})")
    else:
        pass_(f"{mf.relative_to(ROOT)}: sampled {len(local_paths)}/{len(entries)} paths exist on disk")


# ─── 5. SHA-256 checksums: spot-check a few files ────────────────────────
print("\n[5] SHA-256 checksum spot-check (up to 5 per manifest)")
for mf in all_manifest_files:
    data = load_json(mf)
    docs = data.get("documents", [])
    subjects = data.get("subjects", [])
    entries = docs if docs else subjects
    checked = 0
    bad = 0
    for e in entries[:5]:
        sha_expected = e.get("sha256", "")
        if "path" in e:
            fpath = ROOT / e["path"]
        elif "pdfUrl" in e:
            prefix = "https://raw.githubusercontent.com/nandurpm/poly-pmna-pdf-files/main/"
            if e["pdfUrl"].startswith(prefix):
                fpath = ROOT / e["pdfUrl"][len(prefix):]
            else:
                continue
        else:
            continue
        if not fpath.exists():
            continue
        sha_actual = hashlib.sha256(fpath.read_bytes()).hexdigest()
        if sha_actual != sha_expected:
            fail(f"SHA mismatch for {fpath.relative_to(ROOT)}")
            bad += 1
        checked += 1
    if checked > 0 and bad == 0:
        pass_(f"{mf.relative_to(ROOT)}: {checked} checksums verified OK")


# ─── 6. sitttr-index.json consistency with per-year manifests ────────────
print("\n[6] sitttr-index.json is superset of per-year manifests")
idx_path = MANIFESTS_DIR / "sitttr-index.json"
if idx_path.exists():
    idx_data = load_json(idx_path)
    idx_paths = {d["path"] for d in idx_data.get("documents", [])}
    year_manifests = [MANIFESTS_DIR / f for f in
                      ["sitttr-2015.json", "sitttr-2021.json", "sitttr-2026.json", "sitttr-general.json"]]
    all_year_paths = set()
    for ymf in year_manifests:
        if not ymf.exists():
            continue
        ydata = load_json(ymf)
        for d in ydata.get("documents", []):
            all_year_paths.add(d["path"])
    missing_from_index = all_year_paths - idx_paths
    if missing_from_index:
        fail(f"sitttr-index.json missing {len(missing_from_index)} paths from per-year manifests "
             f"(e.g. {sorted(missing_from_index)[0]})")
    else:
        pass_(f"sitttr-index.json contains all {len(all_year_paths)} paths from per-year manifests")
else:
    fail("sitttr-index.json not found")


# ─── 7. Python script syntax check ───────────────────────────────────────
print("\n[7] Python script syntax check")
py_files = sorted(ROOT.glob("*.py"))
for pf in py_files:
    try:
        py_compile.compile(str(pf), doraise=True)
        pass_(f"syntax OK: {pf.name}")
    except py_compile.PyCompileError as e:
        fail(f"syntax error in {pf.name}: {e}")


# ─── Summary ─────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"RESULTS: {PASSED} passed, {FAILED} failed, {PASSED + FAILED} total")
print(f"{'='*60}")
sys.exit(1 if FAILED else 0)
