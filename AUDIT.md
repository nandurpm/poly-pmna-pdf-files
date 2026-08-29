# Archive integrity audit

Audit date: 2026-08-29

## Manifest/File Consistency

The complete archive was checked, rather than sampled. All 1,372 files under `notes/`
have exactly one subject record; every record resolves to an existing file. Recorded byte
sizes and SHA-256 values match. All records are `published`, have a positive recorded page
count, and use the canonical raw URL. No manifest or file correction was required.

`test_manifests.py` now enforces these properties for every notes and SITTTR record. The
old checks inspected only 20 paths and five hashes per manifest, allowing errors elsewhere
to pass.

## PDF Validity

All notes files have a PDF header, `startxref` and EOF trailer, are at least 1 KiB, and
have a positive manifest page count. No duplicate byte-identical notes documents were
found. A PDF parser was unavailable in the audit environment, so page-tree parsing could
not be independently repeated; the structural checks and pipeline-recorded counts passed.
No PDF requires regeneration.

## Versioning

**Unresolved upstream policy violation:** the available Git history shows existing `v1`
paths being modified by repeated `Sync lesson PDFs` commits, while the current tree has no
`v2` notes directory. This is silent overwrite under the documented retention policy.
Historical versions must not be guessed or reconstructed into the current manifest.
The `diploma-notes` publisher must allocate the next version directory and update
`version`/`pdfUrl` atomically before the next changed render. This **requires a change and
re-run of the diploma-notes automation**. Existing historical recovery should be treated
as a separate, explicitly reviewed migration.

## Path/Naming

All notes paths match
`notes/<revision>/<code>/<version>/<code>.pdf`; folder/file code, revision, version and
manifest URL agree exactly, including case. No correction was required.

## sitttr/

SITTTR is intentionally managed separately through revision manifests plus
`sitttr-index.json`; all indexed paths, sizes and hashes agree with disk. The maintenance
script was stale: it ignored the live `lab-manual` and singular
`model-question-paper` categories. Its category list now covers the actual layout without
moving or restructuring archived files.

## Secrets Hygiene

Fourteen committed Python bytecode cache files were local build artifacts. They were
removed. `.gitignore` now excludes Python caches, common backup bundles, additional key
stores and common SSH private-key names as well as the existing staging, upload,
environment and PEM/key rules. No suspiciously named credential, key, staging or backup
file remains in the current tracked tree.

The checkout is shallow and network access was denied, so a claim about the complete
remote history would be unsafe. The available history and current tree were scanned; a
full secret scan must be run in a non-shallow clone before declaring all-history clean.
If a real secret is found, removing a file in a new commit is insufficient: revoke it and
rewrite the affected history.

## Pipeline

The cross-repository `diploma-notes` checkout and GitHub source were unavailable because
outbound access was denied. Token scope, Chromium failure handling and partial-batch
semantics therefore could not be verified and are not guessed here. Upstream follow-up
must verify that the token is limited to this repository, every render is parser-validated
before staging, a failure cannot publish its PDF or manifest record, and the chosen batch
policy is atomic and explicit. Version allocation must also be fixed as described above.

## Git Attributes

PDFs were already marked `-text`, but not explicitly binary/generated. The rule is now
`binary linguist-generated=true`, preventing text conversion/diffs and classifying the
pipeline output accurately.
