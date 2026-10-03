# Progress Prize submission — draft

> **Deadline to submit: 11:59pm Pacific, 2026-10-31.** Submission is via the form linked from
> `scrollprize.org/prizes#progress-prizes`. Open-sourcing on GitHub is required to accept a prize,
> and the docs state that tools released *early* in the month have a better chance of being used
> (community usage is one of the stated selection signals).

## Title

**scroll-catalog-audit — a read-only consistency audit of the open-data catalog: what the catalog
promises vs. what it serves**

## One-liner

A tool that sweeps every Zarr store in the open-data catalog using metadata only (~1,600 requests,
no chunk bytes) and enumerates the places where the published metadata silently disagrees with the
data a consumer receives — including physical scale, populated pyramid levels, path resolution per
access root, and level ladders.

## The problem, in one concrete case

The catalog publishes stores whose *names* state a physical pitch (`...-8.64um-1.2m-116keV-...zarr`)
while their OME metadata carries no `axes[].unit` and a level-0 `scale` of `[1,1,1]`. A reader that
takes the voxel size from metadata — the documented, expected path — silently gets `1`. Four such
surface volumes are already tracked in
[#1951](https://github.com/ScrollPrize/villa/issues/1951).

The audit shows this is not a four-store accident:

* **81 stores** state a µm pitch in their name while their metadata carries none.
* **76 of them are raw CT volumes** (`volumes/*-masked.zarr`) — the input to every downstream step.
* They span **39 samples**.
* Meanwhile 85.4 % of stores (755 of 884 S3 origins) *do* carry correct units, so the catalog is
  not uniformly unitless and a consumer cannot rely on either behaviour.
* The same sweep also found **1 store that declares six pyramid levels and contains no chunks at
  all** (header-only; reads back as `fill_value` with exit 0 — reproduces #1892 exactly) and
  **14 stores with no metadata object at all**.
* A **deep sweep of all 120 raw volumes** — every declared level probed for chunks — found **no
  header-only level**, so the empty-pyramid problem is confined to derived stores, not the primary
  data. No broken level ladders exist either (see negative results).
* Counts come from two independent sweeps merged per store (the run that obtained metadata wins),
  so a difference of a few stores between runs is transient-fetch noise, not a catalog change.

## What the tool does

`scan` → per-store JSONL; `report` → tables. Findings: `PATH_MISSING`, `NO_METADATA`,
`AXES_UNIT_MISSING`, `SCALE_IS_UNIT`, `EMPTY_PYRAMID` / `PARTIAL_LEVELS_MISSING` (with `--deep`),
`NON_MONOTONIC` / `NON_INTEGRAL_RATIO`, plus `LIST_ERROR` for retryable network failures. Every
origin is resolved against the root it declares (`via` in the JSONL), so the ten volumes published
on the alternate host are audited too rather than skipped.

## Community uptake so far

* **Independently reproduced by a second auditor.** The reporter of
  [#1951](https://github.com/ScrollPrize/villa/issues/1951) re-swept the 73 raw `ome-zarr` volumes
  with their own tooling and confirmed the three central claims — every resolvable raw volume carries
  no `axes[].unit` and `scale [1,1,1]`; the manifest holds the pitch for all of them; the four stores
  in that issue have eleven healthy siblings whose *metadata* (not payloads) should be copied. Their
  write-up: `thevibestack/vesuvius-catalog-audit`.

* The reporter of [#1892](https://github.com/ScrollPrize/villa/issues/1892) used this audit's bound
  ("exactly one of 894 roots has no chunks at level 0") and its remediation options to settle on a
  fix, and has said they will re-list the bucket's surface volumes once the manifest entry is
  dropped: *"Option (b) … is the change that stops a reader being handed fill_value. I will re-list
  the bucket's surface volumes after that entry is gone."* Their reply also corrected one of my two
  proposed options — the mesh sits outside the 1 µm POI scan, so re-rendering cannot fill it — which
  is recorded in the thread.
* A maintainer scoping note on [#1760](https://github.com/ScrollPrize/villa/issues/1760) states that
  data errors **in the open data bucket** are actionable while `dl.ash2txt.org` is not; every finding
  here is in that bucket, and the remediation plans are written for it.
* [Cross-check comment on #1727](https://github.com/ScrollPrize/villa/issues/1727#issuecomment-5970524776):
  a second audit's 1,260 `(segment, surface volume)` pairs all resolve to stores in this sweep, and
  the two defect classes were shown to be independent — so maintainers triaging both need not chase a
  shared root cause.

## Two traps the tool handles (and that produced false findings before they were handled)

1. **Access roots.** The catalog publishes some volumes twice, once on
   `s3://vesuvius-challenge-open-data` and once on `https://data.aws.ash2txt.org`. Resolving every
   path against the bucket manufactures 10 false "missing" hits; resolving each origin against its
   own declared root gives **0**.
2. **Chunk naming.** Chunk keys occur as `0/0/0/5` *and* as `0/0.0.11`. A digit-only matcher
   declares populated stores empty.

## Why it helps read the scrolls

The docs ask for analytic tools that *detect failure cases of existing methods on real scroll data*
and produce actionable information. A downstream reader that picks the wrong physical pitch, or an
empty pyramid level, or a path that only exists on one of the two roots, gets a silently wrong or
silently blank result — the same class of failure as a black strip that exits `0`. This tool makes
those cases enumerable and re-checkable after every catalog update (a weekly CI job is included),
so the set cannot quietly grow.

### And here is the code path that consumes it

The audit is not a metadata curiosity: three places in the repo read exactly the value that is
missing and substitute `1.0` without a word.

| Location | Behaviour |
|---|---|
| `lasagna/scripts/download_omezarr.py:449` | `_parse_multiscales()` initialises `scale = [1.0, 1.0, 1.0]` per level; a dataset without a `scale` transform is recorded unitless with no signal |
| `lasagna/scripts/download_omezarr.py:1165-1168, 1214-1216` | unreadable `.zattrs` → `zattrs = {}` → **every** level assigned `[1.0, 1.0, 1.0]`, then passed into the download scanner (`:1243`) |
| `lasagna/scripts/zarr_threshold_masks.py:135` | `_infer_zyx_scale()` falls back to `1.0, 1.0, 1.0` when neither preprocess params nor OME parent metadata carry a scale |

Nothing distinguishes "unitless store" from "1 µm per voxel"; downstream offsets and distances are
then wrong by the ratio of the real pitch (8.64× for the PHerc1447 8.64 µm set).

**A patch for these three sites is included with this submission** (`lasagna-scale-fallback.patch`,
2 files, +39/−2, `git apply --check` verified): a single `WARN … assuming 1.0 per voxel` naming the
affected levels, plus an opt-in `--require-scale` flag that turns it into a hard error. Default
behaviour is unchanged.

It also records a **negative result**: no broken level ladders exist catalog-wide, and the
z-axis/in-plane asymmetry of surface volumes is uniform — so future audits do not have to re-file it.

## Evidence / reproducibility

* `python -m scroll_catalog_audit scan --workers 10` — full catalog, metadata only, resumable.
* `python -m scroll_catalog_audit selftest` — 12 offline unit checks over the parsing and
  classification logic (no network).
* `python -m scroll_catalog_audit explain --path <store>` — prints the raw evidence behind any
  single finding (pitch in the name, axis units, level-0 scale, chunks on the first page, derived
  labels), so a reviewer can spot-check a claim in one command.
* `results.jsonl` (per-store) and `FINDINGS.md` (tables + per-sample summary + negative results)
  are committed with the run that produced the numbers above; `fixlist.json` carries the
  per-class remediation list. Catalog snapshot date recorded in the README.
* The tool was calibrated against two already-confirmed cases before the full sweep — the
  empty-pyramid store from [#1892](https://github.com/ScrollPrize/villa/issues/1892) and the four
  volumes from #1951 — reproducing both exactly.

## Links

* Repository: `<to be published>`
* Findings: `FINDINGS.md`
* Related issues: #1951 (addendum with the catalog-wide numbers), #1892 (reproduced)

## Status / limits (stated up front)

Metadata only; says nothing about data content. Reports, never modifies. Chunk presence is judged
from the first listing page unless `--deep` is used. Transient failures are labelled `LIST_ERROR`
and are meant to be re-run.
