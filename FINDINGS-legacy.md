# The legacy host: what the six fragment samples actually have

`dl.ash2txt.org` is not maintained - the maintainers said so in #1760 - so nothing below will be fixed.
It is documented anyway because for these six samples it is the **only** copy: the catalog lists them,
carries no volumes or segments for any of them, and points at this host through
`properties.legacy_data_url`. Fragments are training material, so "is the legacy copy usable" is a
question with a real audience.

Method: directory listings plus `.zattrs` / `zarr.json`, no chunk bytes, no data objects.
Command: `python contrib/probe-legacy/probe_legacy.py --out results_legacy.jsonl`
Evidence: `results_legacy.jsonl` (28 rows). Snapshot: 2026-10-04.

| family | sample | roots | all levels present | declares 6, has level 0 only | no `axes[].unit` |
|---|---|---:|---|---|---:|
| Frag1 | PHercParis2Fr47 | 4 | 4 | 0 | 4 |
| Frag2 | PHercParis2Fr143 | 4 | 4 | 0 | 4 |
| Frag3 | PHercParis1Fr34 | 4 | 2 | **2** | 4 |
| Frag4 | PHercParis1Fr39 | 4 | 4 | 0 | 4 |
| Frag5 | PHerc1667Cr1Fr3 | 4 | 4 | 0 | 4 |
| Frag6 | PHerc51Cr4Fr8 | 8 | 8 | 0 | 8 |
| | **total** | **28** | **26** | **2** | **28** |

Two things stand out.

**Every legacy root is unitless.** 28 of 28 carry no `axes[].unit` and a level-0 scale of `[1, 1, 1]`,
against 124 of 894 (14 %) on the canonical bucket. A reader that trusts OME metadata measures these
fragment volumes in voxels while the names state 3.24 µm, 7.91 µm and so on - the same class as #1957,
at four times the prevalence.

**The broken store is the one already reported, and it is not alone in its directory.** Frag3's 88 keV
store declares six levels in both `volumes_zarr/` and `volumes_standardized/`, and only `0/` exists; any
client asking for a coarser level gets a 404 rather than "this pyramid has one level". That is #1755,
reproduced here with a different tool and independently of the tool that reported it. The other 26 roots
- including Frag3's own 54 keV siblings - have all declared levels.

So the damage in this corner is bounded: one energy of one fragment is missing its pyramid, everything
else is present but unitless.

**And unlike the bucket, there is nothing to copy the pitch from.** For the 81 unitless stores the
catalog publishes, 77 have `properties.pixel_size_um` recorded in the manifest, which is what makes the
repair a metadata copy rather than a re-derivation. These six samples have no such entry: each carries
only `type`, `legacy_data_url`, `description` and one photo object, with no `pixel_size_um` anywhere in
the sample record. For the 28 legacy roots the file name (`3.24um`, `7.91um`, …) is the only place in the
catalog where the pitch appears, so anyone repairing them has to take the value from the name or from
the scan parameters documented outside the catalog. That is a materially weaker position than the
bucket's 77, and worth knowing before the host goes away.

The contrast inside the manifest is stark and reproducible: of the ten samples that carry a legacy URL,
the four scrolls (`/full-scrolls/`) all have a `pixel_size_um` recorded, and the six fragments
(`/fragments/`) have none. `python -m scroll_catalog_audit manifest` prints both lines.

The 10 declared-but-absent levels above are counted per root, not per level: each of the two affected
roots is missing levels 1 through 5.
