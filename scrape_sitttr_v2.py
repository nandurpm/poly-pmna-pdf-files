#!/usr/bin/env python3

"""
============================================================
FILE: scrape_sitttr_v2.py
PURPOSE: Implements the revised SITTTR scraper and manifest update workflow.
============================================================
"""
from __future__ import annotations

import json
import hashlib
import re
import subprocess
import sys
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

ROOT = Path(__file__).resolve().parent
MANIFEST_DIR = ROOT / "manifests"
SITTTR_DIR = ROOT / "sitttr"
INDEX_FILE = MANIFEST_DIR / "sitttr-index.json"
SITTTR_BASE = "https://www.sitttrkerala.ac.in/index.php"


def fetch_page(url: str) -> str | None:
    """Fetch a webpage and return its content."""
    try:
        req = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urlopen(req, timeout=15) as response:
            return response.read().decode("utf-8", errors="ignore")
    except (URLError, HTTPError, Exception) as e:
        print(f"  Error fetching {url}: {e}")
        return None


def find_pdf_links(html: str) -> list[str]:
    """Find all PDF links in HTML content."""
    pdf_pattern = re.compile(r'href=["\']([^"\']*\.pdf)["\']', re.IGNORECASE)
    return pdf_pattern.findall(html)


def download_pdf(url: str, dest_path: Path) -> bool:
    """Download a PDF file."""
    try:
        req = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urlopen(req, timeout=60) as response:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_path, "wb") as f:
                f.write(response.read())
            return True
    except (URLError, HTTPError, Exception) as e:
        print(f"  Error downloading {url}: {e}")
        return False


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_pdf_pages(file_path: Path) -> int:
    """Get page count of PDF using pdfinfo."""
    try:
        result = subprocess.run(
            ["pdfinfo", str(file_path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        for line in result.stdout.split("\n"):
            if line.startswith("Pages:"):
                return int(line.split(":")[1].strip())
    except Exception:
        pass
    return 0


def get_departments(revision: str, doc_type: str) -> list[dict]:
    """Get list of departments for a revision and document type."""
    if doc_type == "model-question-paper":
        url = f"{SITTTR_BASE}?r=site%2Fdiploma-modelqp&scheme=REV{revision}"
    else:
        url = f"{SITTTR_BASE}?r=site%2Fdiploma-syllabus&scheme=REV{revision}"
    
    print(f"Fetching departments from: {url}")
    html = fetch_page(url)
    
    if not html:
        return []
    
    # Find department links
    departments = []
    pattern = r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>\s*([^<]+)\s*</a>'
    matches = re.findall(pattern, html)
    
    for href, name in matches:
        # Check if it's a department link (contains prog= parameter)
        if "prog=" in href:
            # Extract department code
            prog_match = re.search(r'prog=([A-Z]+)', href)
            if prog_match:
                dept_code = prog_match.group(1)
                dept_name = name.strip()
                
                # Build full URL
                full_url = href.replace("&amp;", "&")
                if not full_url.startswith("http"):
                    full_url = f"{SITTTR_BASE}/{full_url.lstrip('/')}"
                
                departments.append({
                    "code": dept_code,
                    "name": dept_name,
                    "url": full_url
                })
    
    return departments


def get_courses(dept_url: str) -> list[dict]:
    """Get list of courses for a department."""
    print(f"  Fetching courses from: {dept_url}")
    html = fetch_page(dept_url)
    
    if not html:
        return []
    
    # Find course links
    courses = []
    pattern = r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>\s*([^<]+)\s*</a>'
    matches = re.findall(pattern, html)
    
    for href, name in matches:
        # Check if it's a course link (contains course= parameter)
        if "course=" in href:
            # Extract course code
            course_match = re.search(r'course=(\d+[A-Z]*)', href)
            if course_match:
                course_code = course_match.group(1)
                course_name = name.strip()
                
                # Build full URL
                full_url = href.replace("&amp;", "&")
                if not full_url.startswith("http"):
                    full_url = f"{SITTTR_BASE}/{full_url.lstrip('/')}"
                
                courses.append({
                    "code": course_code,
                    "name": course_name,
                    "url": full_url
                })
    
    return courses


def get_pdf_url(course_url: str) -> str | None:
    """Get PDF URL from a course page."""
    html = fetch_page(course_url)
    
    if not html:
        return None
    
    # Find PDF links
    pdf_links = find_pdf_links(html)
    
    if pdf_links:
        # Return the first PDF link
        url = pdf_links[0]
        if not url.startswith("http"):
            url = f"https://www.sitttrkerala.ac.in/{url.lstrip('/')}"
        return url
    
    return None


def main():
    print("=== SITTTR Website Scraper v2 ===\n")
    
    # Load existing index
    existing_docs = {}
    if INDEX_FILE.exists():
        with open(INDEX_FILE, encoding="utf-8") as f:
            index = json.load(f)
        for doc in index["documents"]:
            key = (doc["revision"], doc["documentType"], doc["courseCode"])
            existing_docs[key] = doc
        print(f"Loaded {len(existing_docs)} existing documents from index")
    else:
        index = {
            "schemaVersion": 1,
            "generatedAt": "",
            "source": "https://www.sitttrkerala.ac.in",
            "sourcePolicy": "Official SITTTR pages; only endpoints returning readable PDFs are included.",
            "rawBaseUrl": "https://raw.githubusercontent.com/nandurpm/poly-pmna-pdf-files/main",
            "availability": [],
            "documents": []
        }
    
    print("\nScraping SITTTR website...\n")
    
    new_downloaded = 0
    already_exists = 0
    no_pdf = 0
    
    # Check each revision and document type
    for revision in ["2015", "2021", "2026"]:
        for doc_type in ["model-question-paper", "syllabus"]:
            print(f"\n{'='*60}")
            print(f"Revision {revision} - {doc_type}")
            print(f"{'='*60}")
            
            # Get departments
            departments = get_departments(revision, doc_type)
            print(f"Found {len(departments)} departments")
            
            # For each department, get courses
            for dept in departments:
                print(f"\n  Department: {dept['name']} ({dept['code']})")
                
                courses = get_courses(dept["url"])
                print(f"  Found {len(courses)} courses")
                
                # For each course, check if we have the PDF
                for course in courses:
                    key = (revision, doc_type, course["code"])
                    
                    if key in existing_docs:
                        already_exists += 1
                        continue
                    
                    # Try to find PDF link on course page
                    print(f"    Checking course {course['code']}...")
                    pdf_url = get_pdf_url(course["url"])
                    
                    if pdf_url:
                        print(f"      Found PDF: {pdf_url}")
                        
                        # Create filename
                        filename = f"{course['code']}.pdf"
                        dept_folder = dept["name"].lower().replace(" & ", "-").replace(" ", "-")
                        dest_path = SITTTR_DIR / f"revision-{revision}" / doc_type / dept_folder / "semester-unspecified" / filename
                        
                        if download_pdf(pdf_url, dest_path):
                            print(f"      Downloaded: {dest_path}")
                            new_downloaded += 1
                            
                            # Calculate hash and page count
                            sha256 = calculate_sha256(dest_path)
                            pages = get_pdf_pages(dest_path)
                            size = dest_path.stat().st_size
                            
                            # Add to index
                            new_doc = {
                                "revision": revision,
                                "documentType": doc_type,
                                "departmentCode": dept["code"],
                                "department": dept["name"],
                                "semester": "semester-unspecified",
                                "courseCode": course["code"],
                                "courseName": course["name"],
                                "path": str(dest_path.relative_to(ROOT)),
                                "pdfUrl": f"https://raw.githubusercontent.com/nandurpm/poly-pmna-pdf-files/main/{dest_path.relative_to(ROOT)}",
                                "sourceUrl": pdf_url,
                                "bytes": size,
                                "pages": pages,
                                "sha256": sha256,
                                "status": "published"
                            }
                            index["documents"].append(new_doc)
                            existing_docs[key] = new_doc
                        else:
                            print(f"      Failed to download")
                    else:
                        no_pdf += 1
                        print(f"      No PDF found")
    
    print(f"\n{'='*60}")
    print(f"Summary")
    print(f"{'='*60}")
    print(f"Already in index: {already_exists}")
    print(f"Newly downloaded: {new_downloaded}")
    print(f"No PDF found: {no_pdf}")
    
    # Save updated index
    if new_downloaded > 0:
        from datetime import datetime
        index["generatedAt"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
        print(f"\nUpdated {INDEX_FILE}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
