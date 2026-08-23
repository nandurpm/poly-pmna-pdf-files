#!/usr/bin/env python3
"""Retry downloading missing SITTTR PDFs when the server is available.

Usage:
    python3 retry_missing.py [revision]
    
    revision: 2021, 2026, or 'all' (default: all)
    
This script:
1. Scrapes SITTTR department pages to find all courses
2. Compares with existing PDFs on disk
3. Downloads missing PDFs
4. Updates the manifests
"""
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
    """Fetch a webpage and return its content."""
    try:
        req = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urlopen(req, timeout=20) as response:
            return response.read().decode("utf-8", errors="ignore")
    except Exception as e:
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
    except Exception as e:
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
            ["pdfinfo", str(file_path)], capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.split("\n"):
            if line.startswith("Pages:"):
                return int(line.split(":")[1].strip())
    except Exception:
        pass
    return 0


def slugify(name: str) -> str:
    """Convert a department name to a URL-friendly slug."""
    return (
        name.lower()
        .replace(" & ", "-and-")
        .replace(" and ", "-and-")
        .replace(" ", "-")
        .replace("(", "")
        .replace(")", "")
    )


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
    pattern = r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>\s*([^<]+)\s*</a>'
    for href, name in re.findall(pattern, html):
        if "prog=" in href:
            full_url = href.replace("&amp;", "&")
            if not full_url.startswith("http"):
                full_url = f"https://www.sitttrkerala.ac.in/{full_url.lstrip('/')}"
            depts.append({"name": name.strip(), "url": full_url})

    return depts


def get_courses(dept_url: str) -> list[dict]:
    """Get course links from a department page."""
    html = fetch_page(dept_url)
    if not html:
        return []

    courses = []
    pattern = r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>\s*([^<]+)\s*</a>'
    for href, name in re.findall(pattern, html):
        if "course=" in href:
            course_match = re.search(r"course=(\d+[A-Z]*)", href)
            if course_match:
                full_url = href.replace("&amp;", "&")
                if not full_url.startswith("http"):
                    full_url = f"https://www.sitttrkerala.ac.in/{full_url.lstrip('/')}"
                courses.append({
                    "code": course_match.group(1),
                    "name": name.strip(),
                    "url": full_url,
                })

    return courses


def get_pdf_url(course_url: str) -> str | None:
    """Get PDF URL from a course page."""
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


def process_revision(revision: str) -> int:
    """Process one revision: scrape, compare, download, update manifest."""
    print(f"\n{'='*60}")
    print(f"Processing Revision {revision}")
    print(f"{'='*60}")

    manifest_file = MANIFEST_DIR / f"sitttr-{revision}.json"
    with open(manifest_file, encoding="utf-8") as f:
        data = json.load(f)

    existing_paths = {d["path"] for d in data["documents"]}
    downloaded = 0

    for doc_type in ["syllabus", "model-question-paper"]:
        print(f"\n--- {doc_type} ---")

        depts = get_dept_links(revision, doc_type)
        print(f"Found {len(depts)} departments")

        for dept in depts:
            dept_slug = slugify(dept["name"])
            print(f"\n  Department: {dept['name']} ({dept_slug})")
            time.sleep(0.5)

            courses = get_courses(dept["url"])
            print(f"  Found {len(courses)} courses")

            for course in courses:
                # Check if already downloaded
                rel_path = f"sitttr/revision-{revision}/{doc_type}/{dept_slug}/semester-unspecified/{course['code']}.pdf"
                if rel_path in existing_paths:
                    continue

                # Also check with course name in filename
                name_slug = slugify(course["name"])
                rel_path_named = f"sitttr/revision-{revision}/{doc_type}/{dept_slug}/semester-unspecified/{course['code']}-{name_slug}.pdf"
                if rel_path_named in existing_paths:
                    continue

                # Try to find PDF
                print(f"    Course {course['code']}: {course['name']}")
                pdf_url = get_pdf_url(course["url"])

                if pdf_url:
                    filename = f"{course['code']}.pdf"
                    dest_path = SITTTR_DIR / f"revision-{revision}" / doc_type / dept_slug / "semester-unspecified" / filename

                    if download_pdf(pdf_url, dest_path):
                        print(f"      Downloaded: {dest_path}")
                        downloaded += 1

                        sha256 = calculate_sha256(dest_path)
                        pages = get_pdf_pages(dest_path)
                        size = dest_path.stat().st_size

                        new_doc = {
                            "revision": revision,
                            "documentType": doc_type,
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
                            "status": "published",
                        }
                        data["documents"].append(new_doc)
                        existing_paths.add(new_doc["path"])
                else:
                    print(f"      No PDF found")

            time.sleep(0.3)

    # Save updated manifest
    if downloaded > 0:
        from datetime import datetime
        data["generatedAt"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\nUpdated {manifest_file} with {downloaded} new PDFs")
    else:
        print(f"\nNo new PDFs downloaded for revision {revision}")

    return downloaded


def rebuild_index():
    """Rebuild the index manifest from individual revision manifests."""
    index = {
        "schemaVersion": 1,
        "generatedAt": "",
        "source": "https://www.sitttrkerala.ac.in",
        "sourcePolicy": "Official SITTTR pages; only endpoints returning readable PDFs are included.",
        "rawBaseUrl": "https://raw.githubusercontent.com/nandurpm/poly-pmna-pdf-files/main",
        "documents": [],
    }

    for manifest_file in sorted(MANIFEST_DIR.glob("sitttr-20*.json")):
        with open(manifest_file) as f:
            data = json.load(f)
        index["documents"].extend(data["documents"])

    # Deduplicate
    seen = set()
    unique = []
    for doc in index["documents"]:
        if doc["path"] not in seen:
            seen.add(doc["path"])
            unique.append(doc)
    index["documents"] = unique

    from datetime import datetime
    index["generatedAt"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    with open(MANIFEST_DIR / "sitttr-index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"Rebuilt index: {len(unique)} documents")


def main():
    revisions = sys.argv[1:] if len(sys.argv) > 1 else ["2021", "2026"]

    total = 0
    for rev in revisions:
        if rev == "all":
            continue
        try:
            total += process_revision(rev)
        except Exception as e:
            print(f"Error processing revision {rev}: {e}")

    if total > 0:
        print(f"\nRebuilding index...")
        rebuild_index()

    print(f"\nTotal new PDFs downloaded: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
