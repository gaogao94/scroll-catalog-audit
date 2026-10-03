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
| array `order` other than C | 894 roots | **0** — 813 v2 stores say `"C"` and the 81 v3 stores omit the field, which v3 removed; no store is column-major, so no reader can walk one the wrong way |
| unexpected `filters` | 894 roots | **0** — 813 v2 stores carry `[]`, the 81 v3 stores carry `["sharding_indexed"]`, the standard v3 sharding codec rather than a surprise |

`order` and `filters` were collected by the first sweep and reported for the first time here. Both fail
*silently* when wrong: a column-major store, or one carrying a codec the reader has not implemented,
shows a perfectly ordinary shape and dtype. Neither occurs in the catalog.

One detail that is not a defect but matters when comparing two stores: `fill_value` is written as the
integer `0` in 809 stores and as the float `0.0` in 85 - all numerically zero. Compare fill values
numerically rather than by repr.

Header format splits the corpus cleanly: **all 81 v3 stores are compressed and all are predictions**
(`sharding_indexed` for ink predictions, blosc for surface predictions), while the v2 stores are 763
uncompressed / 50 compressed. So "the catalog stores uncompressed" is true of the v2-era stores and
false of anything published through the v3 path.

## 3b-ii. Folder-name tokens versus `properties`

Volume folder names encode three physical parameters (`<pitch>um-<distance>m-<energy>keV`). Compared
against the manifest's own `properties` for the 67 volume origins whose names carry all three:

| parameter | contradictions | explanation |
|---|---:|---|
| `pixel_size_um` | **0 / 67** | exact match everywhere |
| `energy_keV` | 0 real | one name rounds 65.35 to `65keV` |
| `detector_distance_mm` | 0 real | 28 names round 220 mm to `0.2m` |

So the name is a rounded label and the manifest is the precise record; where they differ the manifest
is the finer value. This matters for repair planning: a fix should copy from `properties`, never parse
the folder name.

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

## 3d. Declared pyramid levels versus what exists - all 894 roots

Extended from the 180-store sample to the whole catalog, reading `multiscales` from `.zattrs` (v2)
and from `attributes.multiscales` (v3), then fetching the header of each store's **last** declared
level:

| check | scope | result |
|---|---:|---|
| every store declares the same pyramid depth | 894 | all declare 6 levels |
| the last declared level has a header | 894 | **0 failures** |
| declared level paths are contiguous from 0 | 894 | **0 failures** |
| declared depth agrees with the level count actually probed | 107 | **0 disagreements** |

v3 stores carry a different axes set (`y, x` with a canvas size) than v2 stores (`z, y, x`), which is
expected for canvas-based predictions but is why a reader that only looks at `.zattrs` sees nothing
for them.

**A note on how this check nearly went wrong.** The first pass read `multiscales` from the top level of
`zarr.json` and therefore classified all 81 v3 stores as having no pyramid metadata at all - a clean
"0 failures" over a set that had silently shrunk to 813. The corrected parser reads
`attributes.multiscales`, and the run above is the corrected one.

### How the unitless stores partition

The two published figures are complementary, not overlapping:

| group | count |
|---|---:|
| state a micrometre pitch **in the name**, no `axes[].unit` | 81 (76 raw CT, 4 surface volumes, 1 prediction) |
| no pitch in the name and no unit either | 43 (42 surface predictions, 1 ink-detection-3d) |
| **total stores with no `axes[].unit`** | **124** |

## 3e. Coordinate transforms

The manifest records 28 `transforms` entries across 73 volumes, each a 3x4 affine matrix naming a
`to_volume_id`. All 28: the target volume exists, the left 3x3 block is invertible (smallest absolute
determinant 0.013, largest 197), and none names its own volume. No transform has a recorded reverse,
which fits a one-way "registered to" relation and is not a defect given every matrix is invertible.

## 3f. The two published catalog files agree

The bucket publishes `metadata.min.json` (67 KB) and `metadata.json` (1.4 MB gzipped). Compared
origin by origin: **894 / 894 Zarr roots in both, with an identical set of declared access roots for
each**. The compact file is a strict subset in fields, not in paths, so a consumer reading either one
is sent to the same place. The `models` section exists only in the full file.

## 3g. The two access roots use different path conventions

Ten origins declare `https://data.aws.ash2txt.org` as their only access root. Each was requested under
both spellings - the manifest's `samples/<sample>/volumes/...` and the unprefixed
`<sample>/volumes/...`:

| origins | S3, unprefixed | S3, `samples/`-prefixed | alternate root |
|---|---:|---:|---:|
| 7 | 404 | 404 | 200 |
| 3 | **200** | 404 | 200 |

So seven catalog volumes really are absent from the S3 bucket (filed as #1949), and the other three are
present on S3 only under the **unprefixed** path: the alternate root serves `samples/<sample>/...` and
the bucket serves `<sample>/...`, while the manifest records the alternate-root spelling.

This matters because a completeness check that requests the declared path verbatim against S3 reports
ten missing, of which three are false positives. Any such check must try both spellings, which is also
why this sweep resolves every origin against its own declared access root rather than against S3.

## 3h. Where the tifxyz missing-point marker reaches a derived bounding box

28 of the 29 PHercParis4 `w###` segments published 2026-07-01 carry a `meta.json` bbox whose lower
corner is the tifxyz `-1` marker (#1618). In the catalog, `volume_coverage[<volume>].bbox_transformed`
for exactly those segments carries a coordinate equal to **`-original_volume_downscale`** - which is
`-4.0` on all three axes, since the downscale is 4 - so a consumer checking for `-1` receives `-4`
(#1734).

Bounded catalog-wide: of the 1,264 `bbox_transformed` entries, **28 carry this value and all 28 are in
`PHercParis4`**. The 544 entries that contain *some* negative coordinate are a different thing (mostly
`PHerc0500P2`, `PHerc0139`, `PHerc1667`) and are not this marker; 24 of the 323 segments carry
`volume_coverage: null` rather than a dict, which is a third shape.

## 3d-ii. Every level of every root holds data, not only a header

`3d` asked whether each declared level has an array **header**. A header can exist with no chunks behind
it - that is exactly #1892, and a reader gets fill_value with no error. So every declared level of
**every root** was listed directly and its chunk objects counted: 884 roots, 6 levels each, **5,304
level listings, 5,304 successful, 0 failures** (7 transient failures on the first pass were re-probed).

| check | scope | result |
|---|---:|---|
| levels with a header but **no** chunk objects | 5,304 | **6** - all six levels of one store (#1892) |
| stores involved | 884 | **1** |

Chunk counts fall with depth as a pyramid should (median 999, 999, 525, 142, 39, 12 from level 0 to 5).
1,766 of the listings are truncated at the API's 1000-key page, so a count of 999 means "at least 999";
that does not affect the presence check, which is what this section reports.

With #1892 the single such store in the catalog, the class is bounded at one store - and that is now a
whole-catalog statement rather than a 120-root sample.

## 3d-iii. Two tempting ways to detect missing data that do not work here

Chunk *counts* look like they should reveal a store that lost data. Both obvious tests were tried and
both are invalid in this catalog, which is worth writing down so nobody spends a day on them:

| candidate test | why it fails |
|---|---|
| a level's chunks are fewer than its declared shape implies | surface volumes are an irregular mesh inside an axis-aligned box, so empty chunks are the norm. Every one of the 20 comparable level-0 arrays was below its shape-implied count (43/64, 845/1400, 369/570, ...) |
| a store name republished under several paths has fewer chunks in one copy | copies under different segments render **different surface regions**, so their occupancy legitimately differs. 42 of 61 comparable (group, level) pairs differ by more than 2x |

What *is* usable is presence, not count: a level with a header and no chunks at all (#1892) is
detectable and is the only such store. One trap inside that check too - a listing is capped at 1000
keys, and the cap shows up as 999 chunks rather than 1000, so a truncated listing compared against a
complete one invents a difference.

## 3d-iv. A chunk-count deficit is not missing data

The obvious way to find missing data is to compare the number of chunk objects in a level against the
number its own `shape` and `chunks` imply. For 155 stores the level-0 listing is short enough to count
exactly (the other 739 are truncated at the 1000-key page), and **154 of those 155 hold fewer chunks
than the grid implies**:

| ratio actual / implied | stores |
|---|---:|
| 1.000 | 1 |
| 0.5 - 0.99 | 134 |
| below 0.5 | 20 |

Median **0.663**, minimum 0.000 - and the minimum is #1892, the store this repository already reports as
empty, which is the one case where the deficit is real.

Zarr permits a chunk object to be absent; a reader gets `fill_value` for it, and every store here fills
with `0`. Surface volumes are mostly empty by construction, so their writers skip the all-zero chunks
and the deficit is the normal state rather than a fault. Verified by listing one store independently of
the probe: S3 returns 43 keys / 42 chunk objects at level 0, exactly what `results_level_chunks.jsonl`
records, so the counts are right and the gap is real sparsity.

Two consequences worth carrying: the ratio is not a health signal, and any "stored bytes" figure
derived from `shape x dtype` is a *logical* size - the number of materialised objects is lower, here by
about a third at the median.

## 3i. A volume and the scan it belongs to agree on the physical parameters

Every volume names a `scan_id`, and both sides carry `pixel_size_um`, `energy_keV` and
`detector_distance_mm` - the volume in `properties`, the scan in `properties` **and** in
`creation.metadata`. Compared for all 73 volumes against both scan-side copies: **0 disagreements**,
and no volume lacks a scan entry.

## 3j. Provenance is recorded for most artifacts, and two caveats inside it

`creation_info.provenance` is present on **3,839 of 4,419 `data` entries (87%)**, carrying the workflow
template, infra revision, atlas version and sha, container images and the full parameter set. Auditing
it turned up two things (filed as #1959) and one class that is *not* a problem:

| finding | scope | detail |
|---|---|---|
| `atlas_git_dirty` is `true` | 3,834 of 3,834 records that have it | so the recorded `atlas_git_sha` does not identify the code that ran, for any artifact |
| `parameters.output-path` disagrees with the artifact's own origin | 1 of 2,500 comparable | a stride-82 run recorded against a published stride-128 file |
| `output-path` differs from the origin only by the prefix a step adds to its output name | 30 of 2,500 | **benign**, recorded here so it is not re-derived as a defect |

And two things inside those blocks that do agree, everywhere they can be compared:

| check | scope | result |
|---|---:|---|
| the commit hash inside a container image tag versus `parameters.commit` | 2,365 records | **0 disagreements** |
| `volume.properties` versus its scan's `properties` **and** `creation.metadata` | 73 volumes x 3 parameters x 2 sources | **0 disagreements** |

`atlas_git_sha` and the sha inside `infra_revision` never coincide (0 of 3,834) - they appear to name
different repositories, so that is recorded here only to stop it being read as a defect later.

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
