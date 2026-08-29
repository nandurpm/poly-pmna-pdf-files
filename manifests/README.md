# PDF Manifests

## Purpose

This folder is the machine-readable index for both PDF collections. Consumers
should use these records instead of inferring a document path from its title.

Store one manifest per curriculum revision, for example `notes-2021.json` and `notes-2026.json`.

Each subject record should include:

- `code`
- `title`
- `revision`
- `pdfUrl`
- `version`
- `bytes`
- `sha256`
- `pages`
- `status`

## SITTTR Manifests

For SITTTR documents, use revision-specific manifests:

- `sitttr-2015.json`
- `sitttr-2021.json`
- `sitttr-2026.json`
- `sitttr-index.json` (complete machine-readable index)

### SITTTR Manifest Schema

Each SITTTR manifest record includes:

```json
{
  "sourceOrganization": "State Institute of Technical Teachers' Training & Research (SITTTR), Kalamassery",
  "sourceWebsite": "https://sitttrkerala.ac.in/",
  "sourcePage": "OFFICIAL_SITTTR_PAGE_URL",
  "sourcePdf": "DIRECT_SITTTR_PDF_URL",
  "revision": "2021",
  "department": "Example Department",
  "semester": 3,
  "subjectCode": "XXXX",
  "subjectTitle": "Example Subject",
  "documentType": "syllabus",
  "verificationStatus": "verified",
  "bytes": 123456,
  "sha256": "abc123...",
  "pages": 42
}
```

### SITTTR Verification Status

Mark `verificationStatus` as:
- `verified` - Official SITTTR PDF confirmed
- `unavailable` - SITTTR page exists but no PDF published
- `missing` - Document not found on SITTTR

See [`sitttr/README.md`](../sitttr/README.md) for complete SITTTR source documentation and verification rules.

## Responsibilities

Place revision-specific JSON manifests and the aggregate SITTTR index here.
Binary documents and scraping code belong in their respective archive folders
or at the repository root, not alongside the indexes.

## Important notes

Whenever a published PDF changes, allocate the intended version, recalculate its
byte size, page count, and SHA-256 checksum, and update its canonical URL in the
same change. Do not mark an entry `verified` unless its source and local file have
both been checked.
