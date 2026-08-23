#!/usr/bin/env python3
"""List all missing SITTTR documents from the index."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST_DIR = ROOT / "manifests"
INDEX_FILE = MANIFEST_DIR / "sitttr-index.json"


def main():
    print("=== SITTTR Missing Documents Report ===\n")
    
    # Load index
    if not INDEX_FILE.exists():
        print(f"Error: {INDEX_FILE} not found")
        sys.exit(1)
    
    with open(INDEX_FILE, encoding="utf-8") as f:
        index = json.load(f)
    
    # Get list of published documents
    published = {}
    for doc in index["documents"]:
        key = (doc["revision"], doc["documentType"], doc["courseCode"])
        published[key] = doc
    
    # Group by revision and document type
    missing = {}
    for avail in index["availability"]:
        revision = avail["revision"]
        doc_type = avail["documentType"]
        key = f"{revision}_{doc_type}"
        
        # Get all documents for this revision/type
        docs = [d for d in index["documents"] if d["revision"] == revision and d["documentType"] == doc_type]
        
        # Find missing ones
        missing[key] = {
            "revision": revision,
            "documentType": doc_type,
            "total_candidates": avail["candidates"],
            "published": avail["published"],
            "missing_count": avail["unavailableOrNotPublished"],
            "documents": []
        }
        
        # We need to reconstruct the missing documents from the availability info
        # Since the index only contains published documents, we'll report what we know
    
    # Print summary
    print("Summary:")
    print(f"{'Revision':<10} {'Document Type':<25} {'Published':<10} {'Missing':<10} {'Total':<10}")
    print("-" * 75)
    
    total_published = 0
    total_missing = 0
    
    for key in sorted(missing.keys()):
        info = missing[key]
        print(f"{info['revision']:<10} {info['documentType']:<25} {info['published']:<10} {info['missing_count']:<10} {info['total_candidates']:<10}")
        total_published += info['published']
        total_missing += info['missing_count']
    
    print("-" * 75)
    print(f"{'TOTAL':<10} {'':<25} {total_published:<10} {total_missing:<10} {total_published + total_missing:<10}")
    
    print(f"\n=== Missing Documents by Revision ===\n")
    
    # For each revision, show some example missing documents
    for revision in ["2015", "2021", "2026"]:
        print(f"Revision {revision}:")
        
        # Get all published documents for this revision
        revision_published = [d for d in index["documents"] if d["revision"] == revision]
        
        # Group by department
        departments = {}
        for doc in revision_published:
            dept = doc["department"]
            if dept not in departments:
                departments[dept] = {"syllabus": set(), "model-question-paper": set()}
            departments[dept][doc["documentType"]].add(doc["courseCode"])
        
        # Show departments with missing documents
        for dept in sorted(departments.keys()):
            syllabus_count = len(departments[dept]["syllabus"])
            mqp_count = len(departments[dept]["model-question-paper"])
            
            # Get expected counts from availability
            for avail in index["availability"]:
                if avail["revision"] == revision:
                    if avail["documentType"] == "syllabus":
                        expected_syllabus = avail["candidates"] // len(departments)  # Rough estimate
                    elif avail["documentType"] == "model-question-paper":
                        expected_mqp = avail["candidates"] // len(departments)  # Rough estimate
            
            if syllabus_count > 0 or mqp_count > 0:
                print(f"  {dept}:")
                print(f"    Syllabus: {syllabus_count} published")
                print(f"    Model Question Papers: {mqp_count} published")
        
        print()
    
    print("=== To check for newly available PDFs, run: ===")
    print("python3 check_missing_sitttr.py")
    print()
    print("=== To manually check SITTTR website, visit: ===")
    print("Revision 2015: https://www.sitttrkerala.ac.in/index.php?r=site%2Fdiploma-syllabus&scheme=REV2015")
    print("Revision 2021: https://www.sitttrkerala.ac.in/index.php?r=site%2Fdiploma-syllabus&scheme=REV2021")
    print("Revision 2026: https://sitttrkerala.ac.in/index.php?r=site/home")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
