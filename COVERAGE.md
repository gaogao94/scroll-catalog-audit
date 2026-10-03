# What was checked, over what, and what came back

Every row is metadata-only: no chunk bytes are downloaded anywhere in this repository. Scope counts
are what the row actually covered, not what it was hoped to cover. "Clean" rows are as much a result
as the findings are, and both are reproducible from the committed per-store data.

Snapshot: `metadata.min.json`, `Last-Modified 2026-09-29`, 894 declared Zarr roots (884 on
`s3://vesuvius-challenge-open-data`, 10 declaring `https://data.aws.ash2txt.org`).

## 1. Catalog layer

| check | scope | result | evidence |
|---|---:|---|---|
| every declared root resolves at its own declared access root | 894 | **894 / 894** | `results.jsonl`, `results_alt.jsonl` |
| roots carrying an OME metadata object | 894 | 14 carry none | `results.jsonl` |
| roots whose level 0 lists no chunks | 884 listable (the alternate root has no listing API) | **1** (#1892) | `results.jsonl` |
| declared store names that are republished under several paths | 224 names | 28 names, 2–81 paths each | `siblings` |
| bucket top-level prefixes accounted for | 46 prefixes | all accounted for; the 7 not in the manifest hold no Zarr | `FINDINGS.md` |

## 2. Physical scale (the main finding)

| check | scope | result | evidence |
|---|---:|---|---|
| stores with no `axes[].unit` at all | 894 | **124** | `results_levels.jsonl` |
| … of which state a micrometre pitch in their own name | 124 | **81** (76 raw CT, 4 surface volumes, 1 prediction) | `results.jsonl` |
| … of which state no pitch in the name | 124 | **43** (42 surface predictions, 1 ink-detection-3d) | `results.jsonl` |
| affected stores whose pitch is already in the manifest | 81 | **77** | `fixlist.json` |
| prediction stores that are unitless | 43 | **43 / 43** | `results.jsonl` |
| level-ladder defects (a level's scale not doubling the previous) | 894 | **0** | `FINDINGS.md` |
| shape/scale disagreements in the geometry probe | 231 probes | **0** | `GEOMETRY_PROBE.md` |

## 3. Array-header layer

| check | scope | result | evidence |
|---|---:|---|---|
| dtype is something other than uint8 | 894 | **0** | `results_zarray.jsonl` |
| non-zero `fill_value` | 894 | **0** | `results_zarray.jsonl` |
| chunk larger than its array shape | 894 | **0** | `results_zarray.jsonl` |
| v3 stores that are compressed | 81 | **81 / 81** | `results_zarray.jsonl` |
| v2 stores uncompressed / compressed | 813 | 763 / 50 | `results_zarray.jsonl` |
| level-0 uncompressed bytes (level 0 only) | 894 | 909 TB; 626 roots over 256 MB | `results_zarray.jsonl` |

The 909 TB corroborates the catalog-wide uncompressed-storage finding in
[#1950](https://github.com/ScrollPrize/villa/issues/1950) from a different tool; it covers **level 0
only**, so it is a subset of that issue's 1.03 PB figure, not a competing number.

## 4. Pyramid-level layer

| check | scope | result | evidence |
|---|---:|---|---|
| declared pyramid depth | 894 | all declare 6 levels | `results_levels.jsonl` |
| a declared level with no array header | 894 | **0** | `results_levels.jsonl` |
| declared level paths that are not `0..n-1` | 894 | **0** | `results_levels.jsonl` |
| declared depth versus depth actually probed | 107 | **0 disagreements** | `results_deep.jsonl` |
| header-only levels (volume roots) | 120 | **0** | `results_deep.jsonl` |
| header-only levels (segment surface volumes, seeded sample) | 60 | **0** | `results_deep_seg.jsonl` |
| levels that have a header but hold **no chunks** | 720 level entries over 120 roots | **0** | `results_level_chunks.jsonl` |

## 5. Manifest integrity

| check | scope | result | evidence |
|---|---:|---|---|
| `segment.original_volume_id` resolves in its own sample | 323 | **323 / 323** | `NEGATIVE_RESULTS.md` §3c |
| `volume.scan_id` resolves in its own sample | 73 | **73 / 73** | `NEGATIVE_RESULTS.md` §3c |
| declared `data_format` matches the published dtype | 73 | **73 / 73** | `NEGATIVE_RESULTS.md` §3c |
| `transforms` targets resolve / are invertible / are non-self | 28 | **0 dangling, 0 singular, 0 self** | `NEGATIVE_RESULTS.md` §3e |
| model `compatible_samples` resolve | 17 | **16 / 17** — one lists the string `"none"` (#1958) | `NEGATIVE_RESULTS.md` §3c |
| `metadata.min.json` vs `metadata.json` agree on paths and access roots | 894 | **894 / 894 identical** | `NEGATIVE_RESULTS.md` §3f |
| `volume_coverage.bbox_transformed` entries carrying the tifxyz `-1` marker as `-downscale` | 1,264 entries | **28**, all in `PHercParis4` (#1734) | `NEGATIVE_RESULTS.md` §3h |
| folder-name tokens versus `properties` (`pixel_size_um`) | 67 | **0 contradictions** | `NEGATIVE_RESULTS.md` §3b-ii |

## 6. Checks that were wrong first, and are recorded as such

A check that silently shrinks its own denominator is worse than no check, so the ones that did are
documented rather than quietly fixed.

| check | what went wrong | where |
|---|---|---|
| level existence | read `multiscales` from the top level of `zarr.json`, so all 81 v3 stores looked like they had no pyramid — a clean "0 failures" over a set that had shrunk to 813 | `NEGATIVE_RESULTS.md` §3d |
| chunk presence | counted `.zarray`/`.zattrs` keys as chunks, so the empty store in #1892 looked populated | `NEGATIVE_RESULTS.md` §3d |
| segment timeline (#1730) | compared *path* timestamps rather than `creation.date`, producing 255 instead of 20 — a different question entirely, caught before it was published | `ops/ledger.md`, cycle 39 |
| transformation matrices | assumed 4×4 and reported "28 malformed matrices"; they are 3×4, the usual affine form | `ops/ledger.md`, cycle 43 |
| unitless counts | read `datasets[].scale` directly, when OME-NGFF nests it under `coordinateTransformations` | `ops/ledger.md`, cycle 44 |

## 7. How to reproduce any row

```
python -m scroll_catalog_audit selftest      # 12 offline checks
python -m scroll_catalog_audit.asserts       # 9 structural assertions over the committed evidence
python -m scroll_catalog_audit demo          # reproduces two filed issues offline
python -m scroll_catalog_audit drift         # what the catalog declares now vs what was swept
```

CI regenerates every committed report from the committed per-store data and fails on any byte
difference, and re-runs the structural assertions, so no figure here can be hand-edited into being
true.
