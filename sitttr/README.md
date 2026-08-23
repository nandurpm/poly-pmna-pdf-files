# SITTTR PDF Archive

This directory contains PDFs downloaded from the official [State Institute of Technical Teachers' Training & Research, Kerala (SITTTR)](https://www.sitttrkerala.ac.in/) pages. It is separate from the generated study-note archive under `notes/`.

## Official SITTTR Sources

**SITTTR (State Institute of Technical Teachers' Training & Research, Kalamassery) must be treated as the primary official source** for all syllabus and model-question-paper collection, auditing, and verification.

| Resource | URL |
| --- | --- |
| SITTTR Official Website | https://sitttrkerala.ac.in/ |
| SITTTR Academic / Courses | https://sitttrkerala.ac.in/index.php?r=site/home |
| Diploma Syllabus – Revision 2015 | https://www.sitttrkerala.ac.in/index.php?r=site%2Fdiploma-syllabus&scheme=REV2015 |
| Diploma Syllabus – Revision 2021 | https://www.sitttrkerala.ac.in/index.php?r=site%2Fdiploma-syllabus&scheme=REV2021 |
| Model Question Papers – Revision 2015 | https://sitttrkerala.ac.in/index.php?r=site%2Fdiploma-modelqp&scheme=REV2015 |
| Model Question Papers – Revision 2021 | https://sitttrkerala.ac.in/index.php?r=site%2Fdiploma-modelqp&scheme=REV2021 |
| Revision 2021 Handbook | https://sitttrkerala.ac.in/syllabus/rev2021/handbook-rev2021.pdf |
| Revision 2021 Rules | https://sitttrkerala.ac.in/syllabus/rev2021/rules-rev2021.pdf |

## Source-of-Truth Policy

For every missing document, follow this order:

```text
POLY PMNA existing repository
        ↓
Official SITTTR
        ↓
Official Government / DTE Kerala source
        ↓
Other authoritative educational source
        ↓
Mark as MISSING if no trustworthy source exists
```

**Never skip the SITTTR check** for diploma syllabus and model question papers.

## Folder Layout

Each document is organized as follows:

```text
sitttr/revision-<year>/<document-type>/<department>/<semester>/<course-code>-<course-name>.pdf
```

Document types:
- `syllabus`
- `model-question-papers`
- `lab-manual`

General revision documents (rules, handbooks) are stored under `_general/`.

## Revision 2015

### Syllabus

Official SITTTR page:
https://www.sitttrkerala.ac.in/index.php?r=site%2Fdiploma-syllabus&scheme=REV2015

Use this page to verify:
- Department/programme
- Curriculum revision
- Programme scheme
- Syllabus documents
- Subject information

### Model Question Papers

Official SITTTR page:
https://sitttrkerala.ac.in/index.php?r=site%2Fdiploma-modelqp&scheme=REV2015

Use this page to collect and verify official model question papers for Revision 2015.

## Revision 2021

### Syllabus

Official SITTTR page:
https://sitttrkerala.ac.in/index.php?r=site%2Fdiploma-syllabus&scheme=REV2021

Use this as the primary official source for:
- Revision 2021 programme schemes
- Department/programme verification
- Syllabus PDFs
- Subject codes
- Subject titles
- Semester structure

### Handbook

Official SITTTR handbook:
https://sitttrkerala.ac.in/syllabus/rev2021/handbook-rev2021.pdf

Use when verifying structure, terminology, curriculum framework, and Revision 2021 implementation details.

### Rules and Regulations

Official SITTTR document:
https://sitttrkerala.ac.in/syllabus/rev2021/rules-rev2021.pdf

Use as supporting official documentation when validating the Revision 2021 curriculum structure and rules.

### Model Question Papers

Official SITTTR page:
https://sitttrkerala.ac.in/index.php?r=site%2Fdiploma-modelqp&scheme=REV2021

Use as the primary official source for Revision 2021 model question papers.

## Revision 2026

Navigate through the current official SITTTR site to locate dedicated Revision 2026 syllabus/programme pages:

https://sitttrkerala.ac.in/index.php?r=site/home

**Do not assume** that Revision 2026 has exactly the same departments, subjects, codes, semester structure, or model-question-paper availability as Revision 2021. Verify Revision 2026 directly against the official SITTTR curriculum before importing documents.

## Document Verification Rules

Before importing a SITTTR document, verify:

```text
SITTTR source
      ↓
Revision
      ↓
Programme / Department
      ↓
Semester
      ↓
Subject Code
      ↓
Subject Title
      ↓
Document Type
      ↓
PDF
```

Example - Syllabus:
```text
Revision 2021
→ Computer Engineering
→ Semester 3
→ Subject Code XXXXX
→ Subject Title XXXXX
→ Syllabus
→ Official SITTTR PDF
```

Example - Model Question Paper:
```text
Revision 2015
→ Electrical & Electronics Engineering
→ Semester 5
→ Subject Code XXXXX
→ Subject Title XXXXX
→ Model Question Paper
→ Official SITTTR PDF
```

## DO NOT Confuse SITTTR Pages with PDF Files

Some SITTTR pages are index/listing pages, while individual subjects may link to separate documents.

**Process:**
1. Open the official SITTTR revision page
2. Identify the programme
3. Identify the subject
4. Follow the specific official document link
5. Download the actual PDF where available
6. Validate the PDF
7. Record both:
   - Original SITTTR page URL
   - Direct PDF URL (when available)

**Do not store only the SITTTR listing page** when the actual PDF is available.

## SITTTR Source Metadata

For every imported SITTTR PDF, add metadata:

### Syllabus metadata:
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
  "verificationStatus": "verified"
}
```

### Model Question Paper metadata:
```json
{
  "sourceOrganization": "State Institute of Technical Teachers' Training & Research (SITTTR), Kalamassery",
  "sourceWebsite": "https://sitttrkerala.ac.in/",
  "sourcePage": "OFFICIAL_SITTTR_MODEL_QP_PAGE",
  "sourcePdf": "DIRECT_SITTTR_PDF_URL",
  "revision": "2015",
  "department": "Example Department",
  "semester": 5,
  "subjectCode": "XXXX",
  "subjectTitle": "Example Subject",
  "documentType": "model-question-paper",
  "verificationStatus": "verified"
}
```

## SITTTR Model Question Paper Check

Do not simply check whether a model-question-paper folder exists.

For every SITTTR programme listed on the official model-paper page:

```text
Programme
→ Semester
→ Subject
→ Subject Code
→ Model Question Paper
```

perform an availability check.

SITTTR provides individual model-paper pages containing actual question-paper content for Revision 2015 subjects. Those documents must be treated as official SITTTR model-question-paper sources and mapped correctly rather than being mixed with unrelated previous examination papers.

## Completion Check

At the end, produce a report showing:

```text
SITTTR Revision 2015
├── Syllabus:        XX / XX
└── Model Papers:    XX / XX

SITTTR Revision 2021
├── Syllabus:        XX / XX
└── Model Papers:    XX / XX

SITTTR Revision 2026
├── Syllabus:        XX / XX
└── Model Papers:    XX / XX
```

For every missing item, show:

```text
Revision
Department
Semester
Subject Code
Subject Title
Document Type
SITTTR page checked
Status
Reason
```

Do not report a document as complete merely because an SITTTR programme page exists. The actual required subject-level document must be verified.

## Availability and Validation

Only URLs that returned a readable PDF were copied. Department tables may list courses for which SITTTR has not published a PDF; those entries are excluded from the visible archive and counted in `manifests/sitttr-index.json`. Every included file was checked with `pdfinfo` and recorded with its byte size, page count, SHA-256 checksum, original source URL, and raw GitHub URL.

| Revision | Document type | Published PDFs |
| --- | --- | ---: |
| 2015 | model-question-paper | 464 |
| 2015 | syllabus | 1113 |
| 2021 | model-question-paper | 1374 |
| 2021 | syllabus | 3461 |
| 2026 | lab-manual | 22 |
| 2026 | model-question-paper | 800 |
| 2026 | syllabus | 669 |
| general | academic-calendar | 9 |
| general | special-docs | 73 |
| **TOTAL** | | **7985** |

See [`manifests/sitttr-index.json`](../manifests/sitttr-index.json) for the complete machine-readable index and [`manifests/sitttr-2021.json`](../manifests/sitttr-2021.json), [`manifests/sitttr-2026.json`](../manifests/sitttr-2026.json), and [`manifests/sitttr-2015.json`](../manifests/sitttr-2015.json) for revision-specific indexes.

The imported archive contains **7985 validated PDFs**.
