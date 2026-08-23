# PDF Manifests

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
