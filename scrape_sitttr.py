#!/usr/bin/env python3
"""Scrape SITTTR website to find all available PDF documents."""
from __future__ import annotations

import json
import hashlib
import re
import subprocess
import sys
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parent
MANIFEST_DIR = ROOT / "manifests"
SITTTR_DIR = ROOT / "sitttr"
INDEX_FILE = MANIFEST_DIR / "sitttr-index.json"

# SITTTR URLs
SITTTR_BASE = "https://www.sitttrkerala.ac.in/index.php"

# Department codes to check
DEPARTMENTS = {
    "AR": "Architecture",
    "AE": "Automobile Engineering",
    "BE": "Biomedical Engineering",
    "CE": "Chemical Engineering",
    "CV": "Civil Engineering",
    "CP": "Commercial Practice",
    "CB": "Computer Application & Business Management",
    "CS": "Computer Engineering",
    "CH": "Computer Hardware Engineering",
    "EE": "Electrical & Electronics Engineering",
    "EC": "Electronics Engineering",
    "EW": "Electronics and Communication",
    "IT": "Information Technology",
    "IE": "Instrumentation Engineering",
    "MT": "Manufacturing Technology",
    "ME": "Mechanical Engineering",
    "PT": "Polymer Technology",
    "PT": "Printing Technology",
    "TT": "Textile Technology",
    "TD": "Tool & Die Engineering",
    "WP": "Wood and Paper Technology",
}


class SITTTRParser(HTMLParser):
    """Parse SITTTR HTML pages to find course links."""
    
    def __init__(self):
        super().__init__()
        self.courses = []
        self.current_tag = None
        self.current_attrs = {}
    
    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        self.current_attrs = dict(attrs)
        
        # Look for links to course pages
        if tag == "a":
            href = self.current_attrs.get("href", "")
            if "courses-show" in href or "course=" in href:
                # Extract course code from URL
                match = re.search(r'course=(\d+)', href)
                if match:
                    course_code = match.group(1)
                    self.courses.append({
                        "code": course_code,
                        "url": href if href.startswith("http") else f"{SITTTR_BASE}/{href.lstrip('/')}"
                    })


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


def scrape_revision_page(revision: str, doc_type: str) -> list[dict]:
    """Scrape SITTTR page for a specific revision and document type."""
    if doc_type == "model-question-paper":
        url = f"{SITTTR_BASE}?r=site%2Fdiploma-modelqp&scheme=REV{revision}"
    else:
        url = f"{SITTTR_BASE}?r=site%2Fdiploma-syllabus&scheme=REV{revision}"
    
    print(f"Scraping: {url}")
    html = fetch_page(url)
    
    if not html:
        return []
    
    # Parse HTML to find course links
    parser = SITTTRParser()
    parser.feed(html)
    
    courses = []
    for course in parser.courses:
        courses.append({
            "code": course["code"],
            "url": course["url"],
            "revision": revision,
            "documentType": doc_type
        })
    
    return courses


def main():
    print("=== SITTTR Website Scraper ===\n")
    
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
    
    # Check each revision and document type
    for revision in ["2015", "2021", "2026"]:
        for doc_type in ["model-question-paper", "syllabus"]:
            print(f"\n=== Revision {revision} - {doc_type} ===")
            
            # Scrape the listing page
            courses = scrape_revision_page(revision, doc_type)
            print(f"Found {len(courses)} courses on listing page")
            
            # For each course, check if we have the PDF
            for course in courses:
                key = (revision, doc_type, course["code"])
                
                if key in already_exists or key in existing_docs:
                    already_exists += 1
                    continue
                
                # Try to find PDF link on course page
                print(f"  Checking course {course['code']}...")
                course_html = fetch_page(course["url"])
                
                if course_html:
                    pdf_links = find_pdf_links(course_html)
                    
                    if pdf_links:
                        # Found a PDF link - download it
                        pdf_url = pdf_links[0]
                        if not pdf_url.startswith("http"):
                            pdf_url = f"https://www.sitttrkerala.ac.in/{pdf_url.lstrip('/')}"
                        
                        print(f"    Found PDF: {pdf_url}")
                        
                        # Determine department from course code
                        dept_code = course["code"][:2]
                        dept_name = DEPARTMENTS.get(dept_code, "Unknown")
                        
                        # Create filename
                        filename = f"{course['code']}.pdf"
                        dest_path = SITTTR_DIR / f"revision-{revision}" / doc_type / dept_name.lower().replace(" & ", "-").replace(" ", "-") / "semester-unspecified" / filename
                        
                        if download_pdf(pdf_url, dest_path):
                            print(f"    Downloaded: {dest_path}")
                            new_downloaded += 1
                            
                            # Calculate hash and page count
                            sha256 = calculate_sha256(dest_path)
                            pages = get_pdf_pages(dest_path)
                            size = dest_path.stat().st_size
                            
                            # Add to index
                            new_doc = {
                                "revision": revision,
                                "documentType": doc_type,
                                "departmentCode": dept_code,
                                "department": dept_name,
                                "semester": "semester-unspecified",
                                "courseCode": course["code"],
                                "courseName": filename.replace(".pdf", "").replace("-", " ").title(),
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
                            print(f"    Failed to download")
                    else:
                        print(f"    No PDF found on course page")
    
    print(f"\n=== Summary ===")
    print(f"Already in index: {already_exists}")
    print(f"Newly downloaded: {new_downloaded}")
    
    # Save updated index
    if new_downloaded > 0:
        from datetime import datetime
        index["generatedAt"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
        print(f"Updated {INDEX_FILE}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
