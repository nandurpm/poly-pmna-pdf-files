#!/usr/bin/env python3
"""Probe a range of course codes. Fast version - no per-dept HTTP requests."""
from __future__ import annotations
import json, hashlib, re, sys, time
from pathlib import Path
from urllib.request import urlopen, Request

ROOT = Path(__file__).resolve().parent
SITTTR_BASE = "https://www.sitttrkerala.ac.in/index.php"
RAW_BASE = "https://raw.githubusercontent.com/nandurpm/poly-pmna-pdf-files/main"
MANIFEST_DIR = ROOT / "manifests"

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

def probe(code: str, revision: str, doc_type: str) -> bytes | None:
    if doc_type == "model-question-paper":
        url = f"{SITTTR_BASE}?r=site%2Fdiploma-modelqp-courses-show&course={code}"
    else:
        url = f"{SITTTR_BASE}?r=site%2Fdiploma-syllabus-course-contents&course={code}"
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=10) as resp:
            data = resp.read()
        if data[:5] == b"%PDF-" and len(data) > 500:
            return data
    except:
        pass
    return None

def main():
    revision = sys.argv[1]
    doc_type = sys.argv[2]
    start = int(sys.argv[3])
    end = int(sys.argv[4])
    
    mf = MANIFEST_DIR / f"sitttr-{revision}.json"
    with open(mf) as f:
        manifest = json.load(f)
    
    known = set()
    known_combos = set()
    for d in manifest["documents"]:
        if d.get("documentType") == doc_type:
            num = "".join(c for c in d["courseCode"] if c.isdigit())
            if num: known.add(num)
            known_combos.add((d.get("departmentCode", ""), d["courseCode"]))
    
    # Get dept codes from listing page
    if doc_type == "model-question-paper":
        list_url = f"{SITTTR_BASE}?r=site%2Fdiploma-modelqp&scheme=REV{revision}"
    else:
        list_url = f"{SITTTR_BASE}?r=site%2Fdiploma-syllabus&scheme=REV{revision}"
    req = Request(list_url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=12) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
    dept_codes = sorted(set(re.findall(r"prog=([A-Z]{2})", html)))
    
    found = 0
    for code_int in range(start, end + 1):
        code = str(code_int)
        if code in known:
            continue
        time.sleep(0.05)
        data = probe(code, revision, doc_type)
        if data:
            found += 1
            known.add(code)
            sha = hashlib.sha256(data).hexdigest()
            m = re.search(rb"/Count\s+(\d+)", data)
            pages = int(m.group(1)) if m else 0
            source_url = (f"{SITTTR_BASE}?r=site%2Fdiploma-syllabus-course-contents&course={code}"
                          if doc_type == "syllabus"
                          else f"{SITTTR_BASE}?r=site%2Fdiploma-modelqp-courses-show&course={code}")
            for dc in dept_codes:
                if (dc, code) in known_combos:
                    continue
                dept_name = DEPT_MAP.get(dc, f"Dept-{dc}")
                dept_folder = dept_name.lower().replace(" & ", "-").replace(" ", "-")
                dest = ROOT / "sitttr" / f"revision-{revision}" / doc_type / dept_folder / "semester-unspecified" / f"{code}.pdf"
                dest.parent.mkdir(parents=True, exist_ok=True)
                if not dest.exists():
                    with open(dest, "wb") as f:
                        f.write(data)
                manifest["documents"].append({
                    "revision": revision, "documentType": doc_type,
                    "departmentCode": dc, "department": dept_name,
                    "semester": "semester-unspecified", "courseCode": code,
                    "courseName": f"Course {code}",
                    "path": str(dest.relative_to(ROOT)),
                    "pdfUrl": f"{RAW_BASE}/{dest.relative_to(ROOT)}",
                    "sourceUrl": source_url, "bytes": len(data),
                    "pages": pages, "sha256": sha, "status": "published",
                })
                known_combos.add((dc, code))
            print(f"+ {code}: {len(data)} bytes")
    
    if found:
        from datetime import datetime, timezone
        manifest["generatedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(mf, "w") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        print(f"Saved ({len(manifest['documents'])} docs)")
    else:
        print(f"No new codes in {start}-{end}")

if __name__ == "__main__":
    main()
