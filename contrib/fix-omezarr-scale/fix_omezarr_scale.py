#!/usr/bin/env python3
"""Write corrected OME-Zarr metadata for the stores with no physical scale.

The validator next door detects the defect; this produces the repair. For a store whose name states a
micrometre pitch but whose published metadata carries no `axes[].unit` and a level-0 `scale` of
`[1,1,1]`, the pitch is usually already recorded in the catalog manifest, so the fix is a metadata
edit rather than a re-render.

    python fix_omezarr_scale.py --plan SCALE_FIX_PLAN.json --path <store>            # print a diff
    python fix_omezarr_scale.py --plan SCALE_FIX_PLAN.json --path <store> --out DIR  # write the file

Nothing is sent anywhere: `--out` writes the corrected metadata to a directory for review, and the
caller uploads it with whatever tooling they already use to publish. That keeps credentials out of this
script and keeps the change reviewable.

Guards, because this edits published data:
  * dry run unless `--out` is given;
  * refuses when the store's current scales do not match the plan's `scales_now`, so a store that has
    been fixed or changed since the plan was made cannot be silently rewritten;
  * says so and does nothing when the fix is already in place.

Every proposed value comes from the plan, which was built from the manifest's own `pixel_size_um` and
the store's own level ratios - in particular it keeps a surface volume's anisotropic ladder (z
constant, in-plane doubling) instead of forcing an isotropic one.
"""

from __future__ import annotations

import argparse
import difflib
import gzip
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

USER_AGENT = {"User-Agent": "vesuvius-scale-repair/1.0"}
TOL = 1e-9


def close(a, b) -> bool:
    return isinstance(a, (int, float)) and isinstance(b, (int, float)) and abs(a - b) <= TOL


def same_scales(a, b) -> bool:
    if not isinstance(a, list) or not isinstance(b, list) or len(a) != len(b):
        return False
    return all(len(x) == len(y) and all(close(u, v) for u, v in zip(x, y)) for x, y in zip(a, b))


def _get(url: str):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=USER_AGENT), timeout=45) as r:
            body = r.read()
    except Exception:
        return None
    if body[:2] == b"\x1f\x8b":
        body = gzip.decompress(body)
    try:
        return json.loads(body.decode("utf-8"))
    except Exception:
        return None


def load_store_metadata(path: str, base: str, local: str | None):
    """Return (document, format, relative filename). v2 keeps multiscales in .zattrs, v3 in zarr.json."""
    if local:
        for name in (".zattrs", "zarr.json"):
            p = Path(local) / name
            if p.exists():
                return json.loads(p.read_text(encoding="utf-8")), ("v2" if name == ".zattrs" else "v3"), name
        return None, None, None
    quoted = urllib.parse.quote(path.rstrip("/"))
    for name, fmt in ((".zattrs", "v2"), ("zarr.json", "v3")):
        doc = _get(f"{base.rstrip('/')}/{quoted}/{name}")
        if isinstance(doc, dict):
            return doc, fmt, name
    return None, None, None


def multiscales_of(doc: dict, fmt: str):
    if fmt == "v2":
        return (doc.get("multiscales") or [None])[0]
    return ((doc.get("attributes") or {}).get("multiscales") or [None])[0]


def scales_of(ms: dict):
    out = []
    for ds in ms.get("datasets") or []:
        for t in ds.get("coordinateTransformations") or []:
            if isinstance(t, dict) and t.get("type") == "scale":
                out.append(t.get("scale"))
                break
        else:
            out.append(ds.get("scale"))
    return out


def apply_fix(doc: dict, fmt: str, plan: dict) -> tuple[dict, list[str]]:
    """Return (corrected document, notes). Raises ValueError on a precondition failure."""
    ms = multiscales_of(doc, fmt)
    if not isinstance(ms, dict):
        raise ValueError("store publishes no multiscales block")
    current = scales_of(ms)
    expected = plan.get("scales_now")
    if expected is not None and not same_scales(current, expected):
        raise ValueError(
            "the store's scales do not match the plan's scales_now, so it has changed since the plan "
            f"was made. live={current} plan={expected}"
        )
    proposed = plan.get("scales_proposed") or []
    datasets = ms.get("datasets") or []
    if proposed and len(proposed) != len(datasets):
        raise ValueError(f"plan has {len(proposed)} levels but the store declares {len(datasets)}")

    notes: list[str] = []
    axes = ms.get("axes") or []
    wanted_units = plan.get("axes_proposed") or []
    changed_units = 0
    for i, axis in enumerate(axes):
        if not isinstance(axis, dict):
            continue
        if axis.get("unit") is None and i < len(wanted_units) and wanted_units[i]:
            axis["unit"] = wanted_units[i]
            changed_units += 1
    if changed_units:
        notes.append(f"set unit on {changed_units} axis/axes")
    if not changed_units and all(isinstance(a, dict) and a.get("unit") for a in axes):
        notes.append("axes already carry units")

    changed_scales = 0
    for ds, want in zip(datasets, proposed):
        if not isinstance(ds, dict) or not want:
            continue
        for t in ds.get("coordinateTransformations") or []:
            if isinstance(t, dict) and t.get("type") == "scale":
                if not same_scales([t.get("scale")], [want]):
                    t["scale"] = list(want)
                    changed_scales += 1
                break
        else:
            ds.setdefault("scale", list(want))
            changed_scales += 1
    if changed_scales:
        notes.append(f"rewrote scale on {changed_scales} level(s)")
    else:
        notes.append("scales already match the plan")
    return doc, notes


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", required=True, help="SCALE_FIX_PLAN.json")
    ap.add_argument("--path", required=True, help="store path as recorded in the plan")
    ap.add_argument("--out", default=None, help="write the corrected metadata here (omit for a dry run)")
    ap.add_argument("--local", default=None, help="read the store from this local directory instead of a URL")
    args = ap.parse_args(argv)

    try:
        plan_doc = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"no plan file at {args.plan}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"plan file {args.plan} is not valid JSON: {exc}", file=sys.stderr)
        return 2
    plans = plan_doc.get("plans") if isinstance(plan_doc, dict) else plan_doc
    match = next((p for p in plans if p.get("path", "").rstrip("/") == args.path.rstrip("/")), None)
    if match is None:
        print(f"no plan entry for {args.path}", file=sys.stderr)
        return 2

    base = match.get("via") or "https://vesuvius-challenge-open-data.s3.amazonaws.com"
    doc, fmt, fname = load_store_metadata(args.path, base, args.local)
    if doc is None:
        print(f"could not read metadata for {args.path}", file=sys.stderr)
        return 2
    before = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False)

    try:
        corrected, notes = apply_fix(doc, fmt, match)
    except ValueError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 3

    after = json.dumps(corrected, indent=1, sort_keys=True, ensure_ascii=False)
    print(f"store      : {args.path}")
    print(f"format     : {fmt} ({fname})")
    print(f"pitch      : {match.get('manifest_pitch_um')} um  (confidence: {match.get('confidence')})")
    for n in notes:
        print(f"  - {n}")
    if after == before:
        print("nothing to do: the corrected document is identical to the published one")
        return 0

    diff = difflib.unified_diff(before.splitlines(), after.splitlines(),
                                fromfile=f"published/{fname}", tofile=f"corrected/{fname}", lineterm="")
    print("\n".join(diff))

    if args.out:
        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        target = out_dir / (Path(args.path.rstrip("/")).name + "." + fname.lstrip("."))
        target.write_text(json.dumps(corrected, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                          encoding="utf-8", newline="\n")
        print(f"\nwrote {target}")
    else:
        print("\n(dry run: pass --out DIR to write the corrected metadata)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
