# PDF integration audit — 5 September 2026

Default-branch Git trees were inspected through the GitHub API; none were truncated.

| Repository | Audited commit | PDF files | Bytes |
| --- | --- | ---: | ---: |
| poly-pmna-pdf-files | 94f7c1d9454df382cfec0c1d90e17f4a7e1920d5 | 9379 | 2119758264 |
| diploma-notes | 3570612aa127714a986fbcdcfa5c34f19ebe93da | 237 | 3161473172 |
| polypmna | b678f63e23071ff0c565138287c9c3a53e4b1a23 | 0 | 0 |

Both note manifests were checked against the archive tree: 172 Revision 2021 and 1,222 Revision 2026 published entries all have existing files with matching byte sizes. This is a path/size check, not a complete PDF content validation.

None of the 237 diploma-notes PDF Git blob hashes occurs in the archive tree. They are different versions, not proven duplicate binaries. The proposed migration preserves each original with its source path and commit before any future removal from the consumer.

The archive's latest PDF_CONSUMERS_TOKEN notification run [succeeded](https://github.com/nandurpm/poly-pmna-pdf-files/actions/runs/33709390600); the duplicate CROSS_REPO_SYNC_TOKEN run [failed](https://github.com/nandurpm/poly-pmna-pdf-files/actions/runs/33709390430) at its credential gate. The changes consolidate these into one workflow.

Other confirmed gaps: consumer sync scripts wrote manifest snapshots but workflows staged only the summary JSON; React download paths were hardcoded to v1; diploma-notes subject browsers used local PDF paths and stale availability flags; archive uploads had no catalog generation step.

Local tests cover numeric version selection (v10 over v2), removal/unpublication, invalid-file rejection, idempotence, byte-preserving migration, manifest-based links, PDF availability without HTML lessons, catalog search/pagination and network-failure UI.

## Remaining live verification

These changes are prepared for pull-request review. The 237-file migration and production upload-to-both-sites test have not run. They require merging the coordinated changes and successful GitHub Actions/deployments. Existing consumer copies are intentionally retained pending a separate historical-URL migration.

