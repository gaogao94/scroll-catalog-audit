# Negative results — what was checked and found clean

A sweep that only reports hits is hard to trust and easy to duplicate. This file records the checks
that came back **clean**, with the scope each one actually covered, so the next person does not have
to repeat them — and so the limits of the positive findings are visible.

Catalog snapshot: **2026-10-03**, 894 Zarr roots declared by `metadata.min.json`.

Every check below is reproduced by `python -m scroll_catalog_audit …` on the data committed in this
repository; no network access is needed to re-derive the numbers.

---

## 1. Empty pyramid levels

| check | scope | result |
|---|---|---|
| level 0 has no chunks | **every root** (894) | exactly **1** store — the one in [#1892](https://github.com/ScrollPrize/villa/issues/1892) |
| every *declared* level has chunks | 120 volume roots (all of them) | **0** header-only levels |
| every *declared* level has chunks | 60 segment surface volumes (`--random 60 --seed 20261003`, 8.7 % of that family) | **0** header-only levels |

The class is real (one instance is filed) but rare. For the segment family, 0 hits in 60 draws
bounds the rate at <5 % (95 %, rule of three) rather than proving absence.

## 2. Level ladders

| check | scope | result |
|---|---|---|
| non-monotonic ladder | 794 roots with parseable multiscale metadata | **0** |
| non-integral level ratio | same | **0** |

The surface volumes are *systematically* anisotropic — z keeps the base pitch while the in-plane
axes double per level (`[8.64, 8.64, 8.64] → [8.64, 17.28, 17.28] → …`). That is uniform across the
catalog and consistent with z being the through-sheet sampling axis, so it is **expected**, not a
defect. Flagging it here so it is not re-filed as one.

## 3. Shape versus declared scale

A level whose array shape contradicts its own `scale` transform makes every reader that selects a
level by scale compute coordinates off by the level ratio — silently.

| check | scope | result |
|---|---|---|
| `shape_i ≈ shape_0 / (scale_i / scale_0)`, tolerance `max(1 voxel, 1 %)` | 120 volume roots | **0** mismatches |
| same | the 81 stores carrying the units defect | **0** mismatches |
| same | 30 segment surface volumes | **0** mismatches |

231 store-probes, 0 mismatches. One store initially reported `INCOMPLETE`; re-checking it directly
showed `0/.zarray` present (HTTP 200) with 297 chunk keys on the first page — a transient fetch
failure, not a defect. Details in `GEOMETRY_PROBE.md`.

## 3b. Array headers (`.zarray` / `zarr.json`, level 0 of every root)

| check | scope | result |
|---|---|---|
| non-zero `fill_value` | 894 roots | **0** — every store fills with `0`, so blank regions cannot read as bright and be mistaken for ink |
| chunk shape larger than the array shape | 894 roots | **0** |
| dtype outside uint8 | 894 roots | **0** (`\|u1` in v2, `uint8` in v3 — same type, different notation) |

Header format splits the corpus cleanly: **all 81 v3 stores are compressed and all are predictions**
(`sharding_indexed` for ink predictions, blosc for surface predictions), while the v2 stores are 763
uncompressed / 50 compressed. So "the catalog stores uncompressed" is true of the v2-era stores and
false of anything published through the v3 path.

## 3c. Referential integrity inside the full `metadata.json`

The catalog publishes two files: `metadata.min.json` (67 KB, paths and physical properties) and
`metadata.json` (1.4 MB gzipped, adds `creation.date`, `original_volume_id`, `properties.shape`,
`data_format`, `volume_coverage`, and a `models` section). Checks below are on the **full** file.

| reference | resolved |
|---|---:|
| `segment.original_volume_id` -> volume in the same sample | **323 / 323** |
| `volume.scan_id` -> scan in the same sample | **73 / 73** |
| `volume.properties.data_format` -> dtype of the published level 0 | **73 / 73** (all declare `uint8`, all are uint8) |
| model `compatible_samples` -> sample | 16 / 17 — one entry lists the string `"none"` (filed as #1958) |

All 13 model entries carry `data: []`, i.e. no origin. Whether that is deliberate (weights published
off-catalog) is unknown to me and is asked as a question in #1958 rather than reported as a defect.

## 4. Path resolution

| check | scope | result |
|---|---|---|
| declared path does not resolve | 894 roots, each against **its own** declared access root | **0** |
| zarr-typed origin missing from the sweep | manifest vs results | **0** |
| scanned path absent from the manifest | results vs manifest | **0** |

Resolving every path against the S3 bucket alone manufactures **10** false "missing path" hits;
those ten are published on `data.aws.ash2txt.org` and are now audited there.

## 5. Manifest internal consistency

| check | scope | result |
|---|---|---|
| volume references a scan that does not exist | 73 volumes / 67 scans | **0** dangling |
| `volume.properties.pixel_size_um` disagrees with its source scan | 73 volumes | **0** |
| volume without a licence field | 73 volumes | **0** (66 × CC BY-NC 4.0, 7 × EduceLab) |

The manifest is clean; the problem described in
[#1957](https://github.com/ScrollPrize/villa/issues/1957) is that its values are not *propagated*
into the published OME metadata, not that they are wrong.

## 6. Duplicate publications

| check | scope | result |
|---|---|---|
| same store name published under several paths | 894 roots → 224 distinct names; 28 names under 2–81 paths | expected catalog structure |
| copies of a name disagree on **metadata** | 28 names | 1 name disagrees — the four stores in [#1951](https://github.com/ScrollPrize/villa/issues/1951), whose eleven sibling copies carry the correct scale |

## 7. Candidate causes ruled out

| hypothesis | how it was tested | result |
|---|---|---|
| the units defect is a pipeline regression in a date window | rendered-month distribution of the 81 affected stores vs the whole catalog | **rejected** — affected stores span 2024-10 → 2026-06 with clean months in between (2025-09: 135 stores, none affected) |
| the units defect explains [#1727](https://github.com/ScrollPrize/villa/issues/1727)'s non-reproducible renders | cross-tabulated ge-al's `match_renderer` against this audit's unitless flag | **rejected** — only 4 of 1,113 non-reproducible entries are unitless, so the two classes are independent |
| a second access root hosts different data | all 10 alternate-root stores fetched from their own root | **no** — same pattern (no unit, `scale [1,1,1]`), 7 of them published *only* there |

## 8. Coverage

| check | scope | result |
|---|---|---|
| top-level prefixes of the bucket | 46 prefixes | 39 covered by the sweep; the other 7 contain **no Zarr data at all** (six hold only `photos/`, one is a thumbnail cache) |

So the 894 roots are all the Zarr in `vesuvius-challenge-open-data`. **Not covered:** the stores on
`dl.ash2txt.org` (a different host, e.g. [#1755](https://github.com/ScrollPrize/villa/issues/1755)).

---

## Reproducing

```
python -m scroll_catalog_audit selftest
python -m scroll_catalog_audit demo                    # offline: self-test + both filed issues + counts
python -m scroll_catalog_audit siblings                # the duplicate-publication structure
python -m scroll_catalog_audit explain --path <store>  # raw fields behind any single finding
```

`ops/probe_geometry.py` in the working repository regenerates section 3 (it is a prototype and is
not part of the published package).
