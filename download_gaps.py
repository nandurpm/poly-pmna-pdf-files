#!/usr/bin/env python3

"""
============================================================
FILE: download_gaps.py
PURPOSE: Downloads and indexes valid SITTTR PDFs found in gaps between known course codes.
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

ROOT = Path(__file__).resolve().parent
SITTTR_DIR = ROOT / "sitttr"
INDEX_FILE = ROOT / "manifests" / "sitttr-index.json"
SITTTR_BASE = "https://www.sitttrkerala.ac.in/index.php"

DEPT_NAMES = {
    "10": "Common", "11": "Common", "12": "Common", "14": "Common",
    "20": "Architecture", "21": "Architecture", "22": "Civil",
    "23": "Civil", "24": "Civil", "27": "Civil",
    "30": "Civil", "31": "Civil", "32": "Civil", "33": "Civil", "34": "Civil", "35": "Civil",
    "40": "Computer Engineering", "41": "Computer Engineering", "42": "Computer Engineering",
    "43": "Computer Engineering", "44": "Computer Engineering", "45": "Computer Engineering",
    "47": "Computer Engineering",
    "50": "Electronics", "51": "Electronics", "52": "Electronics", "53": "Electronics",
    "54": "Electronics", "55": "Electronics", "57": "Electronics",
    "60": "Mechanical", "61": "Mechanical", "62": "Mechanical", "63": "Mechanical",
    "64": "Mechanical", "65": "Mechanical", "67": "Mechanical",
}


def load_index() -> dict:
    with open(INDEX_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_index(index: dict):
    from datetime import datetime
    index["generatedAt"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pdf_pages(data: bytes) -> int:
    m = re.search(rb"/Count\s+(\d+)", data)
    return int(m.group(1)) if m else 0


def try_download(code: str, revision: str, doc_type: str) -> bytes | None:
    if doc_type == "model-question-paper":
        url = f"{SITTTR_BASE}?r=site%2Fdiploma-modelqp-courses-show&course={code}"
    else:
        url = f"{SITTTR_BASE}?r=site%2Fdiploma-syllabus-courses-show&course={code}"
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=5) as resp:
            data = resp.read(5000000)
            if data[:5] == b"%PDF-":
                return data
    except Exception:
        pass
    return None


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 download_gaps.py <revision> <doc_type>")
        sys.exit(1)

    revision = sys.argv[1]
    doc_type = sys.argv[2]

    index = load_index()
    existing = {(d["revision"], d["documentType"], d["courseCode"]) for d in index["documents"]}

    # Get existing codes for this revision/type, sorted numerically
    existing_codes = sorted(
        [d["courseCode"] for d in index["documents"]
         if d["revision"] == revision and d["documentType"] == doc_type],
        key=lambda c: int(re.sub(r"[^0-9]", "", c) or "0")
    )

    print(f"Revision {revision} {doc_type}")
    print(f"Existing codes: {len(existing_codes)}")

    # Find gaps in the code sequences
    # Group by prefix (first 2 digits)
    prefix_groups = {}
    for code in existing_codes:
        digits = "".join(c for c in code if c.isdigit())
        if len(digits) >= 2:
            prefix = digits[:2]
            if prefix not in prefix_groups:
                prefix_groups[prefix] = []
            prefix_groups[prefix].append(code)

    print(f"Code prefixes: {sorted(prefix_groups.keys())}")

    # For each prefix, find gaps
    candidate_codes = []
    for prefix, codes in sorted(prefix_groups.items()):
        nums = sorted(set(int(re.sub(r"[^0-9]", "", c) or "0") for c in codes))
        if not nums:
            continue

        min_num = min(nums)
        max_num = max(nums)

        # Check numbers in range that aren't in the existing set
        existing_nums = set(nums)
        for n in range(min_num, max_num + 1):
            if n not in existing_nums:
                candidate_codes.append(str(n))

    print(f"Gap codes to check: {len(candidate_codes)}")
    print(f"First 20: {candidate_codes[:20]}")

    # Download new PDFs
    downloaded = 0
    checked = 0
    batch_size = 50

    for i in range(0, len(candidate_codes), batch_size):
        batch = candidate_codes[i:i + batch_size]
        print(f"\nBatch {i // batch_size + 1}: checking {batch[0]}-{batch[-1]}")

        for code in batch:
            key = (revision, doc_type, code)
            if key in existing:
                continue

            checked += 1
            data = try_download(code, revision, doc_type)
            if data is None:
                continue

            # Get department
            digits = "".join(c for c in code if c.isdigit())
            prefix = digits[:2] if len(digits) >= 2 else "XX"
            dept_name = DEPT_NAMES.get(prefix, f"Dept-{prefix}")

            filename = f"{code}.pdf"
            dept_folder = dept_name.lower().replace(" & ", "-").replace(" ", "-")
            dest = SITTTR_DIR / f"revision-{revision}" / doc_type / dept_folder / "semester-unspecified" / filename
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, "wb") as f:
                f.write(data)

            new_doc = {
                "revision": revision,
                "documentType": doc_type,
                "departmentCode": prefix,
                "department": dept_name,
                "semester": "semester-unspecified",
                "courseCode": code,
                "courseName": f"Course {code}",
                "path": str(dest.relative_to(ROOT)),
                "pdfUrl": f"https://raw.githubusercontent.com/nandurpm/poly-pmna-pdf-files/main/{dest.relative_to(ROOT)}",
                "sourceUrl": f"https://www.sitttrkerala.ac.in",
                "bytes": len(data),
                "pages": pdf_pages(data),
                "sha256": sha256(data),
                "status": "published",
            }
            index["documents"].append(new_doc)
            existing.add(key)
            downloaded += 1
            print(f"  + {code}: {len(data)} bytes")

            time.sleep(0.3)

        # Save after each batch
        if downloaded > 0:
            save_index(index)

    print(f"\n=== Summary ===")
    print(f"Checked: {checked}")
    print(f"Downloaded: {downloaded}")


if __name__ == "__main__":
    main()
