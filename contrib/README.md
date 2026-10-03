# contrib/ — proposed upstream changes and their evidence

Everything in this directory is packaged so a reviewer can see the whole chain from **one
repository**: the catalog audit, what it found, the code that consumes it, and the patches that fix
it. Nothing here is applied upstream yet; each item names the issue or PR it is intended for.

| File | What it is | Intended target |
|---|---|---|
| `issue-1951-addendum.md` | Catalog-wide quantification of the missing-physical-scale class (71 stores, 66 of them raw CT volumes, 39 samples) plus a negative result on level ladders | comment on [ScrollPrize/villa#1951](https://github.com/ScrollPrize/villa/issues/1951) |
| `scale-fallback-issue.md` | Reader side: three places that substitute `1.0` for a missing physical scale without a word, with `file:line`, executed before/after evidence, and an appendix listing four further candidates found by the same search | new issue in `ScrollPrize/villa` |
| `lasagna-scale-fallback.patch` | Reader-side fix: warning naming the affected levels + opt-in `--require-scale`; 4 files, +111/−2, includes tests | PR against `ScrollPrize/villa` |
| `spiral-unitless-issue.md` | Writer side: `tracks_to_ome_zarr` writes `1.0` into newly produced OME-Zarr metadata when no voxel size is available | new issue / PR description |
| `spiral-unitless-scale.patch` | Writer-side fix: warn before writing a unitless scale; 2 files, +28/−0, includes a test modelled on an existing fixture | PR against `ScrollPrize/villa` |
| `vesuvius-scale-warnings-issue.md` | The two remaining reader-side sites in `tifxyz_label_transfer` (one of them records the assumed scale **as evidence**) | new issue / PR description |
| `vesuvius-scale-warnings.patch` | Reader-side fix for those two: `warnings.warn` on a missing scale, values unchanged; 4 files, +55/−0, includes two tests | PR against `ScrollPrize/villa` |

## How the pieces relate

```
scroll-catalog-audit  ──finds──▶  71 stores whose name states a µm pitch
        (this repo)               while their OME metadata carries none
                                          │
                     ┌────────────────────┴────────────────────┐
                     ▼                                         ▼
        reader side (lasagna)                        writer side (spiral-fitting)
        silently substitutes 1.0                     can WRITE 1.0 into new stores
        → makes existing gaps invisible              → creates new instances
                     │                                         │
                     ▼                                         ▼
        lasagna-scale-fallback.patch                 spiral-unitless-scale.patch
```

Both patches are warning-only and backward compatible: the values produced and consumed are
unchanged, and the new behaviour is a message (plus, on the reader side, an opt-in hard failure).

## Verification status of each patch

| | `lasagna-scale-fallback.patch` | `spiral-unitless-scale.patch` |
|---|---|---|
| `git apply --check` against current `main` | OK | OK |
| Base identical to `origin/main` | yes (3 files) | yes (2 files) |
| `python -m py_compile` | OK | OK |
| Tests added | 2 in an existing file + 1 new guarded file | 1 in an existing file |
| Tests executed locally | 2 PASS (with a minimal pytest shim) | not run (no `click`/`zarr`/`numpy` here); fixture copied from a passing test |
| Behaviour change | none by default; `--require-scale` is opt-in | none (warning only) |

`vesuvius-scale-warnings.patch` (4 files, +55/−0) is in the same state as those two: `git apply
--check` OK, base identical to `origin/main`, all four files compile. Its two tests
(`assertWarns(UserWarning)`) were not executed locally — this environment lacks `tifffile`, `PIL`
and `yaml` — and run in CI.

## Full chain

```
scroll-catalog-audit  ──finds──▶  71 stores whose name states a µm pitch
        (this repo)               while their OME metadata carries none
                                          │
        ┌─────────────────────────────────┼─────────────────────────────────┐
        ▼                                 ▼                                 ▼
 reader side (lasagna)          reader side (tifxyz_label_transfer)   writer side (spiral-fitting)
 silently substitutes 1.0       one site even records the assumed      can WRITE 1.0 into new
                                scale as *evidence*                    stores
        │                                 │                                 │
        ▼                                 ▼                                 ▼
 lasagna-scale-fallback.patch   vesuvius-scale-warnings.patch     spiral-unitless-scale.patch
        +111/−2                          +55/−0                            +28/−0
```

All three patches are warning-only and backward compatible: the values produced and consumed are
unchanged, and the new behaviour is a message (plus, on the reader side, an opt-in hard failure).
