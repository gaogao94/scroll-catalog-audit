# scroll-catalog-audit

**A read-only consistency audit for the Vesuvius Challenge open-data catalog.**

Every store the catalog publishes is checked for the things a *consumer* has to trust before
downloading anything: does the path resolve on the root it declares, are the declared pyramid
levels actually populated, does the metadata carry the physical pixel size the store name
promises, and is the level ladder well formed.

No chunk bytes are ever downloaded — only `ListObjectsV2` listings and small metadata objects
(`.zattrs`, `.zarray`, `zarr.json`). A full sweep of the catalog (≈900 stores) costs about
1,600 requests and 15 minutes on one machine.

## Why

The catalog is published as OME-Zarr stores produced by many different pipelines over several
years. They are not formatted uniformly, and the differences are silent: a reader that takes the
physical voxel size from OME metadata gets `unit: null` / `scale: [1, 1, 1]` for a store whose
own name says `8.64um`, and nothing in the download path raises an error.

This tool exists to turn those silent differences into an enumerated, reproducible list — and to
be run again after every catalog update so the list cannot quietly grow.

**The consuming code path makes this concrete.** Three places in this repository read exactly the
value that is missing and substitute `1.0` without warning:

* `lasagna/scripts/download_omezarr.py:449` — per-level default in `_parse_multiscales()`
* `lasagna/scripts/download_omezarr.py:1165-1168, 1214-1216` — unreadable `.zattrs` → every level
  assigned `[1.0, 1.0, 1.0]`, then used by the download scanner
* `lasagna/scripts/zarr_threshold_masks.py:135` — final fallback in `_infer_zyx_scale()`

A patch that turns those three silent defaults into a warning (plus an opt-in `--require-scale`)
is attached to the accompanying submission.

## Install & run

Standard library only. Python 3.9+.

```bash
# 1. audit every zarr root in the catalog (resumable; safe to interrupt)
python -m scroll_catalog_audit scan --workers 10 --results results.jsonl

# 2. turn the JSONL into a human-readable report plus a machine-readable fix list
python -m scroll_catalog_audit report --results results.jsonl --out FINDINGS.md --fixlist fixlist.json

# 3. offline unit checks (no network)
python -m scroll_catalog_audit selftest

# 4. show every stored field and the derived labels for one store (reviewer spot-check)
python -m scroll_catalog_audit explain --path PHerc1447/segments/20250702235910

# 5. stores that share a name — one volume republished under many segment directories
python -m scroll_catalog_audit siblings --path 8.64um-1.2m-116keV-volume-20250521151220
python -m scroll_catalog_audit siblings          # catalog-wide: how many affected stores have a correct sibling?
```

`explain` prints the raw evidence behind a finding — pitch in the store name, whether the axes
carry a unit, the level-0 scale, how many chunks the first listing page holds, and the labels that
follow from those fields — so a claim can be checked without reading the JSONL.

`report` writes two artifacts: `FINDINGS.md` (per-class tables, a per-sample summary, and an explicit
**negative results** section) and `fixlist.json` (each finding class with a recommended remediation
and the affected store paths, so a maintainer can script the fix).

Useful flags: `--limit N` for a smoke run, `--kind volume:` to restrict the sweep to one family
(e.g. raw volumes only), `--random N --seed S` for a reproducible random sample, `--deep` to probe
each declared level for chunks (slower), `--catalog local.json` to audit a pinned catalog snapshot.

## What it reports

| Finding | Meaning |
|---|---|
| `PATH_MISSING` | the store's prefix returns zero keys on the access root **it declares** |
| `LIST_ERROR` | the listing request failed (network/rate limit) — retryable, *not* a missing path |
| `NO_METADATA` | store has chunks but neither `.zattrs` nor `zarr.json` |
| `AXES_UNIT_MISSING` | `axes` entries carry no `unit` while the store name states a µm pitch |
| `SCALE_IS_UNIT` | level-0 `scale` is `[1,1,1]` while the store name states a µm pitch |
| `SCALE_UNITLESS_NO_NAME_UM` | unitless `scale` with no µm in the name (informational) |
| `EMPTY_PYRAMID` | every declared level exists as a header but contains no chunks (`--deep`) |
| `PARTIAL_LEVELS_MISSING` | some declared levels contain no chunks — a reader that picks a coarser level silently gets `fill_value` (`--deep`) |
| `NON_MONOTONIC` / `NON_INTEGRAL_RATIO` | the per-level scale ladder is broken |
| `ALT_HOST_ORIGIN` | the origin declares a non-S3 access root, so this run skipped it (by design) |

Two details that are easy to get wrong, and that this tool handles:

* **Access roots matter.** The catalog publishes some volumes twice — once on
  `s3://vesuvius-challenge-open-data` and once on `https://data.aws.ash2txt.org`. Resolving every
  path against one bucket produces false "missing" hits. Each origin is resolved against its own
  declared root.
* **Two chunk naming styles exist.** Hierarchical `0/0/0/5` *and* dotted `0/0.0.11`. A
  digit-only matcher declares populated stores empty.

## Results (catalog snapshot 2026-10-03)

Generated by `report`; the raw per-store output is `results.jsonl`, and `fixlist.json` carries the
per-class remediation list.

* **894** zarr roots published by the catalog (884 with an S3 access root); **755 (85.4 %)** carry
  full physical units.
* **71 stores** state a µm pitch in the store name while their OME metadata carries none — **66 of
  them raw CT volumes** (`volumes/*-masked.zarr`), 4 surface volumes, 1 surface prediction — across
  **39 samples**. This is the class tracked for four PHerc1447 volumes in
  [#1951](https://github.com/ScrollPrize/villa/issues/1951).
* **1 store** declares six pyramid levels and contains no chunks at all (reproduces
  [#1892](https://github.com/ScrollPrize/villa/issues/1892) exactly), and **14 stores** carry no
  metadata object at all.
* **Header-only levels are rare.** Level 0 was checked on **every** root (894) and exactly one store
  has no chunks there. A deep sweep then probed *every declared level* on all **120 raw volumes**
  and on a reproducible random sample of **60 segment surface volumes** (8.7 % of that family,
  `--random 60 --seed 20261003`) — **no header-only level in either**. With 0 hits in 60 draws, the
  segment family's rate is bounded at <5 % (95 %, rule of three), so this is a bound rather than
  proof of absence; the one known case is a segment store, so the class is real but rare.
* **No broken level ladders** were found. The z-axis/in-plane asymmetry of surface volumes
  (`[8.64, 8.64, 8.64] → [8.64, 17.28, 17.28]`) is uniform across the catalog and is therefore
  reported as **expected**, not as a defect.
* **894 roots resolve to only 224 distinct store names**: 28 names are republished under 2–81 segment
  directories, so 78 % of the roots are repeat publications. That matters for #1951: the store
  `8.64um-1.2m-116keV-volume-20250521151220.zarr` exists **15 times**, and **11 copies declare the
  8.64 µm scale while the other 4 declare none** — the correct metadata is already in the catalog.
  (`siblings --path <name>` lists them.) Do not generalise the shortcut: of all 71 affected stores
  only these 4 have a correct sibling; the other 67 are single-copy raw CT volumes.
* **The catalog already knows the missing pitch.** For **67 of the 71** affected stores the manifest
  entry carries `properties.pixel_size_um`, and it matches the µm token in the store name exactly
  (verified per store against `metadata.min.json`). The information is therefore not lost — it is
  recorded at manifest level and not propagated into the OME metadata of the store, which is why a
  reader that follows OME-Zarr sees `1.0`. The remaining 4 (the #1951 surface volumes) have it in
  neither. Filed as <https://github.com/ScrollPrize/villa/issues/1957>.
* **Coverage self-check.** The manifest declares zarr-typed data for exactly 894 origins and the
  sweep covers 894 roots; **0 zarr-typed origins are missing from the results** and **0 scanned
  paths are absent from the manifest**, so "every Zarr root the catalog publishes" is verified
  rather than asserted.
* **Every published prediction output is unitless.** All **43** `volume:surface-prediction-zarr`
  stores — the `representations/predictions/surfaces/` family, spanning 36 samples — declare
  level-0 `scale = [1.0, 1.0, 1.0]` and none carries `axes[].unit`. Each `.zattrs` was re-fetched
  directly from the bucket to confirm (42 confirmed, 1 transient failure). For a *surface* this is
  not cosmetic: flattening and measurement code that trusts the metadata gets 1.0 for all of them.
* **The affected stores do not cluster by date.** They span 2024-10 … 2026-06 with clean months in
  between, so a pipeline-regression window is ruled out; the pattern is per-sample/per-store.
* **`demo`** runs the offline self-test, reproduces both filed issues, and prints these numbers in
  one command: `python -m scroll_catalog_audit demo --merge results_deep.jsonl`.

**Method note.** The numbers above come from two independent sweeps merged with
`report --merge`: per store, the run that actually obtained metadata wins. Without the merge a
handful of stores move between classes purely because of transient fetch failures (the tool labels
those `LIST_ERROR` / `META_ERROR` and they are re-run rather than reported), so treat a difference of
a few stores between runs as noise, not as a catalog change.

See `FINDINGS.md` for the enumerated list, the per-sample summary, and the negative results.

## Scope and limits

* Metadata only. This tool says nothing about data *content*, only about what the catalog
  promises versus what it serves.
* It reports findings; it does not modify anything. Fixes are catalog-side decisions.
* Transient failures are labelled `LIST_ERROR` and are meant to be re-run, not reported.
* Chunk presence is judged from the first listing page unless `--deep` is used.

## License

MIT — see `LICENSE`.
