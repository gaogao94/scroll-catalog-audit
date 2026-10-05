# `check_omezarr_metadata.py` - publish-time metadata check

A store whose OME metadata is wrong does not fail; it returns a wrong number or blank data. This script
turns every defect class found in the catalog audit into a check that can run before publishing.

    python check_omezarr_metadata.py --path <catalog path | local dir | url>
    python check_omezarr_metadata.py --path <...> --json
    python check_omezarr_metadata.py --path <...> --no-chunks    # skip the listing

(`--root` is accepted as an alias, because the composite action passes it.)

Exit code 1 when any ERROR was reported. Metadata only; no chunk bytes are downloaded.

Checks: units missing from every axis while the name states a pitch; level-0 `scale` of `[1,1,1]` on a
store whose name states a pitch (#1951); a declared level with no array header; a level that exists but
holds no chunks (#1892); chunk larger than the array shape; a non-zero `fill_value`; level paths that
are not `0..n-1`.

## Status

Ready, verified, and pushed as branch `check-omezarr-metadata` on the fork
(`gaogao94/villa`, commit `32dfde0`, two files, +550/-0). Opening the pull request against
`ScrollPrize/villa` is currently rejected with `FORBIDDEN: does not have the correct permissions to
execute CreatePullRequest` even though the fork is public and the same flow created three pull requests
on 2026-10-03. One-click URL if the web flow is not similarly restricted:

    https://github.com/ScrollPrize/villa/compare/main...gaogao94:check-omezarr-metadata?expand=1

The copy here is byte-identical to the branch, so it stays citable while the pull request is blocked.

## Verified

    python -m unittest test_check_omezarr_metadata.py     # 35 tests, OK

and by hand against four published stores:

| store | result |
|---|---|
| `PHerc0009B/.../8.64um-1.2m-116keV-volume-20250521125136.zarr` | no findings |
| `PHerc0814/.../1.129um-0.22m-59keV-volume-20260521123630-L1.zarr` | `NO_CHUNKS` — **removed upstream 2026-10-05**, so this row is the one that no longer reproduces; the check still detects the class |
| `PHerc1447/.../8.64um-1.2m-116keV-volume-20250521151220.zarr` | `UNITS_MISSING_PITCH_IN_NAME`, `SCALE_IS_UNIT` |
| `PHerc0332/volumes/20251211183505-2.399um-0.2m-78keV-masked.zarr` | `UNITS_MISSING_PITCH_IN_NAME`, `SCALE_IS_UNIT` (correct: all 77 raw CT volumes are unitless) |

Three bugs were found by running the script rather than by the tests: a relative `--root` was treated as
a local directory, the level scale was read from `datasets[].scale` when OME-NGFF nests it under
`coordinateTransformations`, and the chunk check counted `.zarray`/`.zattrs` keys as chunks.
