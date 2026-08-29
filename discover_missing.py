#!/usr/bin/env python3

"""
============================================================
FILE: discover_missing.py
PURPOSE: Discovers missing SITTTR PDFs by probing direct document routes across course-code ranges.
============================================================

The department listing pages (diploma-*-courses&prog=XX) return HTTP 500,
so we probe the direct PDF endpoints instead:
- syllabus: diploma-syllabus-course-contents&course=XXXX
- MQP: diploma-modelqp-courses-show&course=XXXX
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
    "CO": "Computer Science & Engineering", "CP": "Commercial Practice",
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


def get_known_numeric_codes(manifest: dict, doc_type: str) -> set[str]:
    """Return set of numeric course code strings we already have."""
    codes = set()
    for doc in manifest["documents"]:
        if doc.get("documentType") == doc_type:
            num = "".join(c for c in doc["courseCode"] if c.isdigit())
            if num:
                codes.add(num)
    return codes


def probe_code(code_str: str, revision: str, doc_type: str) -> bytes | None:
    """Try to fetch a PDF for a course code."""
    if doc_type == "model-question-paper":
        url = f"{SITTTR_BASE}?r=site%2Fdiploma-modelqp-courses-show&course={code_str}"
    else:
        url = f"{SITTTR_BASE}?r=site%2Fdiploma-syllabus-course-contents&course={code_str}"
    data = fetch(url, timeout=12)
    if data and is_pdf(data) and len(data) > 500:
        return data
    return None


def get_dept_codes(revision: str, doc_type: str) -> list[str]:
    """Get department codes from the listing page."""
    if doc_type == "model-question-paper":
        url = f"{SITTTR_BASE}?r=site%2Fdiploma-modelqp&scheme=REV{revision}"
    else:
        url = f"{SITTTR_BASE}?r=site%2Fdiploma-syllabus&scheme=REV{revision}"
    data = fetch(url, timeout=12)
    if not data:
        return []
    return sorted(set(re.findall(r"prog=([A-Z]{2})", data.decode("utf-8", errors="ignore"))))


def get_dept_course_codes(dept_code: str, revision: str, doc_type: str) -> list[str]:
    """Try to get course codes from department page."""
    if doc_type == "model-question-paper":
        url = f"{SITTTR_BASE}?r=site%2Fdiploma-modelqp-courses&prog={dept_code}"
    else:
        url = f"{SITTTR_BASE}?r=site%2Fdiploma-syllabus-courses&prog={dept_code}"
    data = fetch(url, timeout=12)
    if not data or is_pdf(data):
        return []
    html = data.decode("utf-8", errors="ignore")
    if "ERROR" in html:
        return []
    return sorted(set(re.findall(r"course=(\d+[A-Za-z]*)", html)))


def discover_dept_specific(manifest: dict, revision: str, doc_type: str, dept_codes: list[str], known_course_codes: set[str]):
    """For each dept, try course codes we have in other depts but not this one."""
    existing_combos = set()
    for doc in manifest["documents"]:
        if doc.get("documentType") == doc_type:
            existing_combos.add((doc.get("departmentCode", ""), doc["courseCode"]))

    # Get unique course codes (with suffix) per dept
    dept_code_map: dict[str, set[str]] = {}
    for doc in manifest["documents"]:
        if doc.get("documentType") == doc_type:
            dc = doc.get("departmentCode", "")
            cc = doc["courseCode"]
            if dc not in dept_code_map:
                dept_code_map[dc] = set()
            dept_code_map[dc].add(cc)

    new_count = 0
    for dept_code in dept_codes:
        dept_name = DEPT_MAP.get(dept_code, f"Dept-{dept_code}")
        dept_folder = dept_name.lower().replace(" & ", "-").replace(" ", "-")
        my_codes = dept_code_map.get(dept_code, set())
        
        # Find codes that other departments have but this one doesn't
        all_codes = set()
        for codes in dept_code_map.values():
            all_codes |= codes
        
        missing_codes = all_codes - my_codes
        
        for code in sorted(missing_codes):
            if (dept_code, code) in existing_combos:
                continue
            time.sleep(0.15)
            pdf_data = probe_code(code, revision, doc_type)
            if pdf_data:
                new_count += 1
                dest = ROOT / "sitttr" / f"revision-{revision}" / doc_type / dept_folder / "semester-unspecified" / f"{code}.pdf"
                dest.parent.mkdir(parents=True, exist_ok=True)
                with open(dest, "wb") as f:
                    f.write(pdf_data)
                
                source_url = (f"{SITTTR_BASE}?r=site%2Fdiploma-syllabus-course-contents&course={code}"
                              if doc_type == "syllabus"
                              else f"{SITTTR_BASE}?r=site%2Fdiploma-modelqp-courses-show&course={code}")
                
                new_doc = {
                    "revision": revision,
                    "documentType": doc_type,
                    "departmentCode": dept_code,
                    "department": dept_name,
                    "semester": "semester-unspecified",
                    "courseCode": code,
                    "courseName": f"Course {code}",
                    "path": str(dest.relative_to(ROOT)),
                    "pdfUrl": f"{RAW_BASE}/{dest.relative_to(ROOT)}",
                    "sourceUrl": source_url,
                    "bytes": len(pdf_data),
                    "pages": pdf_page_count(pdf_data),
                    "sha256": sha256_hex(pdf_data),
                    "status": "published",
                }
                manifest["documents"].append(new_doc)
                existing_combos.add((dept_code, code))
                print(f"  + {dept_code}/{code}: {len(pdf_data)} bytes")
    
    return new_count


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 discover_missing.py <revision>")
        sys.exit(1)
    revision = sys.argv[1]
    
    manifest = load_manifest(revision)
    total_new = 0
    
    for doc_type in ["syllabus", "model-question-paper"]:
        print(f"\n{'='*60}")
        print(f"Revision {revision} — {doc_type}")
        print(f"{'='*60}")
        
        known = get_known_numeric_codes(manifest, doc_type)
        print(f"Known numeric codes: {len(known)}")
        
        dept_codes = get_dept_codes(revision, doc_type)
        print(f"Department codes: {len(dept_codes)}")
        
        # Phase 1: Try department pages to get new course codes
        new_codes_from_dept = []
        dept_pages_ok = False
        for dc in dept_codes:
            time.sleep(0.3)
            codes = get_dept_course_codes(dc, revision, doc_type)
            if codes:
                dept_pages_ok = True
                for c in codes:
                    num = "".join(ch for ch in c if ch.isdigit())
                    if num and num not in known:
                        new_codes_from_dept.append(c)
                        known.add(num)
        
        if dept_pages_ok:
            print(f"New course codes from dept pages: {len(new_codes_from_dept)}")
        else:
            print("Department pages unavailable (500). Using range probe...")
            
            # Phase 2: Probe common code ranges
            # Get min/max from existing codes to narrow the range
            existing_ints = [int(c) for c in known]
            if existing_ints:
                min_code = min(existing_ints)
                max_code = max(existing_ints)
            else:
                min_code, max_code = 1001, 7000
            
            # Probe ranges around known gaps
            probe_ranges = []
            # Foundation/common: 1001-1500
            probe_ranges.append((1001, 1500))
            # Department-specific: extend beyond max
            probe_ranges.append((max_code + 1, max_code + 200))
            # Gaps within known range
            sorted_ints = sorted(existing_ints)
            for i in range(1, len(sorted_ints)):
                gap_start = sorted_ints[i-1] + 1
                gap_end = sorted_ints[i] - 1
                if gap_end - gap_start >= 3:  # Only probe significant gaps
                    probe_ranges.append((gap_start, gap_end))
            
            print(f"Probing {len(probe_ranges)} ranges...")
            for lo, hi in probe_ranges:
                found_in_range = 0
                for code_int in range(lo, hi + 1):
                    code_str = str(code_int)
                    if code_str in known:
                        continue
                    time.sleep(0.15)
                    pdf_data = probe_code(code_str, revision, doc_type)
                    if pdf_data:
                        known.add(code_str)
                        new_codes_from_dept.append(code_str)
                        found_in_range += 1
                        print(f"  Found: {code_str} ({len(pdf_data)} bytes)")
                if found_in_range:
                    print(f"  Range {lo}-{hi}: {found_in_range} new codes")
        
        # Phase 3: For new codes found, create entries for all departments
        for code in new_codes_from_dept:
            for dc in dept_codes:
                dept_name = DEPT_MAP.get(dc, f"Dept-{dc}")
                dept_folder = dept_name.lower().replace(" & ", "-").replace(" ", "-")
                
                time.sleep(0.15)
                pdf_data = probe_code(code, revision, doc_type)
                if pdf_data:
                    total_new += 1
                    dest = ROOT / "sitttr" / f"revision-{revision}" / doc_type / dept_folder / "semester-unspecified" / f"{code}.pdf"
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with open(dest, "wb") as f:
                        f.write(pdf_data)
                    
                    source_url = (f"{SITTTR_BASE}?r=site%2Fdiploma-syllabus-course-contents&course={code}"
                                  if doc_type == "syllabus"
                                  else f"{SITTTR_BASE}?r=site%2Fdiploma-modelqp-courses-show&course={code}")
                    
                    new_doc = {
                        "revision": revision,
                        "documentType": doc_type,
                        "departmentCode": dc,
                        "department": dept_name,
                        "semester": "semester-unspecified",
                        "courseCode": code,
                        "courseName": f"Course {code}",
                        "path": str(dest.relative_to(ROOT)),
                        "pdfUrl": f"{RAW_BASE}/{dest.relative_to(ROOT)}",
                        "sourceUrl": source_url,
                        "bytes": len(pdf_data),
                        "pages": pdf_page_count(pdf_data),
                        "sha256": sha256_hex(pdf_data),
                        "status": "published",
                    }
                    manifest["documents"].append(new_doc)
                    print(f"  + {dc}/{code}: {len(pdf_data)} bytes")
        
        # Phase 4: Check for missing dept-specific copies of known codes
        print(f"\nChecking missing dept+code combos for known codes...")
        dept_new = discover_dept_specific(manifest, revision, doc_type, dept_codes, known)
        total_new += dept_new
        
        # Save
        if total_new > 0:
            from datetime import datetime, timezone
            manifest["generatedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            path = MANIFEST_DIR / f"sitttr-{revision}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)
            print(f"Updated {path}")
    
    print(f"\n{'='*60}")
    print(f"Total new documents added: {total_new}")
    print(f"Total in manifest: {len(manifest['documents'])}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
