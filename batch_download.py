#!/usr/bin/env python3

"""
============================================================
FILE: batch_download.py
PURPOSE: Downloads a requested batch of missing SITTTR PDFs, validates them, and updates the canonical index.
============================================================
"""
from __future__ import annotations

import json
import hashlib
import subprocess
import sys
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

ROOT = Path(__file__).resolve().parent
SITTTR_DIR = ROOT / "sitttr"
INDEX_FILE = ROOT / "manifests" / "sitttr-index.json"
SITTTR_URL = "https://www.sitttrkerala.ac.in/index.php?r=site%2Fdiploma-modelqp-courses-show&course={code}"
SITTTR_URL_SYLL = "https://www.sitttrkerala.ac.in/index.php?r=site%2Fdiploma-syllabus-courses-show&course={code}"

DEPT_NAMES = {
    "AR": "Architecture", "AU": "Automobile Engineering", "BM": "Biomedical Engineering",
    "CB": "Computer Application & Business Management", "CE": "Civil Engineering",
    "CH": "Chemical Engineering", "CM": "Computer Hardware Engineering",
    "CP": "Commercial Practice", "CS": "Computer Science Engineering",
    "CT": "Computer Engineering", "CV": "Civil Engineering",
    "EC": "Electronics Engineering", "EE": "Electrical & Electronics Engineering",
    "EW": "Electronics and Communication", "IT": "Information Technology",
    "IE": "Instrumentation Engineering", "ME": "Mechanical Engineering",
    "MF": "Manufacturing Technology", "PT": "Polymer Technology",
    "TT": "Textile Technology", "TD": "Tool & Die Engineering",
    "WP": "Wood and Paper Technology", "PR": "Printing Technology",
    "AI": "Artificial Intelligence", "AM": "Automation and Robotics",
    "CA": "Computer Application", "CC": "Computer Engineering",
    "CF": "Computer Hardware", "CL": "Chemical Engineering",
    "CN": "Computer Networks", "CR": "Computer Science",
    "CW": "Computer Hardware Engineering",
}


def load_index() -> dict:
    with open(INDEX_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_index(index: dict):
    from datetime import datetime
    index["generatedAt"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def get_existing_keys(index: dict) -> set:
    keys = set()
    for doc in index["documents"]:
        keys.add((doc["revision"], doc["documentType"], doc["courseCode"]))
    return keys


def try_download(code: str, revision: str, doc_type: str) -> bytes | None:
    if doc_type == "model-question-paper":
        url = SITTTR_URL.format(code=code)
    else:
        url = SITTTR_URL_SYLL.format(code=code)
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=5) as resp:
            data = resp.read(5000000)  # max 5MB
            if data[:5] == b"%PDF-":
                return data
    except Exception:
        pass
    return None


def get_dept(code: str) -> tuple[str, str]:
    prefix = code.rstrip("0123456789ABCDEFabcdef").rstrip("-")
    if len(prefix) >= 2:
        dc = prefix[:2].upper()
        name = DEPT_NAMES.get(dc, f"Department-{dc}")
        return dc, name
    return "XX", "Unknown"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pdf_pages(data: bytes) -> int:
    """Count pages from PDF stream count."""
    import re
    m = re.search(rb"/Count\s+(\d+)", data)
    return int(m.group(1)) if m else 0


def main():
    if len(sys.argv) < 5:
        print("Usage: python3 batch_download.py <revision> <doc_type> <start> <end>")
        print("  revision: 2021 or 2026")
        print("  doc_type: model-question-paper or syllabus")
        print("  start: starting course code number (e.g. 1000)")
        print("  end: ending course code number (e.g. 1999)")
        sys.exit(1)

    revision = sys.argv[1]
    doc_type = sys.argv[2]
    start = int(sys.argv[3])
    end = int(sys.argv[4])

    index = load_index()
    existing = get_existing_keys(index)

    print(f"Checking {revision} {doc_type} codes {start}-{end}")
    print(f"Already in index: {len([k for k in existing if k[0]==revision and k[1]==doc_type])}")

    downloaded = 0
    checked = 0

    for code_num in range(start, end + 1):
        code = str(code_num)
        key = (revision, doc_type, code)
        if key in existing:
            continue

        checked += 1
        data = try_download(code, revision, doc_type)
        if data is None:
            continue

        dc, dept_name = get_dept(code)
        filename = f"{code}.pdf"
        dept_folder = dept_name.lower().replace(" & ", "-").replace(" ", "-")
        dest = SITTTR_DIR / f"revision-{revision}" / doc_type / dept_folder / "semester-unspecified" / filename
        dest.parent.mkdir(parents=True, exist_ok=True)

        with open(dest, "wb") as f:
            f.write(data)

        pages = pdf_pages(data)
        new_doc = {
            "revision": revision,
            "documentType": doc_type,
            "departmentCode": dc,
            "department": dept_name,
            "semester": "semester-unspecified",
            "courseCode": code,
            "courseName": f"Course {code}",
            "path": str(dest.relative_to(ROOT)),
            "pdfUrl": f"https://raw.githubusercontent.com/nandurpm/poly-pmna-pdf-files/main/{dest.relative_to(ROOT)}",
            "sourceUrl": f"https://www.sitttrkerala.ac.in",
            "bytes": len(data),
            "pages": pages,
            "sha256": sha256(data),
            "status": "published",
        }
        index["documents"].append(new_doc)
        existing.add(key)
        downloaded += 1
        print(f"  + {code} ({dept_name}) {len(data)} bytes, {pages} pages")

    if downloaded > 0:
        save_index(index)
        print(f"\nSaved {downloaded} new PDFs to index")
    else:
        print(f"\nNo new PDFs found (checked {checked} codes)")

    print(f"Checked: {checked}, Downloaded: {downloaded}")


if __name__ == "__main__":
    main()
