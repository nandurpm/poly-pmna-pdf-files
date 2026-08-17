# SITTTR PDF archive

This directory contains PDFs downloaded from the official [State Institute of Technical Teachers’ Training & Research, Kerala (SITTTR)](https://www.sitttrkerala.ac.in/) pages. It is separate from the generated study-note archive under `notes/`.

## Folder layout

Each document is organized as follows:

```text
sitttr/revision-<year>/<document-type>/<department>/<semester>/<course-code>-<course-name>.pdf
```

The document types are `syllabus` and `model-question-papers`. General revision documents such as rules or handbooks are stored under `_general/`. The official SITTTR website currently labels the older collection **Revision 2015**; this is the collection requested as “201t”.

## Availability and validation

Only URLs that returned a readable PDF were copied. Department tables may list courses for which SITTTR has not published a PDF; those entries are excluded from the visible archive and counted in `manifests/sitttr-index.json`. Every included file was checked with `pdfinfo` and recorded with its byte size, page count, SHA-256 checksum, original source URL, and raw GitHub URL.

| Revision | Document type | Candidates | Published PDFs | Not published / unavailable |
| --- | --- | ---: | ---: | ---: |
| 2015 | model-question-paper | 662 | 464 | 198 |
| 2015 | syllabus | 1139 | 1113 | 26 |
| 2021 | model-question-paper | 1465 | 964 | 501 |
| 2021 | syllabus | 2732 | 2701 | 31 |
| 2026 | model-question-paper | 1149 | 364 | 785 |
| 2026 | syllabus | 2666 | 669 | 1997 |

See [`manifests/sitttr-index.json`](../manifests/sitttr-index.json) for the complete machine-readable index and [`manifests/sitttr-2021.json`](../manifests/sitttr-2021.json), [`manifests/sitttr-2026.json`](../manifests/sitttr-2026.json), and [`manifests/sitttr-2015.json`](../manifests/sitttr-2015.json) for revision-specific indexes.

The imported archive contains **6275 validated PDFs** totaling approximately **966.8 MiB**.
