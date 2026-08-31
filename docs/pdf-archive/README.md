# Shared PDF archive interface

This directory documents the shared interface used by the three POLY PMNA repositories.

The canonical source remains at the repository root:

- `manifests/notes-2021.json`
- `manifests/notes-2026.json`
- `manifests/sitttr-2026.json`
- `notes/<revision>/<subject-code>/v1/<subject-code>.pdf`

The two consumer repositories receive refreshed manifest snapshots under their matching `docs/pdf-archive/manifests/` directory when the source repository changes. PDF binaries are intentionally not copied into the consumers; application links continue to resolve to the canonical raw URLs in `poly-pmna-pdf-files`.

The source workflow `.github/workflows/notify-pdf-consumers.yml` dispatches `pdf-archive-updated` events to `diploma-notes` and `polypmna`. Each consumer workflow refreshes its local manifest snapshots and writes `docs/pdf-archive-sync.json` with the source commit, changed paths, and published counts.
