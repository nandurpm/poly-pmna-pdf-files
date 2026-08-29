# Lesson PDF Archive

## Purpose

Contains PDFs generated from the POLY PMNA lesson pages. These files are the
stable, direct-download copies referenced by the revision manifests and website.

## Contents

Documents follow `notes/<revision>/<subject-code>/<version>/<subject-code>.pdf`.
The current collection covers the 2021 and 2026 curriculum revisions and starts
at `v1` for each subject.

## Responsibilities

Only generated lesson PDFs at canonical, versioned paths belong here. Official
SITTTR publications belong under `sitttr/`; indexes and metadata belong under
`manifests/`.

## Important notes

Do not overwrite a published version. Add a new version directory when content
must change, then update the appropriate manifest with its URL, checksum, size,
and page count. The complete checkout is large, so use sparse checkout only for
documentation work that does not need to validate the PDF objects.
