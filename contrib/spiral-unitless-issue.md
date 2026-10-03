# Issue / PR draft · unitless scale is written into output metadata without a word

> **Status**: patch ready (`spiral-unitless-scale.patch`, 2 files, +28/−0, `git apply --check` verified), waiting on G1 to open the PR.
> **Companion**: `work/patches/scale-fallback-issue.md` (the *reader* side of the same class) and the `scroll-catalog-audit` tool, which enumerates the stores this pattern produces.

---

## Body (English, repository language)

**`tracks_to_ome_zarr`: a unitless scale is written into the output metadata without a word**

### What happens

```python
if voxel_size:
    scale = _parse_zyx(voxel_size, '--voxel-size', float)
else:
    scale = reference_scale or (1.0, 1.0, 1.0)     # line 613
unit = unit or reference_unit
```

When neither `--voxel-size` nor a `--like` reference supplies a physical scale, the tool writes
`scale: [1.0, 1.0, 1.0]` into the OME-Zarr metadata of a **newly produced** store, silently. The run
succeeds and the output looks well formed.

### Why it matters more than a read-side default

This is the *producing* end of a pattern that the companion audit enumerates in the catalog: **67
published stores state a µm pitch in their own name while their OME metadata carries no scale** (62
of them raw CT volumes). A reader-side default makes an existing gap invisible; this line can create
new instances of it — and because the output is a valid OME-Zarr whose `scale` looks deliberate,
nothing downstream can tell "unitless" from "1 µm per voxel".

### Proposed change

Print the assumed value and how to fix it:

```
WARN: no --voxel-size and no --like reference provide a physical scale; writing 1.0 per voxel
      into the output OME-Zarr metadata. Pass --voxel-size Z,Y,X if the voxel size is known.
```

* Warning only. No behaviour change; the written value is byte-identical, and the option to pass a
  real scale already exists.
* `click.echo(...)` with default stdout, matching how this script already reports to the user
  (line 779). Happy to move it to `err=True` if you prefer warnings on stderr.
* The test follows the fixture already used by `test_pipeline_schedule_does_not_change_output`
  (a small `dbm` of pickled polylines + `CliRunner().invoke(main, ...)`) and asserts the warning text
  appears in `result.output`.

If you would rather the tool **refuse** to write a unitless scale unless explicitly allowed
(e.g. `--allow-unitless-scale`), say so and I will turn the warning into an error with the opt-out —
I kept it a warning because some existing pipelines may rely on producing schema-valid output
without a known voxel size.

### Verification

* `git apply --check` → **OK**; both files compile (`python -m py_compile`).
* Base verified against upstream `main`: both touched files hash-identical to `origin/main` at the
  time of writing (no rebase needed).
* The new test mirrors a test that already passes in this file; the fixture (one `dbm` record,
  `--shape 16,16,16 --chunk 16`) is copied from it rather than invented.
* Not run locally: this environment has no `click`/`numpy`/`zarr`, so the assertion is verified by
  construction against the existing test's shape. It will run in CI.

### Requested maintainer decision

Warning vs. hard error (with `--allow-unitless-scale`), and stdout vs. stderr for the warning.

---

## 附：为什么这是"源头修复"

| | 读者侧（第一份补丁） | 写者侧（本补丁） |
|---|---|---|
| 作用 | 让**已存在**的缺失可见（告警 + `--require-scale`） | 让**新产生**的无单位元数据不再沉默 |
| 覆盖 | `lasagna` 三处 | `spiral-fitting` 一处 |
| 效果 | 已发布的 67 个 store 不再被静默误读 | 阻止同类新实例进入目录 |

两份补丁合起来构成一个完整叙事：**我们审计了目录 → 找到吃这个缺失的代码 → 修了读取端 → 又掐断了产生端。**
