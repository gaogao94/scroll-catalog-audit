# Vesuvius open-data catalog · consistency audit

- stores scanned: **60** (S3 origins 60, other roots 0)
- stores with full physical units: **60**
- findings: none

## Negative results (checked, nothing found)

- Level ladders: **60** stores had parseable multiscale metadata and **none** showed a non-monotonic or non-integral level ladder.
- The z-axis/in-plane asymmetry of surface volumes (`[8.64, 8.64, 8.64] → [8.64, 17.28, 17.28] → …`) is uniform across the catalog and is recorded here as **expected**, not as a defect, so future audits do not re-file it.
- Origins that declare a non-S3 access root are skipped by design rather than reported missing (see `ALT_HOST_ORIGIN` in the JSONL).
