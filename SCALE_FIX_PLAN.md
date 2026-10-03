# Dry-run repair plan for the missing-physical-scale class

**Nothing here modifies the bucket.** `SCALE_FIX_PLAN.json` is a proposal: for each of the 81
affected stores it lists the `axes[].unit` and per-level `scale` that would make the store's OME
metadata agree with the pitch the catalog manifest already records. It exists because the
maintainer note closing [#1760](https://github.com/ScrollPrize/villa/issues/1760) says data errors in
**the open data bucket** are actionable (while `dl.ash2txt.org` is not), and all 81 stores are in
that bucket.

## Two rules, two confidence levels — and why the difference matters

**Rule A — copy from a correct sibling (4 stores, high confidence).**
A store name that is published more than once can have a copy that already carries the correct
ladder. For the four stores in [#1951](https://github.com/ScrollPrize/villa/issues/1951) eleven such
copies exist, and the proposal is taken **verbatim** from one of them:

```
source  PHerc1447/segments/20250502180708-…/surface-volumes/8.64um-1.2m-116keV-volume-20250521151220.zarr
axes    ["micrometer", "micrometer", "micrometer"]
scales  [8.64, 8.64, 8.64] → [8.64, 17.28, 17.28] → [8.64, 34.56, 34.56] → … → [8.64, 276.48, 276.48]
```

Note the shape of that ladder: **z stays at the base pitch while the in-plane axes double per
level**. This is the convention for surface volumes — 674 of the 689 unit-carrying segment stores
use exactly this form.

**Rule B — derive from the manifest pitch (77 stores, needs confirmation).**
For the raw CT volumes there is **no reference copy**: **0 of the 76 `volume:ome-zarr` stores carry
any unit at all**, so nothing in the catalog shows what a correct raw-volume ladder looks like. The
proposal applies the manifest's `pixel_size_um` to the store's own level ratios, which yields an
isotropic ladder:

```
PHerc0009B/volumes/20250521125136-8.640um-1.2m-116keV-masked.zarr   (manifest pitch 8.64)
scales now  [1,1,1] → [2,2,2] → … → [32,32,32]
proposed    [8.64,8.64,8.64] → [17.28,17.28,17.28] → … → [276.48,276.48,276.48]
```

**This rule is a guess about the z spacing, and it is labelled as one.** The manifest records
in-plane pixel size; whether the volume's z spacing equals it is not something I can determine from
metadata, and an anisotropic raw-volume ladder (z constant, in-plane doubling) is equally plausible.
Applying Rule B without that confirmation risks replacing one silent error with another, which is
why the plan marks these entries `DERIVED_UNVERIFIED` and why nothing was written.

## What the plan contains

| confidence | stores | basis |
|---|---:|---|
| `COPY_FROM_SIBLING` | 4 | a sibling copy's metadata, verified to exist and to carry units |
| `DERIVED_UNVERIFIED` | 77 | manifest `properties.pixel_size_um` × the store's own ratios |

All 81 are covered (`PLAN`, none skipped). Each entry records the proposed values, the source (for
Rule A) or the pitch and ratio basis (for Rule B), and the note above.

## How this was checked

The sibling rule was validated by fetching the sibling's `.zattrs` and comparing it with what the
propagation rule would have produced — they **disagree** (anisotropic vs isotropic), which is how
the wrong first draft was caught. The committed plan therefore carries the sibling's values, not the
derived ones, for those four stores. Regenerate the whole plan with `ops/build_scale_fix.py` in the
working repository.

## What a maintainer would need to decide

1. Whether Rule B's isotropic ladder is right for raw CT volumes, or whether z should stay constant
   as it does for surface volumes. One sentence settles it; after that the plan is mechanical.
2. Whether to fix the 81 stores in place, or to fix the publisher so the manifest value is written
   into the metadata at publish time (which would also stop new instances — see
   [#1957](https://github.com/ScrollPrize/villa/issues/1957)).
