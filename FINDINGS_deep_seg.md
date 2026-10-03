# Vesuvius open-data catalog · consistency audit

- stores scanned: **60** (resolved on the S3 bucket: 60; on a declared alternate root: 0)
- stores with full physical units: **60**
- findings: none

## Negative results (checked, nothing found)

- Level ladders: **60** stores had parseable multiscale metadata and **none** showed a non-monotonic or non-integral level ladder.
- The z-axis/in-plane asymmetry of surface volumes (`[8.64, 8.64, 8.64] → [8.64, 17.28, 17.28] → …`) is uniform across the catalog and is recorded here as **expected**, not as a defect, so future audits do not re-file it.
- Origins that declare a non-S3 access root are resolved against that root (see `via` in the JSONL); on such hosts there is no ListObjectsV2 API, so existence is established from the metadata object and the chunk-page fields stay unknown.
