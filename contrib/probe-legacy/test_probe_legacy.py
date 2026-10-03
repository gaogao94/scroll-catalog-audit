"""Offline tests for the legacy probe's parsing, with the network stubbed out.

`probe()` fetches `.zattrs` / `zarr.json` and lists the store root; both are replaced here so the tests
run without touching the host. The other two contrib tools have tests and this one did not, which also
made `unittest discover -s contrib/probe-legacy` exit 5 ("no tests ran") and look like a failure in the
weekly check.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe_legacy as probe  # noqa: E402


def stub(attrs=None, entries=(), v3=False):
    """Replace the two network calls with fixed answers."""
    def fake_fetch(url):
        if attrs is None:
            return None
        # A real .zattrs is a dict that *contains* multiscales, not the multiscales list itself.
        if v3:
            return {"attributes": {"multiscales": attrs}} if url.endswith("zarr.json") else None
        return {"multiscales": attrs} if url.endswith(".zattrs") else None

    def fake_listing(url):
        return list(entries)

    probe.fetch_json = fake_fetch
    probe.listing = fake_listing


MULTISCALES = [{
    "axes": [{"name": "z"}, {"name": "y"}, {"name": "x"}],
    "datasets": [
        {"path": "0", "coordinateTransformations": [{"type": "scale", "scale": [1.0, 1.0, 1.0]}]},
        {"path": "1"}, {"path": "2"}, {"path": "3"}, {"path": "4"}, {"path": "5"},
    ],
}]


class LegacyProbeTest(unittest.TestCase):
    def test_a_unitless_store_naming_a_pitch_is_flagged(self):
        stub(MULTISCALES, [".zattrs", ".zgroup", "0/"])
        rec = probe.probe("https://dl.ash2txt.org/fragments/Frag3/PHercParis1Fr34.volpkg/"
                          "volumes_zarr/88keV_3.24um_.zarr/")
        self.assertTrue(rec["has_metadata"])
        self.assertTrue(rec["unitless"])
        self.assertTrue(rec["unit_is_one"])
        self.assertEqual(rec["declared_levels"], 6)
        self.assertEqual(rec["levels_present"], ["0"])
        self.assertEqual(rec["levels_missing"], ["1", "2", "3", "4", "5"])

    def test_a_complete_store_reports_no_missing_levels(self):
        stub(MULTISCALES, ["0/", "1/", "2/", "3/", "4/", "5/"])
        rec = probe.probe("https://dl.ash2txt.org/fragments/Frag1/PHercParis2Fr47.volpkg/"
                          "volumes_zarr/54keV_3.24um_.zarr/")
        self.assertEqual(rec["levels_missing"], [])
        self.assertEqual(len(rec["levels_present"]), 6)

    def test_v3_metadata_is_read_from_attributes(self):
        stub(MULTISCALES, ["0/"], v3=True)
        rec = probe.probe("https://dl.ash2txt.org/fragments/Frag6/PHerc51Cr4Fr8.volpkg/x.zarr/")
        self.assertTrue(rec["has_metadata"])
        self.assertEqual(rec["declared_levels"], 6)
        self.assertEqual(rec["units"], [None, None, None])

    def test_no_metadata_is_reported_as_such(self):
        stub(None, [])
        rec = probe.probe("https://dl.ash2txt.org/fragments/Frag9/NOPE.volpkg/x.zarr/")
        self.assertFalse(rec["has_metadata"])
        self.assertEqual(rec["format"], "none")
        self.assertIsNone(rec["declared_levels"])

    def test_the_families_are_the_six_the_catalog_points_at(self):
        self.assertEqual([f[0] for f in probe.FAMILIES],
                         ["Frag1", "Frag2", "Frag3", "Frag4", "Frag5", "Frag6"])
        self.assertEqual(len({s for _, s in probe.FAMILIES}), 6)


if __name__ == "__main__":
    unittest.main()
