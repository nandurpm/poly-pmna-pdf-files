#!/usr/bin/env python3

"""
============================================================
FILE: scrape_and_download.py
PURPOSE: Scrapes department pages for course codes and downloads newly discovered SITTTR PDFs.
============================================================
"""
from __future__ import annotations

import json
import hashlib
import re
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

ROOT = Path(__file__).resolve().parent
SITTTR_DIR = ROOT / "sitttr"
INDEX_FILE = ROOT / "manifests" / "sitttr-index.json"
SITTTR_BASE = "https://www.sitttrkerala.ac.in/index.php"

DEPT_NAMES = {
    "AI": "Artificial Intelligence", "AM": "Automation and Robotics",
    "AR": "Architecture", "AU": "Automobile Engineering",
    "BM": "Biomedical Engineering", "CA": "Computer Application",
    "CB": "Computer Application & Business Management", "CC": "Computer Engineering",
    "CE": "Civil Engineering", "CF": "Computer Hardware",
    "CH": "Chemical Engineering", "CL": "Chemical Engineering",
    "CM": "Computer Hardware Engineering", "CN": "Computer Networks",
    "CP": "Commercial Practice", "CR": "Computer Science",
    "CS": "Computer Science Engineering", "CT": "Computer Engineering",
    "CW": "Computer Hardware Engineering", "CV": "Civil Engineering",
    "EC": "Electronics Engineering", "EE": "Electrical & Electronics Engineering",
    "EW": "Electronics and Communication", "IT": "Information Technology",
    "IE": "Instrumentation Engineering", "ME": "Mechanical Engineering",
    "MF": "Manufacturing Technology", "PT": "Polymer Technology",
    "TT": "Textile Technology", "TD": "Tool & Die Engineering",
    "WP": "Wood and Paper Technology", "PR": "Printing Technology",
    "EV": "Electronics and Communication", "IC": "Instrumentation Engineering",
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
    return {(d["revision"], d["documentType"], d["courseCode"]) for d in index["documents"]}


def fetch(url: str) -> str | None:
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=8) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return None


def fetch_binary(url: str) -> bytes | None:
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=8) as resp:
            data = resp.read(5000000)
            if data[:5] == b"%PDF-":
                return data
    except Exception:
        pass
    return None


def get_dept_codes(revision: str, doc_type: str) -> list[str]:
    """Get department codes from the main listing page."""
    if doc_type == "model-question-paper":
        url = f"{SITTTR_BASE}?r=site%2Fdiploma-modelqp&scheme=REV{revision}"
    else:
        url = f"{SITTTR_BASE}?r=site%2Fdiploma-syllabus&scheme=REV{revision}"

    html = fetch(url)
    if not html:
        return []

    return list(set(re.findall(r"prog=([A-Z]{2})", html)))


def get_course_codes(dept_code: str, revision: str, doc_type: str) -> list[str]:
    """Get course codes from a department page."""
    if doc_type == "model-question-paper":
        url = f"{SITTTR_BASE}?r=site%2Fdiploma-modelqp-courses&prog={dept_code}"
    else:
        url = f"{SITTTR_BASE}?r=site%2Fdiploma-syllabus-courses&prog={dept_code}"

    html = fetch(url)
    if not html:
        return []

    # Check if it's a PDF directly
    if html[:5] == "%PDF-":
        return []

    # Find course codes
    return list(set(re.findall(r"course=(\d+[A-Za-z]*)", html)))


def get_pdf_url(course_code: str, revision: str, doc_type: str) -> str | None:
    """Try to get PDF directly from course URL."""
    if doc_type == "model-question-paper":
        url = f"{SITTTR_BASE}?r=site%2Fdiploma-modelqp-courses-show&course={course_code}"
    else:
        url = f"{SITTTR_BASE}?r=site%2Fdiploma-syllabus-courses-show&course={course_code}"

    data = fetch_binary(url)
    if data:
        return url
    return None


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pdf_pages(data: bytes) -> int:
    m = re.search(rb"/Count\s+(\d+)", data)
    return int(m.group(1)) if m else 0


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 scrape_and_download.py <revision> <doc_type>")
        print("  revision: 2021 or 2026")
        print("  doc_type: model-question-paper or syllabus")
        sys.exit(1)

    revision = sys.argv[1]
    doc_type = sys.argv[2]

    index = load_index()
    existing = get_existing_keys(index)

    print(f"=== Scraping {revision} {doc_type} ===\n")

    # Step 1: Get department codes
    dept_codes = get_dept_codes(revision, doc_type)
    print(f"Found {len(dept_codes)} departments: {dept_codes}\n")

    downloaded = 0
    no_pdf = 0

    for dept_code in dept_codes:
        dept_name = DEPT_NAMES.get(dept_code, f"Dept-{dept_code}")
        print(f"Department: {dept_name} ({dept_code})")

        # Step 2: Get course codes for this department
        time.sleep(0.3)  # Be polite
        course_codes = get_course_codes(dept_code, revision, doc_type)
        print(f"  Found {len(course_codes)} courses: {course_codes[:10]}{'...' if len(course_codes) > 10 else ''}")

        for code in course_codes:
            key = (revision, doc_type, code)
            if key in existing:
                continue

            # Step 3: Try to download PDF
            time.sleep(0.3)
            pdf_url = get_pdf_url(code, revision, doc_type)
            if not pdf_url:
                no_pdf += 1
                continue

            # Download full PDF
            data = fetch_binary(pdf_url)
            if not data:
                continue

            # Save
            filename = f"{code}.pdf"
            dept_folder = dept_name.lower().replace(" & ", "-").replace(" ", "-")
            dest = SITTTR_DIR / f"revision-{revision}" / doc_type / dept_folder / "semester-unspecified" / filename
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, "wb") as f:
                f.write(data)

            new_doc = {
                "revision": revision,
                "documentType": doc_type,
                "departmentCode": dept_code,
                "department": dept_name,
                "semester": "semester-unspecified",
                "courseCode": code,
                "courseName": f"Course {code}",
                "path": str(dest.relative_to(ROOT)),
                "pdfUrl": f"https://raw.githubusercontent.com/nandurpm/poly-pmna-pdf-files/main/{dest.relative_to(ROOT)}",
                "sourceUrl": pdf_url,
                "bytes": len(data),
                "pages": pdf_pages(data),
                "sha256": sha256(data),
                "status": "published",
            }
            index["documents"].append(new_doc)
            existing.add(key)
            downloaded += 1
            print(f"    + {code}: {len(data)} bytes, {pdf_pages(data)} pages")

    if downloaded > 0:
        save_index(index)

    print(f"\n=== Summary ===")
    print(f"Downloaded: {downloaded}")
    print(f"No PDF found: {no_pdf}")


if __name__ == "__main__":
    main()
