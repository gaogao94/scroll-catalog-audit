# Remediation options for the three classes this audit reports

The maintainer note closing [#1760](https://github.com/ScrollPrize/villa/issues/1760) scopes what the
team can act on: data errors **in the open data bucket** are worth looking into, `dl.ash2txt.org` is
not. All three classes below are in that bucket, so each comes with a concrete option rather than
only a description. **Nothing here has been written to the bucket** — these are plans.

| class | stores | plan | confidence |
|---|---:|---|---|
| A · no physical scale, pitch in the name | 81 | `SCALE_FIX_PLAN.md` / `.json` | 4 copy-from-sibling, 77 derived |
| B · prediction outputs with no scale at all | 43 | `PREDICTION_SCALE_PLAN.json` | all derived |
| C · declares six levels, holds no chunks | 1 | **resolved upstream 2026-10-05** (artifacts removed) | — |

---

## A — the 81 stores (#1951, #1957)

For each store: the `axes[].unit` and per-level `scale` needed to agree with the pitch the manifest
already records. Four stores take their ladder **verbatim from a verified sibling copy**; the other
77 are derived from the manifest pitch applied to the store's own ratios.

The open question is one sentence long: **for raw CT volumes, does z stay at the base pitch (as it
does for surface volumes — 674 of 689 unit-carrying segment stores) or scale with the levels?** The
manifest records in-plane pixel size only, so the derived entries are labelled `DERIVED_UNVERIFIED`
until that is answered.

### A safety check on the proposed values

Store names of the form `<pitch>um-...-L<n>.zarr` state the source scan's pitch and the level the store
was taken from, so their **level-0** pitch is `pitch x 2^n`, not `pitch`. Applying a plan that ignored
this would make such a store worse than leaving it unitless.

Checked across all 81 plans: **one** has an `L` token, and it is `L0` (`...-2um-ps256-L0-th0.45.zarr`),
where `2 x 2^0 = 2` and the proposed level-0 scale comes from the manifest anyway. So no plan in the
list is affected. The same convention is handled explicitly in the publish-time check
(`contrib/check-omezarr-metadata`), where it was found by a false positive on the `-L1` store in #1892.

## B — the 43 prediction stores

Every `volume:surface-prediction-zarr` store declares `scale = [1,1,1]` and no `axes[].unit`, while
the manifest entry that declares it **does** carry `properties.pixel_size_um` — all 43 of them
(verified: 0 without). Example:

```
PHerc0009B/representations/predictions/surfaces/20260319104112-…-L2-th0.2.zarr
  manifest pitch : 2.401 µm
  scale now      : [1,1,1] → [2,2,2] → … → [32,32,32]
  proposed       : [2.401,…] → [4.802,…] → … → [76.832,…]
```

Same caveat as class A: derived, not copied, because no prediction store in the catalog carries a
scale to copy from.

## C — the header-only store (#1892)

`PHerc0814/segments/20260226123353-auto_grown_20260226123353106/surface-volumes/1.129um-…-L1.zarr`
declares six levels, has a `.zarray` at each, and **no chunks anywhere**: every read returns
`fill_value` with no error. It is **declared in the manifest** (`sample PHerc0814`, section
`segments`, key `20260226123353`, type `layers-zarr`), so a consumer looking for a surface volume of
this segment finds it and gets blank data.

Evidence bearing on the two options:

* **The same segment rendered its other two volumes fine** — `2.399um-…-20260309142202.zarr` has
  297 chunks on the first page and `9.362um-…-20250804134230.zarr` has 48. So this is not a broken
  segment pipeline; it is one volume that came out empty.
* **16 same-name siblings elsewhere in the catalog do have chunks** (297/296 keys). They are *not* a
  drop-in replacement: the store name encodes the source scan, not the segment extent, and copies
  differ in size — a rendering for another segment covers a different surface region.

So the options are (a) re-render that one surface volume for this segment, or (b) drop this origin
from the manifest so consumers stop being handed a store that reads as blank. Option (b) is a
one-line catalog change and can be done today; option (a) restores the data.

---

## What is needed from a maintainer

1. **One sentence** on the z spacing for raw volumes and prediction surfaces (classes A and B).
   After that both plans are mechanical.
2. A decision on **fix-in-place vs fix-the-publisher**: writing the manifest value into the metadata
   at publish time would stop new instances, which is the difference between repairing 124 stores
   and repairing the pipeline that produced them.
3. For class C, whether the store is worth re-rendering or dropping.

Regenerate all three plans: `ops/build_scale_fix.py`, `ops/build_prediction_plan.py` (read-only, no
chunk bytes downloaded).
