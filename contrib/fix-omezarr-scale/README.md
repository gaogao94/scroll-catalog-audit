# `fix_omezarr_scale.py` — write the corrected metadata for the stores that lack a physical scale

The validator next door detects the defect; this produces the repair.

For a store whose name states a micrometre pitch but whose published metadata carries no
`axes[].unit` and a level-0 `scale` of `[1,1,1]`, the pitch is usually **already recorded in the
catalog manifest**, so the fix is a metadata edit rather than a re-render. This reads the store's live
metadata, applies the change the plan describes, prints a diff, and — only if asked — writes the
corrected file to a directory for review.

```
python fix_omezarr_scale.py --plan ../../SCALE_FIX_PLAN.json --path <store path>            # print a diff
python fix_omezarr_scale.py --plan ../../SCALE_FIX_PLAN.json --path <store path> --out DIR  # write it
python fix_omezarr_scale.py --plan ../../SCALE_FIX_PLAN.json --path <store path> --local DIR
```

Nothing is uploaded: `--out` writes the corrected `.zattrs` / `zarr.json`, and whoever publishes the
store uploads it with the tooling they already use. Credentials never enter this script, and the change
stays reviewable as a diff.

## Guards, because this edits published data

| guard | behaviour |
|---|---|
| dry run by default | nothing is written unless `--out` is given |
| the store must match the plan | if the live scales differ from the plan's `scales_now`, it refuses and prints both, so a store fixed since the plan was built cannot be silently rewritten |
| already fixed | reports that the corrected document is identical and stops |
| level count | refuses when the plan and the store disagree on how many levels exist |

Exit codes: 0 when it did something or found nothing to do, 2 when the store has no plan entry or
its metadata cannot be read, 3 when a guard above refused.

Every proposed value comes from the plan, which was built from the manifest's own `pixel_size_um` and
the store's own level ratios — in particular it keeps a surface volume's **anisotropic** ladder (z at
the base pitch, in-plane doubling) rather than forcing an isotropic one.

## Status

Verified: 10 unit tests (`python -m unittest test_fix_omezarr_scale`), and a dry run against a real
store in the published catalog:

```
store      : PHerc0009B/volumes/20250521125136-8.640um-1.2m-116keV-masked.zarr
format     : v2 (.zattrs)
pitch      : 8.64 um  (confidence: DERIVED_UNVERIFIED)
  - set unit on 3 axis/axes
  - rewrote scale on 6 level(s)
    [1.0, 1.0, 1.0]  ->  [8.64, 8.64, 8.64]
    [2.0, 2.0, 2.0]  ->  [17.28, 17.28, 17.28]
    ...
```

The plan itself marks 77 of the 81 entries `DERIVED_UNVERIFIED`: the manifest records the in-plane
pixel size, and the store's own ladder supplies the rest, which is not the same as the publisher
confirming the value. That is stated in every dry run rather than hidden.
