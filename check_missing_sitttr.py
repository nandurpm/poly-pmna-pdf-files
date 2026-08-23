#!/usr/bin/env python3
"""Check SITTTR website for newly available PDFs and download them."""
from __future__ import annotations

import json
import hashlib
import subprocess
import sys
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

ROOT = Path(__file__).resolve().parent
MANIFEST_DIR = ROOT / "manifests"
SITTTR_DIR = ROOT / "sitttr"
INDEX_FILE = MANIFEST_DIR / "sitttr-index.json"

# SITTTR base URLs
SITTTR_BASE = "https://www.sitttrkerala.ac.in/index.php"
SITTTR_MQP_URL = f"{SITTTR_BASE}?r=site%2Fdiploma-modelqp-courses-show&course="
SITTTR_SYLLABUS_URL = f"{SITTTR_BASE}?r=site%2Fdiploma-syllabus-courses-show&course="


def get_pdf_url_from_sitttr(course_code: str, document_type: str) -> str | None:
    """Try to find PDF URL from SITTTR website for a given course code."""
    if document_type == "model-question-paper":
        base_url = SITTTR_MQP_URL
    else:
        base_url = SITTTR_SYLLABUS_URL
    
    try:
        url = f"{base_url}{course_code}"
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=10) as response:
            html = response.read().decode("utf-8", errors="ignore")
            
            # Look for PDF links in the HTML
            import re
            pdf_pattern = re.compile(r'href=["\']([^"\']*\.pdf)["\']', re.IGNORECASE)
            matches = pdf_pattern.findall(html)
            
            if matches:
                # Return the first PDF link found
                pdf_url = matches[0]
                if not pdf_url.startswith("http"):
                    pdf_url = f"https://www.sitttrkerala.ac.in/{pdf_url.lstrip('/')}"
                return pdf_url
    except (URLError, HTTPError, Exception) as e:
        print(f"  Error checking {course_code}: {e}")
    
    return None


def download_pdf(url: str, dest_path: Path) -> bool:
    """Download a PDF file."""
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=30) as response:
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


def main():
    print("=== SITTTR Missing PDF Checker ===\n")
    
    # Load index
    if not INDEX_FILE.exists():
        print(f"Error: {INDEX_FILE} not found")
        sys.exit(1)
    
    with open(INDEX_FILE, encoding="utf-8") as f:
        index = json.load(f)
    
    # Get list of published documents
    published = set()
    for doc in index["documents"]:
        key = (doc["revision"], doc["documentType"], doc["courseCode"])
        published.add(key)
    
    # Get availability info
    print("Current availability:")
    for avail in index["availability"]:
        print(f"  {avail['revision']} {avail['documentType']}: {avail['published']}/{avail['candidates']} published")
    print()
    
    # Check for unavailable documents
    print("Checking SITTTR website for newly available PDFs...\n")
    
    found_new = 0
    downloaded = 0
    
    # For each revision and document type
    for revision in ["2015", "2021", "2026"]:
        for doc_type in ["model-question-paper", "syllabus"]:
            # Get all candidates for this revision/type
            candidates = []
            for doc in index["documents"]:
                if doc["revision"] == revision and doc["documentType"] == doc_type:
                    candidates.append(doc)
            
            # Check each candidate
            for doc in candidates:
                key = (doc["revision"], doc["documentType"], doc["courseCode"])
                if key in published:
                    continue  # Already have this PDF
                
                # This document is unavailable, try to find it
                print(f"Checking: {doc['revision']} | {doc['department']} | {doc['courseCode']} | {doc['courseName']}")
                
                pdf_url = get_pdf_url_from_sitttr(doc["courseCode"], doc["documentType"])
                
                if pdf_url:
                    print(f"  Found PDF: {pdf_url}")
                    found_new += 1
                    
                    # Download the PDF
                    filename = f"{doc['courseCode']}-{doc['courseName'].lower().replace(' ', '-')}.pdf"
                    dest_path = SITTTR_DIR / f"revision-{doc['revision']}" / doc["documentType"] / doc["department"].lower().replace(" ", "-") / "semester-unspecified" / filename
                    
                    if download_pdf(pdf_url, dest_path):
                        print(f"  Downloaded: {dest_path}")
                        downloaded += 1
                        
                        # Calculate hash and page count
                        sha256 = calculate_sha256(dest_path)
                        pages = get_pdf_pages(dest_path)
                        size = dest_path.stat().st_size
                        
                        # Add to index
                        new_doc = {
                            "revision": doc["revision"],
                            "documentType": doc["documentType"],
                            "departmentCode": doc["departmentCode"],
                            "department": doc["department"],
                            "semester": "semester-unspecified",
                            "courseCode": doc["courseCode"],
                            "courseName": doc["courseName"],
                            "path": str(dest_path.relative_to(ROOT)),
                            "pdfUrl": f"https://raw.githubusercontent.com/nandurpm/poly-pmna-pdf-files/main/{dest_path.relative_to(ROOT)}",
                            "sourceUrl": pdf_url,
                            "bytes": size,
                            "pages": pages,
                            "sha256": sha256,
                            "status": "published"
                        }
                        index["documents"].append(new_doc)
                        published.add(key)
                    else:
                        print(f"  Failed to download")
                else:
                    print(f"  No PDF found on SITTTR")
    
    print(f"\n=== Summary ===")
    print(f"New PDFs found: {found_new}")
    print(f"Successfully downloaded: {downloaded}")
    
    # Save updated index
    if downloaded > 0:
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
        print(f"Updated {INDEX_FILE}")
    
    return 0 if downloaded > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
