# Progress Prize submission #2 — draft

> **Same deadline: 11:59pm Pacific, 2026-10-31.** The prize rules allow multiple submissions per
> month. This is a deliberately separate entry from `SUBMISSION.md`: that one is the catalog audit
> **tool**; this one is the **fix** it motivated. Submit together or separately — see the note at
> the bottom.

## Title

**Stop three silent `1.0` fallbacks for missing physical scale (and make the absence representable)**

## One-liner

Three places in the pipeline read a physical voxel size that may simply be absent, and substitute
`1.0` per voxel with no warning; a patch makes the absence visible (a single `WARN` naming the
affected levels) and adds an opt-in `--require-scale` that fails instead of proceeding unitless.

## Why this is not hypothetical

A metadata-only sweep of the catalog (`scroll-catalog-audit`, companion submission) found **71
stores that state a µm pitch in their own name while their OME metadata carries no `scale`** — 76
of them raw CT volumes, across 39 samples. Four surface volumes of this kind are already tracked in
[#1951](https://github.com/ScrollPrize/villa/issues/1951).

Then we looked at what consumes that value:

| Location | Behaviour today |
|---|---|
| `lasagna/scripts/download_omezarr.py:449` | `_parse_multiscales()` initialises `scale = [1.0, 1.0, 1.0]` per level and only overwrites it if the dataset carries a `scale` transform — a level without one is recorded as unitless, silently |
| `lasagna/scripts/download_omezarr.py:1165-1168, 1214-1216` | if `.zattrs` cannot be read, `zattrs = {}` and **every** level is assigned `[1.0, 1.0, 1.0]`; that map is then passed into the download scanner (`:1243`) |
| `lasagna/scripts/zarr_threshold_masks.py:135` | `_infer_zyx_scale()` falls back to `1.0, 1.0, 1.0` when neither preprocess params nor parent OME metadata carry a scale |

Nothing distinguishes "this store is unitless" from "this store is 1 µm per voxel". Downstream
offsets and distances are then wrong by the ratio of the real pitch — 8.64× for the PHerc1447
8.64 µm set. This is the same class of failure as #1660 (an all-black render that exits `0`), one
layer earlier.

## What the patch changes

* `_parse_multiscales(zattrs, missing=None)` records which levels had no `scale` transform.
* One `WARN: no physical scale in OME metadata for level(s) [...] of <prefix>; assuming 1.0 per
  voxel` per run, naming the levels and the prefix.
* New opt-in flag **`--require-scale`** turns it into a hard error (`exit 1`) for pipelines that
  would rather stop than proceed unitless.
* `zarr_threshold_masks.py` prints the same warning when it falls back.
* Two tests in the repository's existing style, plus a new test file guarded with
  `pytest.importorskip`.

**Backward compatible by construction**: the returned map is byte-identical to before, the
single-argument call still works, and the warning goes to stderr. Verified by executing both
versions on the same input:

```
BEFORE  _parse_multiscales(zattrs) -> {0: [8.64,8.64,8.64], 1: [1.0,1.0,1.0], 2: [1.0,1.0,1.0]}
        stderr -> ''                      # nothing distinguishes a real level from a missing one
AFTER   _parse_multiscales(zattrs, missing) -> same map,  missing -> {1, 2}
```

## Evidence / reproducibility

* Patch: 4 files, **+111/−2**; `git apply --check` against current `main` → **OK**.
  (`download_omezarr.py`, `zarr_threshold_masks.py`, two test files.)
* Base verified against upstream: the three touched files hash-identical to `origin/main`
  (`5a4388f`) at the time of writing, so the patch is not stale.
* Both modified files compile (`python -m py_compile`).
* The two new tests in `test_download_omezarr.py` were executed with a minimal pytest shim in an
  environment without pytest/heavy deps → **PASS**. The `zarr_threshold_masks` test skips there
  (internal extension modules absent) and will run in CI.
* The catalog side that motivates the patch is reproducible with the companion tool:
  `python -m scroll_catalog_audit scan` then `report`, or
  `python -m scroll_catalog_audit explain --path <store>` for a single store.

## Links

* Patch: `<to be published>` · Tool: `<to be published>`
* Related: [#1951](https://github.com/ScrollPrize/villa/issues/1951) (the four volumes),
  [#1660](https://github.com/ScrollPrize/villa/issues/1660) (same failure class, different layer)

## Limits (stated up front)

The three sites are what the patch fixes. The same repo-wide search also found **four more
candidates of the same class**, listed with `file:line` in the issue draft so the search does not
have to be repeated: a second default one function downstream in the same file, a missing-key
default for TIFXYZ `meta.json` (where a malformed scale already raises), an initialised-then-maybe-
overwritten scale in the label-transfer module, and — the most interesting — a writer in
`spiral-fitting/tracks_to_ome_zarr.py` that will **write** 1.0 into newly produced OME-Zarr metadata
when no voxel size is available. That last one can manufacture the very pattern the companion audit
enumerates, so it is the natural next fix.

The fix makes the fallback *visible*; it does not repair the catalog metadata itself (that is a
catalog-side change, and `fixlist.json` in the companion submission enumerates exactly which stores
need it).

---

## Note on submitting one entry or two

* **Two entries** — the tool and the fix each stand alone and each maps to a different line of the
  stated selection criteria (analytic tooling vs. resolving a bug in a tool people use). Multiple
  submissions are explicitly permitted.
* **One entry** — a single, stronger story: "we audited the catalog, found the class, found the code
  that consumes it, and fixed it". Simpler for the reviewer to weigh.
* Recommendation: submit the **fix as entry #2** and let the tool be entry #1, but mention the other
  in each, so a reviewer reading either one sees the whole chain.
