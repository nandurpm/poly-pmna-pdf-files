#!/usr/bin/env python3
"""Scrape SITTTR to find all courses, compare with existing, and download missing PDFs."""
from __future__ import annotations

import json
import hashlib
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

ROOT = Path(__file__).resolve().parent
SITTTR_DIR = ROOT / "sitttr"
MANIFEST_DIR = ROOT / "manifests"
SITTTR_BASE = "https://www.sitttrkerala.ac.in/index.php"


def fetch_page(url: str) -> str | None:
    try:
        req = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urlopen(req, timeout=15) as response:
            return response.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return None


def find_pdf_links(html: str) -> list[str]:
    pdf_pattern = re.compile(r'href=["\']([^"\']*\.pdf)["\']', re.IGNORECASE)
    return pdf_pattern.findall(html)


def download_pdf(url: str, dest_path: Path) -> bool:
    try:
        req = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urlopen(req, timeout=60) as response:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_path, "wb") as f:
                f.write(response.read())
            return True
    except Exception as e:
        print(f"  Error downloading {url}: {e}")
        return False


def calculate_sha256(file_path: Path) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_pdf_pages(file_path: Path) -> int:
    try:
        result = subprocess.run(["pdfinfo", str(file_path)], capture_output=True, text=True, timeout=10)
        for line in result.stdout.split("\n"):
            if line.startswith("Pages:"):
                return int(line.split(":")[1].strip())
    except:
        pass
    return 0


def get_dept_links(revision: str, doc_type: str) -> list[dict]:
    """Get department links from the SITTTR revision page."""
    if doc_type == "model-question-paper":
        url = f"{SITTTR_BASE}?r=site%2Fdiploma-modelqp&scheme=REV{revision}"
    else:
        url = f"{SITTTR_BASE}?r=site%2Fdiploma-syllabus&scheme=REV{revision}"
    
    print(f"Fetching dept list from: {url}")
    html = fetch_page(url)
    if not html:
        return []
    
    depts = []
    # Find links containing prog= parameter
    pattern = r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>\s*([^<]+)\s*</a>'
    for href, name in re.findall(pattern, html):
        if "prog=" in href:
            full_url = href.replace("&amp;", "&")
            if not full_url.startswith("http"):
                full_url = f"https://www.sitttrkerala.ac.in/{full_url.lstrip('/')}"
            depts.append({"name": name.strip(), "url": full_url})
    
    return depts


def get_course_links(dept_url: str) -> list[dict]:
    """Get course links from a department page."""
    html = fetch_page(dept_url)
    if not html:
        return []
    
    courses = []
    pattern = r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>\s*([^<]+)\s*</a>'
    for href, name in re.findall(pattern, html):
        if "course=" in href:
            course_match = re.search(r'course=(\d+[A-Z]*)', href)
            if course_match:
                full_url = href.replace("&amp;", "&")
                if not full_url.startswith("http"):
                    full_url = f"https://www.sitttrkerala.ac.in/{full_url.lstrip('/')}"
                courses.append({
                    "code": course_match.group(1),
                    "name": name.strip(),
                    "url": full_url
                })
    
    return courses


def get_pdf_url(course_url: str) -> str | None:
    html = fetch_page(course_url)
    if not html:
        return None
    
    pdf_links = find_pdf_links(html)
    if pdf_links:
        url = pdf_links[0]
        if not url.startswith("http"):
            url = f"https://www.sitttrkerala.ac.in/{url.lstrip('/')}"
        return url
    
    return None


def main():
    results = {}
    
    for revision in ["2021", "2026"]:
        results[revision] = {"syllabus": [], "model-question-paper": []}
        
        for doc_type in ["syllabus", "model-question-paper"]:
            print(f"\n{'='*60}")
            print(f"Revision {revision} - {doc_type}")
            print(f"{'='*60}")
            
            depts = get_dept_links(revision, doc_type)
            print(f"Found {len(depts)} departments")
            
            for dept in depts:
                print(f"\n  Department: {dept['name']}")
                time.sleep(0.5)  # Be polite to the server
                
                courses = get_course_links(dept["url"])
                print(f"  Found {len(courses)} courses")
                
                for course in courses:
                    results[revision][doc_type].append({
                        "department": dept["name"],
                        "code": course["code"],
                        "name": course["name"],
                        "url": course["url"]
                    })
                
                time.sleep(0.3)
    
    # Save results
    output_file = ROOT / "sitttr_all_courses.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # Summary
    for rev in results:
        for dt in results[rev]:
            count = len(results[rev][dt])
            print(f"\nRevision {rev} {dt}: {count} courses found on SITTTR")
    
    print(f"\nSaved to {output_file}")


if __name__ == "__main__":
    main()
