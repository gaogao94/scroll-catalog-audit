# Vesuvius open-data catalog · consistency audit

- stores scanned: **120** (S3 origins 110, other roots 10)
- stores with full physical units: **0**
- findings: `AXES_UNIT_MISSING` × 65, `SCALE_IS_UNIT` × 65, `SCALE_UNITLESS_NO_NAME_UM` × 42, `NO_METADATA` × 3

## Summary by sample

| sample | findings |
|---|---|
| PHerc0139 | `AXES_UNIT_MISSING` × 9, `SCALE_IS_UNIT` × 9, `SCALE_UNITLESS_NO_NAME_UM` × 2 |
| PHercParis4 | `AXES_UNIT_MISSING` × 6, `SCALE_IS_UNIT` × 6, `SCALE_UNITLESS_NO_NAME_UM` × 2 |
| PHerc0500P2 | `AXES_UNIT_MISSING` × 4, `SCALE_IS_UNIT` × 4, `SCALE_UNITLESS_NO_NAME_UM` × 2 |
| PHerc0009B | `AXES_UNIT_MISSING` × 3, `SCALE_IS_UNIT` × 3, `SCALE_UNITLESS_NO_NAME_UM` × 1 |
| PHerc0814 | `SCALE_UNITLESS_NO_NAME_UM` × 2, `AXES_UNIT_MISSING` × 2, `SCALE_IS_UNIT` × 2, `NO_METADATA` × 1 |
| PHerc0841 | `SCALE_UNITLESS_NO_NAME_UM` × 2, `AXES_UNIT_MISSING` × 2, `SCALE_IS_UNIT` × 2 |
| PHerc0846A | `SCALE_UNITLESS_NO_NAME_UM` × 2, `AXES_UNIT_MISSING` × 2, `SCALE_IS_UNIT` × 2 |
| PHerc1203 | `SCALE_UNITLESS_NO_NAME_UM` × 2, `AXES_UNIT_MISSING` × 2, `SCALE_IS_UNIT` × 2 |
| PHerc0343P | `AXES_UNIT_MISSING` × 2, `SCALE_IS_UNIT` × 2, `SCALE_UNITLESS_NO_NAME_UM` × 1 |
| PHerc1451 | `AXES_UNIT_MISSING` × 2, `SCALE_IS_UNIT` × 2, `SCALE_UNITLESS_NO_NAME_UM` × 1 |
| PHercMANBp | `AXES_UNIT_MISSING` × 2, `SCALE_IS_UNIT` × 2, `SCALE_UNITLESS_NO_NAME_UM` × 1 |
| PHerc0172 | `AXES_UNIT_MISSING` × 2, `SCALE_IS_UNIT` × 2 |
| PHerc1667 | `AXES_UNIT_MISSING` × 2, `SCALE_IS_UNIT` × 2 |
| PHerc0125 | `SCALE_UNITLESS_NO_NAME_UM` × 1, `AXES_UNIT_MISSING` × 1, `SCALE_IS_UNIT` × 1 |
| PHerc0175A | `SCALE_UNITLESS_NO_NAME_UM` × 1, `AXES_UNIT_MISSING` × 1, `SCALE_IS_UNIT` × 1 |
| PHerc0175B | `SCALE_UNITLESS_NO_NAME_UM` × 1, `AXES_UNIT_MISSING` × 1, `SCALE_IS_UNIT` × 1 |
| PHerc0211 | `SCALE_UNITLESS_NO_NAME_UM` × 1, `AXES_UNIT_MISSING` × 1, `SCALE_IS_UNIT` × 1 |
| PHerc0257 | `SCALE_UNITLESS_NO_NAME_UM` × 1, `AXES_UNIT_MISSING` × 1, `SCALE_IS_UNIT` × 1 |
| PHerc0268 | `SCALE_UNITLESS_NO_NAME_UM` × 1, `AXES_UNIT_MISSING` × 1, `SCALE_IS_UNIT` × 1 |
| PHerc0306B | `SCALE_UNITLESS_NO_NAME_UM` × 1, `AXES_UNIT_MISSING` × 1, `SCALE_IS_UNIT` × 1 |
| PHerc0332 | `SCALE_UNITLESS_NO_NAME_UM` × 1, `AXES_UNIT_MISSING` × 1, `SCALE_IS_UNIT` × 1 |
| PHerc0343 | `SCALE_UNITLESS_NO_NAME_UM` × 1, `AXES_UNIT_MISSING` × 1, `SCALE_IS_UNIT` × 1 |
| PHerc0358 | `SCALE_UNITLESS_NO_NAME_UM` × 1, `AXES_UNIT_MISSING` × 1, `SCALE_IS_UNIT` × 1 |
| PHerc0483A | `SCALE_UNITLESS_NO_NAME_UM` × 1, `AXES_UNIT_MISSING` × 1, `SCALE_IS_UNIT` × 1 |
| PHerc0483B | `SCALE_UNITLESS_NO_NAME_UM` × 1, `AXES_UNIT_MISSING` × 1, `SCALE_IS_UNIT` × 1 |
| PHerc0490A | `SCALE_UNITLESS_NO_NAME_UM` × 1, `AXES_UNIT_MISSING` × 1, `SCALE_IS_UNIT` × 1 |
| PHerc0490B | `SCALE_UNITLESS_NO_NAME_UM` × 1, `AXES_UNIT_MISSING` × 1, `SCALE_IS_UNIT` × 1 |
| PHerc0800 | `SCALE_UNITLESS_NO_NAME_UM` × 1, `AXES_UNIT_MISSING` × 1, `SCALE_IS_UNIT` × 1 |
| PHerc0813 | `SCALE_UNITLESS_NO_NAME_UM` × 1, `AXES_UNIT_MISSING` × 1, `SCALE_IS_UNIT` × 1 |
| PHerc0826 | `NO_METADATA` × 1, `AXES_UNIT_MISSING` × 1, `SCALE_IS_UNIT` × 1 |
| PHerc0846B | `SCALE_UNITLESS_NO_NAME_UM` × 1, `AXES_UNIT_MISSING` × 1, `SCALE_IS_UNIT` × 1 |
| PHerc1218 | `SCALE_UNITLESS_NO_NAME_UM` × 1, `AXES_UNIT_MISSING` × 1, `SCALE_IS_UNIT` × 1 |
| PHerc1299 | `SCALE_UNITLESS_NO_NAME_UM` × 1, `AXES_UNIT_MISSING` × 1, `SCALE_IS_UNIT` × 1 |
| PHerc1447 | `SCALE_UNITLESS_NO_NAME_UM` × 1, `AXES_UNIT_MISSING` × 1, `SCALE_IS_UNIT` × 1 |
| PHerc1545 | `SCALE_UNITLESS_NO_NAME_UM` × 1, `AXES_UNIT_MISSING` × 1, `SCALE_IS_UNIT` × 1 |
| PHercMAN5 | `SCALE_UNITLESS_NO_NAME_UM` × 1, `AXES_UNIT_MISSING` × 1, `SCALE_IS_UNIT` × 1 |
| PHercMANB | `SCALE_UNITLESS_NO_NAME_UM` × 1, `AXES_UNIT_MISSING` × 1, `SCALE_IS_UNIT` × 1 |
| PHerc0191 | `SCALE_UNITLESS_NO_NAME_UM` × 1, `NO_METADATA` × 1 |
| PHercParis3 | `AXES_UNIT_MISSING` × 1, `SCALE_IS_UNIT` × 1 |

## Negative results (checked, nothing found)

- Level ladders: **107** stores had parseable multiscale metadata and **none** showed a non-monotonic or non-integral level ladder.
- The z-axis/in-plane asymmetry of surface volumes (`[8.64, 8.64, 8.64] → [8.64, 17.28, 17.28] → …`) is uniform across the catalog and is recorded here as **expected**, not as a defect, so future audits do not re-file it.
- Origins that declare a non-S3 access root are skipped by design rather than reported missing (see `ALT_HOST_ORIGIN` in the JSONL).

## AXES_UNIT_MISSING — 65 stores

| # | store | sample | detail |
|---:|---|---|---|
| 1 | `PHerc0009B/volumes/20250521125136-8.640um-1.2m-116keV-masked.zarr/` | PHerc0009B | name 8.64µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 2 | `PHerc0009B/volumes/20250820154339-2.401um-0.3m-77keV-masked.zarr/` | PHerc0009B | name 2.401µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 3 | `PHerc0009B/volumes/20260319104112-2.401um-0.3m-77keV-masked.zarr/` | PHerc0009B | name 2.401µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 4 | `PHerc0125/volumes/20250821151825-9.362um-1.2m-113keV-masked.zarr/` | PHerc0125 | name 9.362µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 5 | `PHerc0139/volumes/20250728140407-9.362um-1.2m-113keV-masked.zarr/` | PHerc0139 | name 9.362µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 6 | `PHerc0139/volumes/20250820105138-2.403um-0.2m-77keV-masked.zarr/` | PHerc0139 | name 2.403µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 7 | `PHerc0139/volumes/20250822062710-2.403um-0.2m-77keV-masked.zarr/` | PHerc0139 | name 2.403µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 8 | `PHerc0139/volumes/20251107132835-9.362um-1.2m-113keV-pag0-masked.zarr/` | PHerc0139 | name 9.362µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 9 | `PHerc0139/volumes/20251107135911-9.362um-1.2m-113keV-pag50-masked.zarr/` | PHerc0139 | name 9.362µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 10 | `PHerc0139/volumes/20260102150214-2.399um-0.2m-78keV-masked.zarr/` | PHerc0139 | name 2.399µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 11 | `PHerc0139/volumes/20260319133050-2.403um-0.2m-77keV-masked.zarr/` | PHerc0139 | name 2.403µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 12 | `PHerc0139/volumes/20260319133554-2.403um-0.2m-77keV-masked.zarr/` | PHerc0139 | name 2.403µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 13 | `PHerc0139/volumes/20260413113053-1.129um-0.2m-59keV-masked.zarr/` | PHerc0139 | name 1.129µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 14 | `PHerc0172/volumes/20241024131838-7.910um-53keV-masked.zarr/` | PHerc0172 | name 7.91µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 15 | `PHerc0172/volumes/20241024131839-7.910um-53keV-masked.zarr/` | PHerc0172 | name 7.91µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 16 | `PHerc0175A/volumes/20250521115057-8.640um-1.2m-116keV-masked.zarr/` | PHerc0175A | name 8.64µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 17 | `PHerc0175B/volumes/20250521125822-8.640um-1.2m-116keV-masked.zarr/` | PHerc0175B | name 8.64µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 18 | `PHerc0211/volumes/20250821151803-9.362um-1.2m-113keV-masked.zarr/` | PHerc0211 | name 9.362µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 19 | `PHerc0257/volumes/20250821151750-9.362um-1.2m-113keV-masked.zarr/` | PHerc0257 | name 9.362µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 20 | `PHerc0268/volumes/20251110183117-8.640um-1.2m-116keV-masked.zarr/` | PHerc0268 | name 8.64µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 21 | `PHerc0306B/volumes/20250521133212-8.640um-1.2m-116keV-masked.zarr/` | PHerc0306B | name 8.64µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 22 | `PHerc0332/volumes/20251211183505-2.399um-0.2m-78keV-masked.zarr/` | PHerc0332 | name 2.399µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 23 | `PHerc0343/volumes/20250521140437-8.640um-1.2m-116keV-masked.zarr/` | PHerc0343 | name 8.64µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 24 | `PHerc0343P/volumes/20250521134555-8.640um-1.2m-116keV-masked.zarr/` | PHerc0343P | name 8.64µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 25 | `PHerc0343P/volumes/20260304131111-2.215um-0.4m-111keV-masked.zarr/` | PHerc0343P | name 2.215µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 26 | `PHerc0358/volumes/20250821151737-9.362um-1.2m-113keV-masked.zarr/` | PHerc0358 | name 9.362µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 27 | `PHerc0483A/volumes/20250521140913-8.640um-1.2m-116keV-masked.zarr/` | PHerc0483A | name 8.64µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 28 | `PHerc0483B/volumes/20251124083638-8.640um-1.2m-116keV-masked.zarr/` | PHerc0483B | name 8.64µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 29 | `PHerc0490A/volumes/20250521151210-8.640um-1.2m-116keV-masked.zarr/` | PHerc0490A | name 8.64µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 30 | `PHerc0490B/volumes/20250521151215-8.640um-1.2m-116keV-masked.zarr/` | PHerc0490B | name 8.64µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 31 | `PHerc0500P2/volumes/20250526151718-2.215um-0.4m-111keV-masked.zarr/` | PHerc0500P2 | name 2.215µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 32 | `PHerc0500P2/volumes/20250528085330-4.317um-1.2m-111keV-masked.zarr/` | PHerc0500P2 | name 4.317µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 33 | `PHerc0500P2/volumes/20250820143440-9.362um-1.2m-113keV-masked.zarr/` | PHerc0500P2 | name 9.362µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 34 | `PHerc0500P2/volumes/20250821110041-0.550um-0.1m-65keV-masked.zarr/` | PHerc0500P2 | name 0.55µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 35 | `PHerc0800/volumes/20250521135224-8.640um-1.2m-116keV-masked.zarr/` | PHerc0800 | name 8.64µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 36 | `PHerc0813/volumes/20250821151723-9.362um-1.2m-113keV-masked.zarr/` | PHerc0813 | name 9.362µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 37 | `PHerc0814/volumes/20250804134230-9.362um-1.2m-113keV-masked.zarr/` | PHerc0814 | name 9.362µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 38 | `PHerc0814/volumes/20260309142202-2.399um-0.2m-78keV-masked.zarr/` | PHerc0814 | name 2.399µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 39 | `PHerc0826/volumes/20250821151701-9.362um-1.2m-113keV-masked.zarr/` | PHerc0826 | name 9.362µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 40 | `PHerc0841/volumes/20250821151531-9.366um-1.2m-113keV-masked.zarr/` | PHerc0841 | name 9.366µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| … | 25 more in the JSONL results | | |

## SCALE_IS_UNIT — 65 stores

| # | store | sample | detail |
|---:|---|---|---|
| 1 | `PHerc0009B/volumes/20250521125136-8.640um-1.2m-116keV-masked.zarr/` | PHerc0009B | name 8.64µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 2 | `PHerc0009B/volumes/20250820154339-2.401um-0.3m-77keV-masked.zarr/` | PHerc0009B | name 2.401µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 3 | `PHerc0009B/volumes/20260319104112-2.401um-0.3m-77keV-masked.zarr/` | PHerc0009B | name 2.401µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 4 | `PHerc0125/volumes/20250821151825-9.362um-1.2m-113keV-masked.zarr/` | PHerc0125 | name 9.362µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 5 | `PHerc0139/volumes/20250728140407-9.362um-1.2m-113keV-masked.zarr/` | PHerc0139 | name 9.362µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 6 | `PHerc0139/volumes/20250820105138-2.403um-0.2m-77keV-masked.zarr/` | PHerc0139 | name 2.403µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 7 | `PHerc0139/volumes/20250822062710-2.403um-0.2m-77keV-masked.zarr/` | PHerc0139 | name 2.403µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 8 | `PHerc0139/volumes/20251107132835-9.362um-1.2m-113keV-pag0-masked.zarr/` | PHerc0139 | name 9.362µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 9 | `PHerc0139/volumes/20251107135911-9.362um-1.2m-113keV-pag50-masked.zarr/` | PHerc0139 | name 9.362µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 10 | `PHerc0139/volumes/20260102150214-2.399um-0.2m-78keV-masked.zarr/` | PHerc0139 | name 2.399µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 11 | `PHerc0139/volumes/20260319133050-2.403um-0.2m-77keV-masked.zarr/` | PHerc0139 | name 2.403µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 12 | `PHerc0139/volumes/20260319133554-2.403um-0.2m-77keV-masked.zarr/` | PHerc0139 | name 2.403µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 13 | `PHerc0139/volumes/20260413113053-1.129um-0.2m-59keV-masked.zarr/` | PHerc0139 | name 1.129µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 14 | `PHerc0172/volumes/20241024131838-7.910um-53keV-masked.zarr/` | PHerc0172 | name 7.91µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 15 | `PHerc0172/volumes/20241024131839-7.910um-53keV-masked.zarr/` | PHerc0172 | name 7.91µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 16 | `PHerc0175A/volumes/20250521115057-8.640um-1.2m-116keV-masked.zarr/` | PHerc0175A | name 8.64µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 17 | `PHerc0175B/volumes/20250521125822-8.640um-1.2m-116keV-masked.zarr/` | PHerc0175B | name 8.64µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 18 | `PHerc0211/volumes/20250821151803-9.362um-1.2m-113keV-masked.zarr/` | PHerc0211 | name 9.362µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 19 | `PHerc0257/volumes/20250821151750-9.362um-1.2m-113keV-masked.zarr/` | PHerc0257 | name 9.362µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 20 | `PHerc0268/volumes/20251110183117-8.640um-1.2m-116keV-masked.zarr/` | PHerc0268 | name 8.64µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 21 | `PHerc0306B/volumes/20250521133212-8.640um-1.2m-116keV-masked.zarr/` | PHerc0306B | name 8.64µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 22 | `PHerc0332/volumes/20251211183505-2.399um-0.2m-78keV-masked.zarr/` | PHerc0332 | name 2.399µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 23 | `PHerc0343/volumes/20250521140437-8.640um-1.2m-116keV-masked.zarr/` | PHerc0343 | name 8.64µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 24 | `PHerc0343P/volumes/20250521134555-8.640um-1.2m-116keV-masked.zarr/` | PHerc0343P | name 8.64µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 25 | `PHerc0343P/volumes/20260304131111-2.215um-0.4m-111keV-masked.zarr/` | PHerc0343P | name 2.215µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 26 | `PHerc0358/volumes/20250821151737-9.362um-1.2m-113keV-masked.zarr/` | PHerc0358 | name 9.362µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 27 | `PHerc0483A/volumes/20250521140913-8.640um-1.2m-116keV-masked.zarr/` | PHerc0483A | name 8.64µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 28 | `PHerc0483B/volumes/20251124083638-8.640um-1.2m-116keV-masked.zarr/` | PHerc0483B | name 8.64µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 29 | `PHerc0490A/volumes/20250521151210-8.640um-1.2m-116keV-masked.zarr/` | PHerc0490A | name 8.64µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 30 | `PHerc0490B/volumes/20250521151215-8.640um-1.2m-116keV-masked.zarr/` | PHerc0490B | name 8.64µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 31 | `PHerc0500P2/volumes/20250526151718-2.215um-0.4m-111keV-masked.zarr/` | PHerc0500P2 | name 2.215µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 32 | `PHerc0500P2/volumes/20250528085330-4.317um-1.2m-111keV-masked.zarr/` | PHerc0500P2 | name 4.317µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 33 | `PHerc0500P2/volumes/20250820143440-9.362um-1.2m-113keV-masked.zarr/` | PHerc0500P2 | name 9.362µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 34 | `PHerc0500P2/volumes/20250821110041-0.550um-0.1m-65keV-masked.zarr/` | PHerc0500P2 | name 0.55µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 35 | `PHerc0800/volumes/20250521135224-8.640um-1.2m-116keV-masked.zarr/` | PHerc0800 | name 8.64µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 36 | `PHerc0813/volumes/20250821151723-9.362um-1.2m-113keV-masked.zarr/` | PHerc0813 | name 9.362µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 37 | `PHerc0814/volumes/20250804134230-9.362um-1.2m-113keV-masked.zarr/` | PHerc0814 | name 9.362µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 38 | `PHerc0814/volumes/20260309142202-2.399um-0.2m-78keV-masked.zarr/` | PHerc0814 | name 2.399µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 39 | `PHerc0826/volumes/20250821151701-9.362um-1.2m-113keV-masked.zarr/` | PHerc0826 | name 9.362µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 40 | `PHerc0841/volumes/20250821151531-9.366um-1.2m-113keV-masked.zarr/` | PHerc0841 | name 9.366µm; scale0=[1.0, 1.0, 1.0]; axes have no unit |
| … | 25 more in the JSONL results | | |

## SCALE_UNITLESS_NO_NAME_UM — 42 stores

| # | store | sample | detail |
|---:|---|---|---|
| 1 | `PHerc0009B/representations/predictions/surfaces/20260319104112-surface-20260413222639-surface-m7-L2-th0.2.zarr/` | PHerc0009B | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 2 | `PHerc0125/representations/predictions/surfaces/20250821151825-surface-20260413222639-surface-m7-L0-th0.2.zarr/` | PHerc0125 | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 3 | `PHerc0139/representations/predictions/surfaces/20250728140407-surface-20250701154204-surface-recto-090.zarr/` | PHerc0139 | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 4 | `PHerc0139/representations/predictions/surfaces/20250728140407-surface-20260413222639-surface-m7-L0-th0.2.zarr/` | PHerc0139 | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 5 | `PHerc0175A/representations/predictions/surfaces/20250521115057-surface-20260413222639-surface-m7-L0-th0.2.zarr/` | PHerc0175A | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 6 | `PHerc0175B/representations/predictions/surfaces/20250521125822-surface-20260413222639-surface-m7-L0-th0.2.zarr/` | PHerc0175B | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 7 | `PHerc0191/representations/predictions/surfaces/20250821151635-surface-20260413222639-surface-m7-L0-th0.2.zarr/` | PHerc0191 | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 8 | `PHerc0211/representations/predictions/surfaces/20250821151803-surface-20260413222639-surface-m7-L0-th0.2.zarr/` | PHerc0211 | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 9 | `PHerc0257/representations/predictions/surfaces/20250821151750-surface-20260413222639-surface-m7-L0-th0.2.zarr/` | PHerc0257 | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 10 | `PHerc0268/representations/predictions/surfaces/20251110183117-surface-20260413222639-surface-m7-L0-th0.2.zarr/` | PHerc0268 | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 11 | `PHerc0306B/representations/predictions/surfaces/20250521133212-surface-20260413222639-surface-m7-L0-th0.2.zarr/` | PHerc0306B | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 12 | `PHerc0332/representations/predictions/surfaces/20251211183505-surface-20260413222639-surface-m7-L2-th0.2.zarr/` | PHerc0332 | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 13 | `PHerc0343/representations/predictions/surfaces/20250521140437-surface-20260413222639-surface-m7-L0-th0.2.zarr/` | PHerc0343 | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 14 | `PHerc0343P/representations/predictions/surfaces/20260304131111-surface-20260413222639-surface-m7-L2-th0.2.zarr/` | PHerc0343P | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 15 | `PHerc0358/representations/predictions/surfaces/20250821151737-surface-20260413222639-surface-m7-L0-th0.2.zarr/` | PHerc0358 | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 16 | `PHerc0483A/representations/predictions/surfaces/20250521140913-surface-20260413222639-surface-m7-L0-th0.2.zarr/` | PHerc0483A | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 17 | `PHerc0483B/representations/predictions/surfaces/20251124083638-surface-20260413222639-surface-m7-L0-th0.2.zarr/` | PHerc0483B | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 18 | `PHerc0490A/representations/predictions/surfaces/20250521151210-surface-20260413222639-surface-m7-L0-th0.2.zarr/` | PHerc0490A | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 19 | `PHerc0490B/representations/predictions/surfaces/20250521151215-surface-20260413222639-surface-m7-L0-th0.2.zarr/` | PHerc0490B | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 20 | `PHerc0500P2/representations/predictions/surfaces/20250526151718-surface-20260413222639-surface-m7-L2-th0.2.zarr/` | PHerc0500P2 | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 21 | `PHerc0500P2/representations/predictions/surfaces/20250820143440-surface-20260413222639-surface-m7-L0-th0.2.zarr/` | PHerc0500P2 | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 22 | `PHerc0800/representations/predictions/surfaces/20250521135224-surface-20260413222639-surface-m7-L0-th0.2.zarr/` | PHerc0800 | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 23 | `PHerc0813/representations/predictions/surfaces/20250821151723-surface-20260413222639-surface-m7-L0-th0.2.zarr/` | PHerc0813 | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 24 | `PHerc0814/representations/predictions/surfaces/20250804134230-surface-20260413222639-surface-m7-L0-th0.2.zarr/` | PHerc0814 | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 25 | `PHerc0814/representations/predictions/surfaces/20260309142202-surface-20260413222639-surface-m7-L2-th0.2.zarr/` | PHerc0814 | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 26 | `PHerc0841/representations/predictions/surfaces/20250821151531-surface-20260413222639-surface-m7-L0-th0.2.zarr/` | PHerc0841 | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 27 | `PHerc0841/representations/predictions/surfaces/20260319124803-surface-20260413222639-surface-m7-L2-th0.2.zarr/` | PHerc0841 | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 28 | `PHerc0846A/representations/predictions/surfaces/20250728152254-surface-20260413222639-surface-m7-L0-th0.2.zarr/` | PHerc0846A | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 29 | `PHerc0846A/representations/predictions/surfaces/20260319102732-surface-20260413222639-surface-m7-L2-th0.2.zarr/` | PHerc0846A | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 30 | `PHerc0846B/representations/predictions/surfaces/20250804142305-surface-20260413222639-surface-m7-L0-th0.2.zarr/` | PHerc0846B | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 31 | `PHerc1203/representations/predictions/surfaces/20250820131727-surface-20260413222639-surface-m7-L0-th0.2.zarr/` | PHerc1203 | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 32 | `PHerc1203/representations/predictions/surfaces/20260319130212-surface-20260413222639-surface-m7-L2-th0.2.zarr/` | PHerc1203 | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 33 | `PHerc1218/representations/predictions/surfaces/20250521120456-surface-20260413222639-surface-m7-L0-th0.2.zarr/` | PHerc1218 | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 34 | `PHerc1299/representations/predictions/surfaces/20260309130042-surface-20260413222639-surface-m7-L2-th0.2.zarr/` | PHerc1299 | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 35 | `PHerc1447/representations/predictions/surfaces/20250521151220-surface-20260413222639-surface-m7-L0-th0.2.zarr/` | PHerc1447 | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 36 | `PHerc1451/representations/predictions/surfaces/20260319101107-surface-20260413222639-surface-m7-L2-th0.2.zarr/` | PHerc1451 | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 37 | `PHerc1545/representations/predictions/surfaces/20250821151648-surface-20260413222639-surface-m7-L0-th0.2.zarr/` | PHerc1545 | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 38 | `PHercMAN5/representations/predictions/surfaces/20260311104824-surface-20260413222639-surface-m7-L2-th0.2.zarr/` | PHercMAN5 | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 39 | `PHercMANB/representations/predictions/surfaces/20260323091048-surface-20260413222639-surface-m7-L2-th0.2.zarr/` | PHercMANB | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| 40 | `PHercMANBp/representations/predictions/surfaces/20251216152116-surface-20260413222639-surface-m7-L2-th0.2.zarr/` | PHercMANBp | scale0=[1.0, 1.0, 1.0]; axes have no unit |
| … | 2 more in the JSONL results | | |

## NO_METADATA — 3 stores

| # | store | sample | detail |
|---:|---|---|---|
| 1 | `PHerc0191/volumes/20250821151635-9.362um-1.2m-113keV-masked.zarr/` | PHerc0191 | name 9.362µm |
| 2 | `PHerc0814/volumes/20260521123630-1.129um-0.2m-59keV-masked.zarr/` | PHerc0814 | name 1.129µm |
| 3 | `PHerc0826/representations/predictions/surfaces/20250821151701-surface-20260413222639-surface-m7-L0-th0.2.zarr/` | PHerc0826 |  |
