<!-- 文本副本：这是实际发布到 GitHub 的文本，数字为发布当时的值。 -->
> **文本副本** —— 以下是实际发布到 GitHub 的文本，数字为**发布当时**的值；后续目录变化以 [README](../README.md) / [COVERAGE](../COVERAGE.md) 为准。

**The manifest knows the pitch; the published OME metadata does not**

### What was checked

A read-only, metadata-only sweep of every Zarr root the catalog publishes — 894 roots, ~1,900
requests, no chunk bytes downloaded. Method and raw per-store output:
<https://github.com/gaogao94/scroll-catalog-audit>.

**81 stores state a µm pitch in their own name while their OME metadata carries no `axes[].unit`
and a level-0 `scale` of `[1.0, 1.0, 1.0]`.**

### The new part: the catalog already knows the value

`metadata.min.json` records the physical pitch for these volumes. For **77 of the 81** affected
stores, the manifest entry that declares the store carries `properties.pixel_size_um`, and it
**matches the pitch encoded in the store name exactly**:

| store | name states | OME metadata says | manifest `properties.pixel_size_um` |
|---|---|---|---|
| `PHerc0009B/volumes/20250521125136-8.640um-1.2m-116keV-masked.zarr` | 8.64 µm | `axes[].unit` absent, `scale = [1,1,1]` | **8.64** |
| `PHerc0009B/volumes/20250820154339-2.401um-0.3m-77keV-masked.zarr` | 2.401 µm | `axes[].unit` absent, `scale = [1,1,1]` | **2.401** |
| `PHerc0009B/volumes/20260319104112-2.401um-0.3m-77keV-masked.zarr` | 2.401 µm | `axes[].unit` absent, `scale = [1,1,1]` | **2.401** |

Breakdown of the 81: **76 × `volume:ome-zarr`**, 1 × `volume:surface-prediction-zarr` and
**4 × `segment:layers-zarr`** — those four are the group tracked in #1951 and the only ones without a
manifest pitch. They are also copies of one store name; see
[the note there](https://github.com/ScrollPrize/villa/issues/1951#issuecomment-5970262863).

Ten of the 81 are published on the **alternate access root** (`data.aws.ash2txt.org`, `samples/…`
layout) and seven of those ten are not present in the S3 bucket at all. They show the same pattern,
so the class is not specific to one host.

One case where the two disagree: `PHercParis4/representations/predictions/surfaces/…-surface-recto-2um-ps256-L0-th0.45.zarr`
has **`2um` in its name while the manifest entry says `2.4`**, and its OME metadata carries no scale
at all — so nothing in the store resolves the conflict. Flagging it as a single observation rather
than a pattern: it is the only disagreement among the 77 stores where both values exist.

So the information is not missing from the catalog. It is recorded at manifest level and **not
propagated into the OME metadata of the store itself**.

### Why it matters

Any reader that follows the OME-Zarr metadata — which is the documented way to get voxel size —
gets `1.0` for these volumes. Distances, offsets and physical measurements are then wrong by the
ratio of the real pitch (8.64× for the 8.64 µm volumes). Nothing in the store signals this: the run
succeeds and the metadata looks well-formed.

This also explains why the same reader-side code paths that were already reported keep appearing:
when the metadata is absent, three places in the toolchain silently substitute `1.0` rather than
reporting it (#1954, #1956), and a producer can write `1.0` in the first place (#1955).

### Suggested fix

At publish time, take the value that is already in the manifest and write it into the store:

* `multiscales[0].axes[].unit = "micrometer"` for all three axes;
* level-0 `coordinateTransformations[scale] = [p, p, p]` with the existing per-level ratios
  preserved for the coarser levels.

Failing that, a check at catalog-build time would catch it: for each published `ome-zarr` whose
manifest entry has `properties.pixel_size_um`, assert that the store's OME metadata carries the
matching scale. The audit tool linked above already computes both sides of that comparison and can
be run as a one-command check (`python -m scroll_catalog_audit report`).

### Reproduce

```
python -m scroll_catalog_audit scan --workers 10     # ~23 min, 894 roots, no chunk bytes
python -m scroll_catalog_audit report --merge results_deep.jsonl
python -m scroll_catalog_audit explain --path PHerc0009B/volumes/20250521125136
```

### Scope notes

* I did not download chunk bytes, so I make no claim about the arrays' contents — this is purely a
  metadata-layer report.
* Counts come from two independent sweeps merged per store (the run that obtained metadata wins);
  a single sweep gives 67 rather than 71 because of transient fetch failures, which the tool labels
  and re-runs rather than reporting. Expect a few stores to move between classes on a re-run.
