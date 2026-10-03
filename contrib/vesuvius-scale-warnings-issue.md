# Issue / PR draft · two more places treat a missing physical scale as 1.0

> **Status**: patch ready (`vesuvius-scale-warnings.patch`, 4 files, +55/−0, `git apply --check` verified), waiting on G1.
> **Companion**: `scale-fallback-issue.md` (the `lasagna` reader-side fix, which lists these two as candidates found by the same search) and `spiral-unitless-issue.md` (the writer side).

---

## Body (English, repository language)

**Two more readers turn a missing physical scale into 1.0 silently — and one of them records it as evidence**

Following the survey in the companion issue (a repo-wide search for silent physical-scale defaults),
these are the two `vesuvius/tifxyz_label_transfer` sites that were left out of that patch to keep its
diff reviewable. Both are warning-only and behaviour-preserving.

### 1. `tifxyz_label_transfer/io.py:161` — a missing `scale` key in `meta.json`

```python
scale = metadata.get("scale", [1.0, 1.0])
if not isinstance(scale, list) or len(scale) < 2:
    raise ValueError(f"invalid scale in {surface_path / 'meta.json'}")
```

A **missing key** silently becomes one cell per voxel, while the very next lines already refuse a
malformed one. The file's own convention is documented two lines down (`[x_scale, y_scale]`, grid
cells per voxel), so a surface without `scale` is unknown, not unitary.

Change: `warnings.warn(...)` before falling back, `stacklevel=2`. The value used is unchanged.

### 2. `prepare_canvas_offset_evidence.py:205` — a level without a `scale` transform

```python
scale = (1.0, 1.0, 1.0)
for transform in dataset.get("coordinateTransformations") or []:
    if transform.get("type") == "scale":
        ...
        scale = values
```

If no 3-element `scale` transform is found, the level is recorded as 1.0 — and this value is written
into the emitted evidence JSON (`"scale_zyx": list(info.scale_zyx)`), i.e. **the evidence asserts a
physical scale that was never observed**. For a tool named "prepare auditable evidence", that is the
part worth fixing first.

Change: track whether a scale was found and `warnings.warn(...)` when it was not; the recorded value
is unchanged.

### Why warn and not raise

Both are library/CLI helpers that may legitimately be run against hand-made or legacy surfaces; a
missing key is not necessarily fatal, but it must not be invisible. A warning is visible by default
(Python prints `UserWarning` to stderr), is filterable, and does not break existing pipelines. If you
would rather these be hard errors, I will switch them — the sites are one line each.

### Tests

* `test_io.py` — builds the same TIFXYZ fixture the existing `meta.json` test uses, omits `scale`,
  and asserts `assertWarns(UserWarning)` plus the resulting `scale_yx == (1.0, 1.0)`.
* `test_prepare_canvas_offset_evidence.py` — patches `_cat_json` (the existing tests already mock
  rclone-facing helpers) so `inspect_zarr` sees a dataset with no scale transform, and asserts the
  warning and `scale_zyx == (1.0, 1.0, 1.0)`.

Both follow the fixtures already in those files rather than inventing new scaffolding.

### Verification

* `git apply --check` → **OK** (4 files, +55/−0); all four files compile (`python -m py_compile`).
* Base verified against upstream `main`: all four touched files hash-identical to `origin/main`.
* **Not executed locally**: this environment lacks the modules these tests import (`tifffile`, `PIL`,
  `yaml`, …), so the tests run in CI. Stated here rather than claimed green.

### Requested maintainer decision

Warning vs. hard error, and whether the evidence JSON should carry an explicit
"scale assumed, not observed" marker instead of silently recording 1.0.

---

## 附：这条线现在覆盖了什么

| 层次 | 位置 | 状态 |
|---|---|---|
| 读取端（主链路） | `lasagna/scripts/download_omezarr.py` ×2、`zarr_threshold_masks.py` | 补丁已备（+111/−2，测试本机 PASS） |
| 读取端（其余两处） | `tifxyz_label_transfer/io.py`、`prepare_canvas_offset_evidence.py` | **本补丁**（+55/−0） |
| 写者端 | `spiral-fitting/tracks_to_ome_zarr.py` | 补丁已备（+28/−0，测试照抄既有夹具） |
| 防御性默认值 | `download_omezarr.py:679` | 不单独改：上游已由第一份补丁在更早的位置报出缺失 |

三份补丁合起来，把"缺失的物理尺度被静默当成 1.0"这条链从**产生端**到**读取端**全部标出来了。
