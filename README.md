# POLY PMNA PDF Files

This public repository is dedicated to PDF study-note distribution for the [POLY PMNA website](https://polypmna.dpdns.org/).

## Archive layout

PDF files must be organized by curriculum revision and stable subject code:

```text
notes/2021/<subject-code>/v1/<subject-code>.pdf
notes/2026/<subject-code>/v1/<subject-code>.pdf
```

The `manifests/` directory contains metadata such as subject title, revision, public URL, byte size, page count, and SHA-256 checksum.

## Upload policy

Do not commit PDFs directly to the default branch unless the file size and long-term Git-history impact have been reviewed. For a large archive, publish the PDFs as versioned release assets or use object storage such as Cloudflare R2. Never overwrite a published PDF silently; use a new version directory such as `v2` and update the manifest.

Every published file must be validated as a readable PDF and recorded in the checksum manifest. Upload credentials, private keys, local staging files, and backup bundles must never be committed.

## Download URLs

If PDFs are stored in this repository's default branch, use stable raw URLs only after the archive has been validated. If PDFs are published as release assets, use versioned release URLs. The POLY PMNA website should consume the manifest rather than constructing filenames from display titles.

## Current state

The repository is initialized with the archive structure and policy documentation. PDF binaries have not been uploaded yet.
