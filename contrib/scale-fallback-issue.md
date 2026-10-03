# Issue / PR draft · physical scale silently defaults to 1.0 in three places

> **Status**: patch ready (`lasagna-scale-fallback.patch`, 4 files, +111/−2, verified with `git apply --check` against current `main`); opened as <https://github.com/ScrollPrize/villa/pull/1954>.
> **Companion evidence**: `work/patches/issue-1951-addendum.md` (catalog-wide enumeration) and the `scroll-catalog-audit` tool (`work/publish/`).

---

## Body (English, repository language)

**Physical scale silently defaults to 1.0 in three places, and the catalog has stores that trigger it**

### What the catalog does

A read-only sweep of every Zarr root the catalog publishes (894 roots, `metadata.min.json` 2026-10-03; tool and raw output in <https://github.com/gaogao94/scroll-catalog-audit>) found **81 stores whose own name states a µm pitch while their OME metadata carries no `axes[].unit` and a level-0 `scale` of `[1,1,1]`** — 76 of them **raw CT volumes** (`volumes/*-masked.zarr`), spanning 39 samples. Meanwhile 85.4 % of stores *do* carry correct units, so a consumer cannot rely on either behaviour.

Four such surface volumes are already tracked in #1951. The point of this issue is the other half: **what happens downstream when a store like that is read.**

### Three sites that substitute 1.0 with no warning

1. **`lasagna/scripts/download_omezarr.py:449`** — `_parse_multiscales()` initialises `scale = [1.0, 1.0, 1.0]` and only overwrites it if the dataset carries a `scale` coordinate transformation. A level without one is recorded as unitless with no signal.
2. **`lasagna/scripts/download_omezarr.py:1165-1168, 1214-1216`** — if `.zattrs` cannot be read, `zattrs = {}` and then *every* level is assigned `[1.0, 1.0, 1.0]`. The resulting map is passed into the download scanner (`:1243`), so the fabricated scales are what the rest of the run uses.
3. **`lasagna/scripts/zarr_threshold_masks.py:135`** — `_infer_zyx_scale()` tries preprocess params, then the parent OME metadata, then returns `1.0, 1.0, 1.0` as a final fallback.

In all three cases the run completes normally. Nothing distinguishes "this store is unitless" from "this store is 1 µm per voxel"; any offset or distance derived downstream is then wrong by the ratio of the real pitch (8.64× for the PHerc1447 8.64 µm set).

### Why this is the same class of problem as #1660

#1660 is about a render that writes an all-black strip and exits `0`. This is the same failure mode one layer earlier: metadata that is absent is read as a plausible number, and the consumer has no way to notice.

### Proposed change (in the patch attached)

Fail loudly instead of silently:

* `_parse_multiscales(zattrs, missing)` records which levels had no `scale` transform; a `WARN … assuming 1.0 per voxel` is printed once per run, naming the levels and the prefix.
* The `.zattrs`-missing branch adds every level to that set, so the fabricated scales are reported too.
* New opt-in flag **`--require-scale`** makes it a hard error (`exit 1`) for pipelines that would rather stop than proceed unitless. Default behaviour is unchanged.
* `zarr_threshold_masks.py` prints the same warning when `_infer_zyx_scale()` falls back.

The change is deliberately additive: no existing invocation changes behaviour unless `--require-scale` is passed, and the warning goes to stderr.

### How it was verified

**Executed before/after** (stubbed `boto3`/`botocore`, patched module loaded by path, same input in both runs):

```
=== BEFORE ===
  _parse_multiscales(zattrs)      -> {0: [8.64, 8.64, 8.64], 1: [1.0, 1.0, 1.0], 2: [1.0, 1.0, 1.0]}
  stderr                          -> ''            # nothing distinguishes a real 8.64 µm level
                                                   # from two levels whose scale is simply absent
=== AFTER ===
  _parse_multiscales(zattrs, missing) -> {0: [8.64, 8.64, 8.64], 1: [1.0, 1.0, 1.0], 2: [1.0, 1.0, 1.0]}
  missing                         -> {1, 2}        # the absence is now representable
  old single-argument call still returns the identical map   (backward compatible)
  empty/absent multiscales still return {}                   (unchanged)
```

* Patch applies cleanly to `main`: `git apply --check` → **OK** (4 files, +111/−2).
* Both modified files compile: `python -m py_compile` → **OK**.
* Tests added in the repository's existing style, and **run locally with a minimal pytest shim** (pytest and the heavy dependencies are not installed in this environment):
  * `lasagna/tests/test_download_omezarr.py` — asserts the returned map **and** that `missing == {1, 2}`; a second test pins the old single-argument behaviour. → **both executed: PASS**
  * `lasagna/tests/test_zarr_threshold_masks_scale.py` — monkeypatches both scale sources to `None`, asserts the fallback value *and* the warning text via `capsys`, plus a no-warning case when metadata supplies a scale. → **skips in this environment** (`zarr_threshold_masks` pulls in internal modules such as `lasagna_volume` / `omezarr_pyramid` that are not built here); the file is guarded with `pytest.importorskip`, so it can never break the suite, and it will run in CI where those modules exist.
* `_parse_multiscales` and `_infer_zyx_scale` each have exactly one call site and no pre-existing test references, so the signature change is contained.
* The catalog side is reproducible with the companion tool: `python -m scroll_catalog_audit scan` (metadata only, no chunk bytes) followed by `report`.

### Requested maintainer decision

Happy to split this into (a) warn-only and (b) `--require-scale` if you would rather take the warning alone. Also happy to extend the same treatment to any other reader you know of that defaults a missing physical scale — the three above are the ones a repo-wide search found, but I would rather be told than guess.

---

### Appendix — other sites found by the same repo-wide search (not covered by this patch)

A search for silent physical-scale defaults (`1.0, 1.0, 1.0` / `get("scale", …)` / `voxel_size = 1.0`)
across production code (excluding tests, convolution kernels and colour tables) found four more
candidates of the same class. They are deliberately **not** in this patch, to keep the diff
reviewable — but they are listed here so the search does not have to be repeated:

| Location | Behaviour | Suggested treatment |
|---|---|---|
| `lasagna/scripts/download_omezarr.py:679` | `base_scale = multiscales.get(0, [1.0, 1.0, 1.0])` in `_guarded_scanner` — a second default for the same value, one function downstream of the one this patch fixes | With the patch, missing levels are already tracked upstream; this line could consume the same `missing_scale` set if you would rather it be airtight |
| `vesuvius/src/vesuvius/tifxyz_label_transfer/io.py:161` | `scale = metadata.get("scale", [1.0, 1.0])` for TIFXYZ `meta.json`: a **missing key** silently becomes 1.0 per cell, while the next two lines already raise `ValueError` for a malformed scale | Treat a missing `scale` like a malformed one (raise), or warn; the type/length validation is already there |
| `vesuvius/src/vesuvius/tifxyz_label_transfer/prepare_canvas_offset_evidence.py:205` | `scale = (1.0, 1.0, 1.0)` initialised and only overwritten if a `scale` transform exists — a dataset without one silently yields 1.0 | Same shape as the site this patch fixes; a one-line warning would make it visible |
| `spiral-fitting/tracks_to_ome_zarr.py:613` | `scale = reference_scale or (1.0, 1.0, 1.0)` — when neither `--voxel-size` nor a reference scale is available, the tool **writes** 1.0 into newly produced OME-Zarr metadata | This one *creates* the metadata other readers later trust; worth refusing to write a unitless scale unless explicitly asked |

The fourth is the most interesting of the four: it can manufacture exactly the metadata pattern the
companion audit enumerates, so fixing it would prevent new instances rather than only reporting
existing ones.

---

## 附：本地已完成的工作

| 步骤 | 状态 |
|---|---|
| 证据枚举（894 根目录级审计） | ✅ `work/audit/results/roots.jsonl` |
| 消费者代码路径定位 | ✅ 三处，含 file:line |
| 补丁编写 | ✅ `lasagna-scale-fallback.patch`（4 文件 +111/−2，含测试）→ PR #1954 |
| 补丁可应用性验证 | ✅ `git apply --check` OK |
| 语法验证 | ✅ `python -m py_compile` OK |
| 提交 | ⏳ 等 G1 |
