from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import fix_omezarr_scale as fix


def plan_entry(**over):
    entry = {
        "path": "PHerc0009B/volumes/20250521125136-8.640um-1.2m-116keV-masked.zarr",
        "status": "PLAN",
        "manifest_pitch_um": 8.64,
        "axes_now": [None, None, None],
        "axes_proposed": ["micrometer", "micrometer", "micrometer"],
        "scales_now": [[1.0, 1.0, 1.0], [2.0, 2.0, 2.0]],
        "scales_proposed": [[8.64, 8.64, 8.64], [17.28, 17.28, 17.28]],
        "level_ratios": [1.0, 2.0],
        "confidence": "DERIVED_UNVERIFIED",
    }
    entry.update(over)
    return entry


def v2_doc(units=(None, None, None), scales=((1.0, 1.0, 1.0), (2.0, 2.0, 2.0)), names=("z", "y", "x")):
    return {
        "multiscales": [{
            "version": "0.4",
            "axes": [{"name": n, "type": "space", "unit": u} for n, u in zip(names, units)],
            "datasets": [
                {"path": str(i), "coordinateTransformations": [{"type": "scale", "scale": list(s)}]}
                for i, s in enumerate(scales)
            ],
        }]
    }


class ApplyTest(unittest.TestCase):
    def test_fills_units_and_scales(self):
        doc = v2_doc()
        out, notes = fix.apply_fix(doc, "v2", plan_entry())
        axes = out["multiscales"][0]["axes"]
        self.assertTrue(all(a["unit"] == "micrometer" for a in axes))
        self.assertEqual(fix.scales_of(out["multiscales"][0]), [[8.64, 8.64, 8.64], [17.28, 17.28, 17.28]])
        self.assertIn("set unit on 3 axis/axes", notes)
        self.assertIn("rewrote scale on 2 level(s)", notes)

    def test_is_idempotent(self):
        doc = v2_doc()
        once, _ = fix.apply_fix(doc, "v2", plan_entry())
        twice, notes = fix.apply_fix(once, "v2", plan_entry(scales_now=[[8.64, 8.64, 8.64], [17.28, 17.28, 17.28]]))
        self.assertEqual(once, twice)
        self.assertIn("axes already carry units", notes)
        self.assertIn("scales already match the plan", notes)

    def test_refuses_when_the_store_changed_since_the_plan(self):
        doc = v2_doc(scales=((5.0, 5.0, 5.0), (10.0, 10.0, 10.0)))
        with self.assertRaises(ValueError) as ctx:
            fix.apply_fix(doc, "v2", plan_entry())
        self.assertIn("do not match the plan", str(ctx.exception))

    def test_refuses_on_a_level_count_mismatch(self):
        doc = v2_doc(scales=((1.0, 1.0, 1.0),))
        # plan has two levels, store declares one
        with self.assertRaises(ValueError) as ctx:
            fix.apply_fix(doc, "v2", plan_entry(scales_now=[[1.0, 1.0, 1.0]]))
        self.assertIn("levels but the store declares", str(ctx.exception))

    def test_refuses_without_a_multiscales_block(self):
        with self.assertRaises(ValueError):
            fix.apply_fix({}, "v2", plan_entry())

    def test_keeps_an_anisotropic_ladder(self):
        """A surface volume's z stays at the base pitch while the in-plane axes double."""
        doc = v2_doc(scales=((1.0, 1.0, 1.0), (1.0, 2.0, 2.0)))
        entry = plan_entry(
            scales_now=[[1.0, 1.0, 1.0], [1.0, 2.0, 2.0]],
            scales_proposed=[[2.401, 2.401, 2.401], [2.401, 4.802, 4.802]],
        )
        out, _ = fix.apply_fix(doc, "v2", entry)
        self.assertEqual(fix.scales_of(out["multiscales"][0]), [[2.401, 2.401, 2.401], [2.401, 4.802, 4.802]])

    def test_v3_reads_multiscales_from_attributes(self):
        ms = v2_doc()["multiscales"][0]
        doc = {"attributes": {"multiscales": [ms]}, "zarr_version": 3}
        out, _ = fix.apply_fix(doc, "v3", plan_entry())
        self.assertEqual(out["attributes"]["multiscales"][0]["axes"][0]["unit"], "micrometer")
        self.assertEqual(fix.scales_of(out["attributes"]["multiscales"][0])[0], [8.64, 8.64, 8.64])


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.plan_path = self.tmp / "plan.json"
        self.plan_path.write_text(json.dumps({"plans": [plan_entry()]}), encoding="utf-8")
        store = self.tmp / "store"
        store.mkdir()
        (store / ".zattrs").write_text(json.dumps(v2_doc()), encoding="utf-8")
        self.store = store

    def test_dry_run_writes_nothing(self):
        out_dir = self.tmp / "out"
        code = fix.main(["--plan", str(self.plan_path), "--path", plan_entry()["path"], "--local", str(self.store)])
        self.assertEqual(code, 0)
        self.assertFalse(out_dir.exists())

    def test_out_writes_the_corrected_file(self):
        out_dir = self.tmp / "out"
        code = fix.main(["--plan", str(self.plan_path), "--path", plan_entry()["path"],
                         "--local", str(self.store), "--out", str(out_dir)])
        self.assertEqual(code, 0)
        written = list(out_dir.glob("*"))
        self.assertEqual(len(written), 1)
        doc = json.loads(written[0].read_text(encoding="utf-8"))
        self.assertEqual(fix.scales_of(doc["multiscales"][0])[0], [8.64, 8.64, 8.64])

    def test_a_path_with_no_plan_is_rejected(self):
        code = fix.main(["--plan", str(self.plan_path), "--path", "not/in/the/plan.zarr", "--local", str(self.store)])
        self.assertEqual(code, 2)

    def test_a_precondition_failure_exits_three(self):
        store = self.tmp / "changed"
        store.mkdir()
        (store / ".zattrs").write_text(json.dumps(v2_doc(scales=((9.0, 9.0, 9.0), (18.0, 18.0, 18.0)))), encoding="utf-8")
        code = fix.main(["--plan", str(self.plan_path), "--path", plan_entry()["path"], "--local", str(store)])
        self.assertEqual(code, 3)


if __name__ == "__main__":
    unittest.main()
