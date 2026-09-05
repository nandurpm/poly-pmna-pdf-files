# Upload once, use on both websites

After this change is merged, the **Index PDFs and notify consumers** workflow
validates uploads, updates the archive catalog and lesson manifests, then notifies
both consumer repositories using the existing `PDF_CONSUMERS_TOKEN` secret
(`CROSS_REPO_SYNC_TOKEN` is accepted as a fallback).

## Uploading a lesson PDF

Upload to `notes/<2021-or-2026>/<code>/v<number>/<code>.pdf` on `main`.
For example, `notes/2026/1141/v2/1141.pdf`. Use a new, increasing version
number to retain existing published versions. The highest numeric version is
selected automatically. Readable PDFs get a checksum, page count, size and
published manifest entry. Existing subject titles are retained; for a new subject,
edit its title in the manifest if the default `Course <code>` is insufficient.

Both sites read the published manifest and use its exact URL. Refresh the page
after the workflow succeeds; GitHub's raw-file cache can add a short delay.
Adding a new curriculum subject still requires adding the course to the curriculum
data. A PDF upload cannot infer a programme or semester assignment reliably.

## Other PDFs

Every PDF, including PDFs outside the lesson layout, appears in
`manifests/archive-index.json` and the **All PDFs** page on both websites:

- `https://polypmna.dpdns.org/pdf-library.html`
- `https://gptcperinthalmanna.dpdns.org/pdf-library.html`

SITTTR subject-specific metadata still belongs in the corresponding SITTTR
manifest. The generic catalog does not claim that an uploaded file is official
or assign a course from an arbitrary filename.

## Preserving the existing PDFs

The first run copies every tracked PDF from `diploma-notes` into
`legacy/diploma-notes/<source-commit>/<original-path>`. Every copy is checked
against the original Git blob, and its SHA-256 is recorded in
`manifests/legacy-diploma-notes.json`. These historical files are visible in the
All PDFs catalog. They do not replace the current canonical lesson versions.
Existing source files are retained so historical URLs remain valid. Removal of
those copies needs a separate redirect/deployment migration.

If PDFs are added to diploma-notes later, run this workflow with `import_legacy`
enabled. Future PDF uploads should go directly to this archive.

## Verification after merging

1. Merge the consumer changes, then this archive change.
2. Confirm the archive workflow succeeds, including legacy preservation.
3. Confirm **Sync PDF archive reference** succeeds in both consumer repositories.
4. Open All PDFs on both sites and verify the same catalog and a sample download.
5. Upload a real new version at the documented path and confirm the subject's
   download URL changes to that version after the successful workflow and refresh.

No cross-repository secret values are committed. The duplicate notification
workflow was removed so there is one indexing-before-notification sequence.
