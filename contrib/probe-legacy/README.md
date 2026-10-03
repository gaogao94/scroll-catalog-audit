# probe-legacy

Metadata-only audit of the **legacy host** `dl.ash2txt.org`, for the six fragment samples the catalog
lists but does not publish: `PHercParis2Fr47` (Frag1), `PHercParis2Fr143` (Frag2), `PHercParis1Fr34`
(Frag3), `PHercParis1Fr39` (Frag4), `PHerc1667Cr1Fr3` (Frag5), `PHerc51Cr4Fr8` (Frag6).

Why it is separate from the catalog audit: the maintainers have said this host is no longer maintained
(#1760), so nothing here will be fixed - but for these six samples it is the **only** copy, and fragments
are training material. "Is the legacy copy usable, and does it carry the same defects" is therefore a
question with a real audience.

```bash
python probe_legacy.py --out results_legacy.jsonl     # resumable; metadata only, no chunk bytes
```

Five offline tests cover the parsing (`python -m unittest discover -s contrib/probe-legacy -p "test_*.py"`);
the network calls are stubbed, so they run anywhere.

Discovery walks the host's autoindex pages; only `.zattrs` / `zarr.json` and one listing per store are
fetched. Results: `results_legacy.jsonl` (28 roots) and the table in `FINDINGS-legacy.md`.

**What it found (2026-10-04):** 28 Zarr roots. All 28 carry **no `axes[].unit` and a level-0 scale of
`[1,1,1]`** - the same defect class as the catalog, at 100 % rather than 14 %. Twenty-six declare six
levels and have all six; **Frag3's 88 keV store, in both `volumes_zarr` and `volumes_standardized`,
declares six levels and has only level 0** - the case reported in #1755, reproduced here with a
different tool.
