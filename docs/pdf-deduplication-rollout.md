# PDF deduplication: draft, not safe to deploy yet

Baseline: archive commit 816e4beee57aaa879b811173dabd01bebc57fc77.

The draft removes 5,265 repeated SITTTR file paths, representing 813,118,559
uncompressed bytes. It retains all 4,351 distinct PDF Git blobs, including every
lesson PDF and every migrated legacy website PDF. No history is rewritten.
Git already shares identical blobs, so this is a working-tree reduction, not
an equivalent reduction in GitHub storage.

Every original catalogue row remains. Titles, departments, revisions, course
codes, checksums, sizes, publication status and source URLs are preserved.
The existing path field remains a logical catalogue identity; canonicalPath
identifies the retained file, and pdfUrl addresses that file directly.
Consumers must download pdfUrl, not concatenate a base URL and logical path.

manifests/pdf-aliases.json records each removed path, its retained target, Git
blob hash and byte size. This is a catalogue mapping, NOT an HTTP redirect.
The indexer verifies retained bytes and recreates all logical entries on each
publication; an absent or changed target stops publication.

## Verified before publication

- All 5,265 aliases resolve to the same original Git blob and size.
- The retained tree contains exactly the original set of 4,351 PDF blobs.
- All 9,616 archive catalogue entries remain.
- SITTTR manifest row counts and non-download metadata remain unchanged.
- Six regression tests pass, including corruption and missing-target rejection,
  path safety, alias reintroduction and repeat-index stability.

## Unresolved compatibility requirement

Do not merge this draft merely because repository checks pass.
GitHub raw hosting does not provide per-path redirects for removed files.
An old URL containing main and a removed path would return 404 after merging.
Updating a manifest cannot fix a saved URL or a cached, older website document.

The consumer data files assets/data/sitttr-archive-links.json,
assets/data/sitttr-pdf-links.json and assets/data/revision-2015-pdf-links.json
must be migrated first and their deployments verified. Both consumers also
contain local snapshots under docs/pdf-archive/manifests; those must be
refreshed. Check generated pages, service-worker caches, direct links, and
embedded viewers, including offline/revisited pages.

The 237 public website PDF URLs restored from docs/pdf-storage-map.json are
unaffected: that map points to an immutable archive commit and none of those
PDF contents is duplicated.

Even after current website links are migrated, arbitrary old GitHub raw URLs
cannot be preserved by this repository change. If preserving those URLs is
mandatory, retain their original paths on main. Do not substitute symlink
text or HTML redirects for PDF bytes.
