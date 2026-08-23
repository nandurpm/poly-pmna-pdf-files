#!/usr/bin/env python3
"""Batch-discover missing SITTTR PDFs.

Since department listing pages return HTTP 500, we probe the direct PDF
endpoints for new course codes and create entries for all departments.

Run in batches: python3 discover_batch.py 2021 syllabus 1001 1100
"""
from __future__ import annotations

import json
import hashlib
import re
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request

ROOT = Path(__file__).resolve().parent
MANIFEST_DIR = ROOT / "manifests"
SITTTR_BASE = "https://www.sitttrkerala.ac.in/index.php"
RAW_BASE = "https://raw.githubusercontent.com/nandurpm/poly-pmna-pdf-files/main"

DEPT_MAP = {
    "AI": "Artificial Intelligence", "AM": "Artificial Intelligence & Machine Learning",
    "AR": "Architecture", "AU": "Automobile Engineering",
    "BM": "Biomedical Engineering", "CA": "Commercial Practice",
    "CB": "Computer Application & Business Management", "CC": "Computer Engineering",
    "CE": "Chemical Engineering", "CF": "Computer Hardware Engineering",
    "CH": "Civil & Environmental Engineering", "CL": "Civil & Rural Engineering",
    "CM": "Civil (Public Health and Environment) Engineering",
    "CN": "Communication & Computer Networking",
    "CO": "Computer Science & Engineering",
    "CR": "Computer Science & Engineering", "CS": "Computer Science & Engineering",
    "CT": "Computer Engineering", "CV": "Civil Engineering",
    "CZ": "Cyber Forensics and Information Security",
    "EC": "Electronics and Communication", "EE": "Electrical & Electronics Engineering",
    "EG": "Electrical Engineering", "EL": "Electronics Engineering",
    "ES": "Electronics and Computer Engineering",
    "ET": "Electrical Engineering & Electric Vehicles Technology",
    "EV": "Fire Technology and Safety", "FS": "Food Processing Technology",
    "FT": "Fire Technology and Safety", "HM": "Hotel Management and Catering Technology",
    "IC": "Integrated Circuit Design & Fabrication", "ID": "Interior Design",
    "IE": "Instrumentation Engineering", "IF": "Integrated Circuit Design & Fabrication",
    "MA": "Manufacturing Technology", "MC": "Mechanical Engineering",
    "ME": "Mechatronics", "MI": "Micro Electronics", "MT": "Manufacturing Technology",
    "PL": "Polymer Technology", "PT": "Printing Technology",
    "RA": "Renewable Energy", "RE": "Renewable Energy",
    "RP": "Robotic Process Automation", "TD": "Tool & Die Engineering",
    "TT": "Textile Technology", "WP": "Wood and Paper Technology",
}


def fetch(url: str, timeout: int = 10) -> bytes | None:
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception:
        return None


def is_pdf(data: bytes) -> bool:
    return data[:5] == b"%PDF-"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pdf_page_count(data: bytes) -> int:
    m = re.search(rb"/Count\s+(\d+)", data)
    return int(m.group(1)) if m else 0


def load_manifest(revision: str) -> dict:
    path = MANIFEST_DIR / f"sitttr-{revision}.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {"schemaVersion": 1, "revision": revision, "documents": []}


def save_manifest(manifest: dict, revision: str):
    from datetime import datetime, timezone
    manifest["generatedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    path = MANIFEST_DIR / f"sitttr-{revision}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"Saved {path} ({len(manifest['documents'])} docs)")


def get_dept_codes(revision: str, doc_type: str) -> list[str]:
    if doc_type == "model-question-paper":
        url = f"{SITTTR_BASE}?r=site%2Fdiploma-modelqp&scheme=REV{revision}"
    else:
        url = f"{SITTTR_BASE}?r=site%2Fdiploma-syllabus&scheme=REV{revision}"
    data = fetch(url, timeout=12)
    if not data:
        return []
    return sorted(set(re.findall(r"prog=([A-Z]{2})", data.decode("utf-8", errors="ignore"))))


def get_known_codes(manifest: dict, doc_type: str) -> set[str]:
    return {"".join(c for c in d["courseCode"] if c.isdigit())
            for d in manifest["documents"] if d.get("documentType") == doc_type and "".join(c for c in d["courseCode"] if c.isdigit())}


def get_known_suffixes(manifest: dict, doc_type: str) -> dict[str, set[str]]:
    """Return {numeric_code: set of full course codes with suffixes like '1002A'}."""
    result: dict[str, set[str]] = {}
    for d in manifest["documents"]:
        if d.get("documentType") == doc_type:
            code = d["courseCode"]
            num = "".join(c for c in code if c.isdigit())
            if num:
                if num not in result:
                    result[num] = set()
                result[num].add(code)
    return result


def probe_code(code_str: str, revision: str, doc_type: str) -> bytes | None:
    if doc_type == "model-question-paper":
        url = f"{SITTTR_BASE}?r=site%2Fdiploma-modelqp-courses-show&course={code_str}"
    else:
        url = f"{SITTTR_BASE}?r=site%2Fdiploma-syllabus-course-contents&course={code_str}"
    data = fetch(url, timeout=12)
    if data and is_pdf(data) and len(data) > 500:
        return data
    return None


def add_entry(manifest: dict, revision: str, doc_type: str, dept_codes: list[str],
              course_code: str, pdf_data: bytes, known_combos: set):
    """Add a manifest entry for every dept that doesn't already have this code."""
    added = 0
    for dc in dept_codes:
        if (dc, course_code) in known_combos:
            continue
        dept_name = DEPT_MAP.get(dc, f"Dept-{dc}")
        dept_folder = dept_name.lower().replace(" & ", "-").replace(" ", "-")
        dest = ROOT / "sitttr" / f"revision-{revision}" / doc_type / dept_folder / "semester-unspecified" / f"{course_code}.pdf"
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            with open(dest, "wb") as f:
                f.write(pdf_data)
        
        source_url = (f"{SITTTR_BASE}?r=site%2Fdiploma-syllabus-course-contents&course={course_code}"
                      if doc_type == "syllabus"
                      else f"{SITTTR_BASE}?r=site%2Fdiploma-modelqp-courses-show&course={course_code}")
        
        manifest["documents"].append({
            "revision": revision,
            "documentType": doc_type,
            "departmentCode": dc,
            "department": dept_name,
            "semester": "semester-unspecified",
            "courseCode": course_code,
            "courseName": f"Course {course_code}",
            "path": str(dest.relative_to(ROOT)),
            "pdfUrl": f"{RAW_BASE}/{dest.relative_to(ROOT)}",
            "sourceUrl": source_url,
            "bytes": len(pdf_data),
            "pages": pdf_page_count(pdf_data),
            "sha256": sha256_hex(pdf_data),
            "status": "published",
        })
        known_combos.add((dc, course_code))
        added += 1
    return added


def main():
    if len(sys.argv) < 5:
        print("Usage: python3 discover_batch.py <revision> <doc_type> <start> <end>")
        print("  e.g.: python3 discover_batch.py 2021 syllabus 1001 1100")
        sys.exit(1)

    revision = sys.argv[1]
    doc_type = sys.argv[2]
    start = int(sys.argv[3])
    end = int(sys.argv[4])

    manifest = load_manifest(revision)
    known = get_known_codes(manifest, doc_type)
    known_suffixes = get_known_suffixes(manifest, doc_type)
    dept_codes = get_dept_codes(revision, doc_type)

    known_combos = {(d.get("departmentCode", ""), d["courseCode"])
                    for d in manifest["documents"] if d.get("documentType") == doc_type}

    print(f"Rev {revision} {doc_type}: probing {start}-{end}")
    print(f"Known numeric codes: {len(known)}, Dept codes: {len(dept_codes)}")

    new_found = 0
    new_entries = 0

    for code_int in range(start, end + 1):
        code_str = str(code_int)
        if code_str in known:
            continue

        time.sleep(0.12)
        pdf_data = probe_code(code_str, revision, doc_type)
        if pdf_data:
            new_found += 1
            added = add_entry(manifest, revision, doc_type, dept_codes, code_str, pdf_data, known_combos)
            new_entries += added
            known.add(code_str)
            print(f"  + {code_str}: {len(pdf_data)} bytes, {added} entries")

    # Also probe suffixed variants (e.g., 1002A) for codes we have
    # Check common suffixes
    for code_int in range(start, end + 1):
        code_str = str(code_int)
        for suffix in ["A", "B"]:
            full_code = code_str + suffix
            if code_str in known_suffixes and full_code in known_suffixes.get(code_str, set()):
                continue
            time.sleep(0.12)
            pdf_data = probe_code(full_code, revision, doc_type)
            if pdf_data:
                new_found += 1
                added = add_entry(manifest, revision, doc_type, dept_codes, full_code, pdf_data, known_combos)
                new_entries += added
                print(f"  + {full_code}: {len(pdf_data)} bytes, {added} entries")

    if new_found:
        save_manifest(manifest, revision)

    print(f"\nBatch complete: {new_found} new codes, {new_entries} new entries")


if __name__ == "__main__":
    main()
