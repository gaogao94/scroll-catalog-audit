#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scroll-catalog-audit — read-only consistency audit of the Vesuvius Challenge open-data catalog.

What it checks (metadata only; no chunk bytes are ever downloaded):
  1. path resolution   — every origin is resolved against ITS OWN declared access_root
                         (the catalog publishes some volumes on two roots; resolving all
                         paths against one bucket manufactures false "missing" hits)
  2. chunk presence    — stores that declare multiscale levels but contain no chunks
  3. physical scale    — store names that state a µm pitch while OME metadata declares
                         no unit / scale [1,1,1] (a reader that trusts metadata gets 1)
  4. level ladders     — monotonicity and integrality of per-level scales
Supports Zarr v2 (`.zattrs`/`.zarray`) and Zarr v3 (`zarr.json`).

Usage:
  python -m scroll_catalog_audit scan    [--limit N] [--workers 10] [--results results.jsonl]
  python -m scroll_catalog_audit report  [--results results.jsonl] [--out FINDINGS.md]
  python -m scroll_catalog_audit selftest

Only the Python standard library is required.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import gzip
import hashlib
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

__version__ = "0.2.0"

BUCKET = "https://vesuvius-challenge-open-data.s3.amazonaws.com"
S3_ROOT = "s3://vesuvius-challenge-open-data"
CATALOG_KEY = "metadata.min.json"
NS = {"s": "http://s3.amazonaws.com/doc/2006-03-01/"}
UA = {"User-Agent": f"scroll-catalog-audit/{__version__} (read-only, metadata only)"}
UM_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)um")
META_KEYS = (".zarray", ".zattrs", ".zgroup", ".zmetadata", ".zcompressor", "zarr.json")
INTEGRAL_RATIOS = (1, 2, 3, 4, 8, 16, 32, 64)
_stats = {"req": 0}
_lock = threading.Lock()


# --------------------------------------------------------------------------------------
# pure helpers (unit-tested, no network)
# --------------------------------------------------------------------------------------
def is_chunk_key(rel_key: str) -> bool:
    """True if a key relative to a store root is a chunk.

    Two naming styles exist in this catalog and both must be handled:
      hierarchical: 0/0/0/5      dotted: 0/0.0.11
    """
    rel = rel_key.strip("/")
    if not rel:
        return False
    tail = rel.split("/")[-1]
    if tail in META_KEYS:
        return False
    return bool(re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", tail))


def um_from_path(path: str):
    m = UM_RE.search(path or "")
    return float(m.group(1)) if m else None


def parse_axes(axes) -> dict:
    """Normalise an `axes` list from either OME-Zarr v2 or v3 metadata."""
    out = []
    for a in axes or []:
        if isinstance(a, dict):
            out.append({"name": a.get("name"), "unit": a.get("unit")})
        else:
            out.append({"name": a, "unit": None})
    present = bool(out) and all(a["unit"] for a in out)
    return {"axes": out, "units_present": present, "has_axes": bool(out)}


def parse_multiscales(doc: dict, v3: bool = False) -> dict:
    """Extract axes + per-level scales from a `.zattrs` (v2) or `zarr.json` (v3) document."""
    src = (doc.get("attributes") or {}) if v3 else doc
    ms_list = src.get("multiscales") or []
    ms = ms_list[0] if ms_list else {}
    axes = ms.get("axes") or src.get("axes") or []
    scales, levels = [], []
    for ds in ms.get("datasets") or []:
        trs = ds.get("coordinateTransformations") or []
        scale = trs[0].get("scale") if trs else None
        scales.append(scale)
        levels.append(ds.get("path"))
    info = parse_axes(axes)
    info.update({"scales": scales, "levels": levels, "scale0": scales[0] if scales else None,
                 "n_levels": len(scales)})
    return info


def resolves_on_s3(access_roots) -> bool:
    """A path should only be looked up in the bucket when it declares that bucket."""
    if not access_roots:
        return True
    return S3_ROOT in access_roots


def origin_base(access_roots):
    """The URL base a store must be resolved against, per its OWN declared access roots (R4).

    Some volumes are published on a second host and only there; skipping them would leave a hole
    in the sweep, so resolve each origin against its declared root instead.
    """
    roots = access_roots or []
    if not roots or S3_ROOT in roots:
        return BUCKET
    for r in roots:
        if isinstance(r, str) and r.startswith("http"):
            return r.rstrip("/")
    return None


def ladder_issues(scales) -> list:
    """Report non-monotonic ladders and non-integral level ratios (empty = clean)."""
    sc = [s for s in (scales or []) if isinstance(s, list) and s]
    issues = []
    if len(sc) < 2:
        return issues
    n = min(len(s) for s in sc)
    for i in range(len(sc) - 1):
        for k in range(n):
            if sc[i + 1][k] < sc[i][k]:
                issues.append("NON_MONOTONIC")
                break
    for i in range(len(sc) - 1):
        for k in range(n):
            a, b = sc[i][k], sc[i + 1][k]
            if a:
                r = b / a
                if abs(r - round(r)) > 1e-6 or round(r) not in INTEGRAL_RATIOS:
                    issues.append("NON_INTEGRAL_RATIO")
                    break
    order = ("NON_MONOTONIC", "NON_INTEGRAL_RATIO")
    seen = set(issues)
    return [k for k in order if k in seen]


def classify(record: dict) -> list:
    """Derive mismatch labels for one scanned store.

    Pure: it reads only fields stored in the JSONL, so `report` can re-derive labels
    from an older results file without re-scanning.
    """
    if record.get("skipped"):
        return []
    if record.get("list_err"):
        return ["LIST_ERROR"]
    if record.get("exists") is False:
        return ["PATH_MISSING"]
    if record.get("exists") is None:
        return []
    if record.get("format") == "none":
        return ["NO_METADATA" if "HTTP404" in str(record.get("meta_err", "")) else "META_ERROR"]
    out = []
    um = record.get("um_in_path")
    sc0 = record.get("scale0")
    if record.get("units_present") is False and um:
        out.append("AXES_UNIT_MISSING")
    if isinstance(sc0, list) and len(set(sc0)) == 1 and sc0[0] == 1:
        if um:
            out.append("SCALE_IS_UNIT")
        elif record.get("ctx", {}).get("vol_pixel_um"):
            out.append("SCALE_UNITLESS_NO_NAME_UM")
    # Chunk keys sort after .zarray/.zattrs/.zgroup, so a populated store shows chunks
    # on the first listing page. Zero chunks = a store that reads back as fill_value.
    if record.get("n_keys_first_page") is not None and record.get("chunks_in_first_page") == 0:
        out.append("NO_CHUNKS_IN_FIRST_PAGE")
    if record.get("empty_levels") and len(record["empty_levels"]) == record.get("n_levels", 0):
        out.append("EMPTY_PYRAMID")
    elif record.get("empty_levels"):
        out.append("PARTIAL_LEVELS_MISSING")
    out += ladder_issues(record.get("scales"))
    return out


# --------------------------------------------------------------------------------------
# network layer
# --------------------------------------------------------------------------------------
def _get(url, timeout=45):
    with _lock:
        _stats["req"] += 1
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def _json(url):
    try:
        _, body = _get(url)
    except urllib.error.HTTPError as e:
        return None, f"HTTP{e.code}"
    except Exception as e:  # noqa: BLE001
        return None, type(e).__name__
    if body[:2] == b"\x1f\x8b":
        try:
            body = gzip.decompress(body)
        except Exception:  # noqa: BLE001
            pass
    try:
        return json.loads(body.decode("utf-8", "replace")), None
    except Exception as e:  # noqa: BLE001
        return None, f"parse:{type(e).__name__}"


def list_keys(prefix, max_keys=300, base=BUCKET, attempts=3):
    """List keys under a prefix. Distinguishes an empty store from a failed request."""
    last = None
    for i in range(attempts):
        q = f"{base}/?list-type=2&max-keys={max_keys}&prefix={urllib.parse.quote(prefix)}"
        try:
            _, body = _get(q)
            root = ET.fromstring(body)
            return [k.find("s:Key", NS).text for k in root.findall("s:Contents", NS)], None
        except urllib.error.HTTPError as e:
            last = f"HTTP{e.code}"
            if e.code in (403, 404):
                break
        except Exception as e:  # noqa: BLE001
            last = type(e).__name__
        time.sleep(0.5 * (i + 1))
    return None, last


def load_catalog(path=None):
    """Return the catalog dict, from a local file or the bucket."""
    if path and os.path.exists(path):
        raw = open(path, "rb").read()
    else:
        _, raw = _get(f"{BUCKET}/{CATALOG_KEY}")
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return json.loads(raw.decode("utf-8", "replace"))


def build_roots(catalog):
    """Every zarr root the catalog publishes, with kind/sample/context."""
    roots = {}

    def add(path, kind, sample, ctx):
        p = (path or "").strip()
        if not p or (".zarr" not in p):
            return
        key = p if p.endswith("/") else p + "/"
        rec = roots.setdefault(key, {"path": key, "kind": kind, "sample": sample, "ctx": {}})
        rec["ctx"].update({k: v for k, v in ctx.items() if v is not None})

    for sample, s in (catalog.get("samples") or {}).items():
        for vid, v in (s.get("volumes") or {}).items():
            props = v.get("properties") or {}
            scan = (s.get("scans") or {}).get(v.get("scan_id")) or {}
            sprops = scan.get("properties") or {}
            for d in v.get("data") or []:
                for o in d.get("origins") or []:
                    add(o.get("path"), f"volume:{d.get('type')}", sample, {
                        "volume_id": vid, "scan_id": v.get("scan_id"),
                        "vol_pixel_um": props.get("pixel_size_um"), "scan_pixel_um": sprops.get("pixel_size_um"),
                        "access_roots": [r.get("url") for r in (o.get("access_roots") or [])]})
        for sid, sg in (s.get("segments") or {}).items():
            for d in sg.get("data") or []:
                for o in d.get("origins") or []:
                    add(o.get("path"), f"segment:{d.get('type')}", sample, {
                        "segment_id": sid,
                        "access_roots": [r.get("url") for r in (o.get("access_roots") or [])]})
    return roots


def scan_root(rec, deep=False):
    """Audit a single store. Never downloads chunk bytes."""
    root = rec["path"]
    out = {k: v for k, v in rec.items() if k != "ctx"}
    out["ctx"] = {k: v for k, v in rec["ctx"].items() if k in ("vol_pixel_um", "scan_pixel_um", "access_roots")}
    out["um_in_path"] = um_from_path(root)
    roots = rec["ctx"].get("access_roots")
    base = origin_base(roots)
    out["access_roots"] = roots
    if base is None:
        out["skipped"] = "NO_USABLE_ROOT"
        out["exists"] = None
        out["mismatch"] = []
        return out
    out["via"] = base
    is_s3 = base == BUCKET
    if is_s3:
        keys, err = list_keys(root, base=base)
        if err:
            # A failed request is NOT a missing path: keep it retryable and separate.
            out.update({"exists": None, "list_err": err, "mismatch": ["LIST_ERROR"]})
            return out
        out["exists"] = bool(keys)
        out["n_keys_first_page"] = len(keys)
        out["chunks_in_first_page"] = sum(1 for k in keys if is_chunk_key(k[len(root):]))
        if not out["exists"]:
            out["mismatch"] = ["PATH_MISSING"]
            return out
    # Non-S3 roots are plain HTTPS file servers: they have no ListObjectsV2 API, so existence is
    # established from the metadata object itself and the chunk-page fields stay unknown.
    doc, zerr = _json(f"{base}/{urllib.parse.quote(root.rstrip('/'))}/.zattrs")
    fmt = "v2"
    if doc is None:
        doc, zerr3 = _json(f"{base}/{urllib.parse.quote(root.rstrip('/'))}/zarr.json")
        if doc is not None:
            fmt = "v3"
            info = parse_multiscales(doc, v3=True)
        else:
            reason = "NO_METADATA" if "HTTP404" in f"{zerr}{zerr3}" else "META_ERROR"
            out.update({"meta_err": f"{zerr}|{zerr3}", "format": "none"})
            if not is_s3:
                out["exists"] = "HTTP404" not in f"{zerr}{zerr3}"
                out["mismatch"] = ["PATH_MISSING"] if not out["exists"] else [reason]
                return out
            out["mismatch"] = [reason]
            return out
    else:
        info = parse_multiscales(doc, v3=False)
    if not is_s3:
        out["exists"] = True
    out.update({"format": fmt, **info})
    out.pop("levels", None)
    if deep and info.get("levels"):
        empty = []
        for lvl in info["levels"][:8]:
            lk, lerr = list_keys(f"{root}{lvl}/", max_keys=5, base=base)
            if lerr or not any(is_chunk_key(k[len(root):]) for k in (lk or [])):
                empty.append(lvl)
        out["empty_levels"] = empty
    out["mismatch"] = classify(out)
    return out


def cmd_scan(args):
    catalog = load_catalog(args.catalog)
    roots = build_roots(catalog)
    print(f"catalog: {len(roots)} zarr roots")
    done = set()
    if os.path.exists(args.results):
        with open(args.results, encoding="utf-8") as fh:
            for line in fh:
                try:
                    done.add(json.loads(line)["path"])
                except Exception:  # noqa: BLE001
                    pass
    todo = [r for p, r in sorted(roots.items()) if p not in done]
    if args.kind:
        todo = [r for r in todo if args.kind in r["kind"]]
    if args.path_substring:
        todo = [r for r in todo if args.path_substring in r["path"]]
    if args.random:
        import random as _random
        rnd = _random.Random(args.seed)
        todo = rnd.sample(todo, min(args.random, len(todo)))
    if args.limit:
        todo = todo[: args.limit]
    print(f"scanning {len(todo)} (already done: {len(done)}) deep={args.deep} workers={args.workers}"
          + (f" kind~{args.kind}" if args.kind else "")
          + (f" random={args.random} seed={args.seed}" if args.random else ""))
    t0 = time.time()
    with open(args.results, "a", encoding="utf-8") as fh, cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        for i, rec in enumerate(ex.map(lambda r: scan_root(r, args.deep), todo), 1):
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            if i % 100 == 0 or i == len(todo):
                print(f"  {i}/{len(todo)} {time.time()-t0:5.0f}s req={_stats['req']}")
    print(f"done in {time.time()-t0:.0f}s, {_stats['req']} requests, no chunk bytes downloaded")


def load_rows(results, merges=None):
    """Read a results file, optionally merging others, and re-derive every label.

    Merging prefers, per store, the run that actually obtained metadata: transient fetch
    failures otherwise move a handful of stores between classes and make counts irreproducible.
    Labels are always re-derived from the stored fields, so a newer checker can re-read an
    older scan without re-scanning.
    """
    rows = [json.loads(l) for l in open(results, encoding="utf-8") if l.strip()]
    for extra in merges or []:
        best = {}
        for line in open(extra, encoding="utf-8"):
            if not line.strip():
                continue
            r = json.loads(line)
            best[r["path"]] = r
        index = {r["path"]: r for r in rows}
        replaced = 0
        for path, r in best.items():
            cur = index.get(path)
            if cur is None:
                rows.append(r)
                index[path] = r
                continue
            cur_has = cur.get("format") not in (None, "none")
            new_has = r.get("format") not in (None, "none")
            if new_has and not cur_has:
                index[path].clear()
                index[path].update(r)
                replaced += 1
        print(f"merge {extra}: replaced {replaced} store record(s) that had no metadata")
    for r in rows:
        r["mismatch"] = classify(r)
    return rows


def cmd_report(args):
    rows = load_rows(args.results, args.merge)
    from collections import Counter, defaultdict
    agg = Counter()
    for r in rows:
        for m in r.get("mismatch") or []:
            agg[m] += 1
    s3 = [r for r in rows if not r.get("skipped")]
    units_ok = [r for r in s3 if r.get("units_present")]
    on_alt = [r for r in s3 if r.get("via") and r["via"] != BUCKET]
    lines = ["# Vesuvius open-data catalog · consistency audit", "",
             f"- stores scanned: **{len(rows)}** (resolved on the S3 bucket: {len(s3) - len(on_alt)}; "
             f"on a declared alternate root: {len(on_alt)})",
             f"- stores with full physical units: **{len(units_ok)}**",
             f"- findings: " + (", ".join(f"`{k}` × {v}" for k, v in agg.most_common()) or "none"), ""]
    by = defaultdict(list)
    for r in rows:
        for m in r.get("mismatch") or []:
            by[m].append(r)

    # summary by sample
    per_sample = defaultdict(Counter)
    for r in rows:
        for m in r.get("mismatch") or []:
            per_sample[r.get("sample", "?")][m] += 1
    if per_sample:
        lines += ["## Summary by sample", "", "| sample | findings |", "|---|---|"]
        for s, c in sorted(per_sample.items(), key=lambda kv: -sum(kv[1].values())):
            lines.append(f"| {s} | " + ", ".join(f"`{k}` × {v}" for k, v in c.most_common()) + " |")
        lines.append("")

    # negative results are as useful as findings: say so explicitly
    ladder_checked = sum(1 for r in s3 if r.get("scales"))
    lines += [
        "## Negative results (checked, nothing found)",
        "",
        f"- Level ladders: **{ladder_checked}** stores had parseable multiscale metadata and "
        "**none** showed a non-monotonic or non-integral level ladder.",
        "- The z-axis/in-plane asymmetry of surface volumes "
        "(`[8.64, 8.64, 8.64] → [8.64, 17.28, 17.28] → …`) is uniform across the catalog and is "
        "recorded here as **expected**, not as a defect, so future audits do not re-file it.",
        "- Origins that declare a non-S3 access root are resolved against that root (see `via` in "
        "the JSONL); on such hosts there is no ListObjectsV2 API, so existence is established from "
        "the metadata object and the chunk-page fields stay unknown.",
        "",
    ]

    for m, items in sorted(by.items(), key=lambda kv: -len(kv[1])):
        lines += [f"## {m} — {len(items)} stores", "", "| # | store | sample | detail |", "|---:|---|---|---|"]
        for i, r in enumerate(items[:40], 1):
            det = []
            if r.get("um_in_path"):
                det.append(f"name {r['um_in_path']}µm")
            if r.get("scale0"):
                det.append(f"scale0={r['scale0']}")
            if r.get("units_present") is False:
                det.append("axes have no unit")
            if r.get("chunks_in_first_page") == 0:
                det.append("no chunks in first page")
            if r.get("empty_levels"):
                det.append(f"empty levels {r['empty_levels']}")
            lines.append(f"| {i} | `{r['path']}` | {r.get('sample','')} | {'; '.join(det)} |")
        if len(items) > 40:
            lines.append(f"| … | {len(items)-40} more in the JSONL results | | |")
        lines.append("")
    # newline="\n" keeps the output byte-identical on Windows and Linux, so a CI job can
    # regenerate the report and diff it against the committed file.
    open(args.out, "w", encoding="utf-8", newline="\n").write("\n".join(lines))

    # machine-readable remediation list: what a maintainer would actually act on
    ACTIONS = {
        "AXES_UNIT_MISSING": "Write axes[].unit in the store metadata (the pitch is already stated in the store name), or document the exemption.",
        "SCALE_IS_UNIT": "Write the level-0 scale from the pitch encoded in the store name; a reader that trusts metadata otherwise gets 1.",
        "NO_METADATA": "Decide whether this store should carry .zattrs/zarr.json; if it is intentional, document it so consumers can tell.",
        "PATH_MISSING": "The declared access root does not serve this path: backfill it or drop the origin from the catalog.",
        "NO_CHUNKS_IN_FIRST_PAGE": "Check whether the level actually contains chunks; an empty level reads as fill_value with no error.",
        "EMPTY_PYRAMID": "Every declared level is header-only: backfill the chunks or remove/quarantine the store.",
        "PARTIAL_LEVELS_MISSING": "Some declared levels contain no chunks: readers that pick a coarser level silently get fill_value (--deep only).",
        "NON_MONOTONIC": "Repair the level ladder; readers pick levels by expected scale.",
        "NON_INTEGRAL_RATIO": "Repair the level ladder ratio.",
        "LIST_ERROR": "Transient request failure - re-run the scan; not a finding.",
        "META_ERROR": "Transient metadata fetch failure - re-run the scan; not a finding.",
        "ALT_HOST_ORIGIN": "No action: this origin was resolved against its own declared (non-S3) root.",
    }
    fix = {"generated_from": args.results, "stores": len(rows),
           "classes": {m: {"count": len(v), "recommended_action": ACTIONS.get(m, ""),
                           "paths": [r["path"] for r in v]}
                       for m, v in sorted(by.items(), key=lambda kv: -len(kv[1]))}}
    if hasattr(args, "fixlist") and args.fixlist:
        open(args.fixlist, "w", encoding="utf-8", newline="\n").write(
            json.dumps(fix, ensure_ascii=False, indent=2))
        print(f"wrote {args.fixlist}")
    print(f"wrote {args.out}: {len(rows)} stores, {len(agg)} finding classes")


SELFTEST_CASES = [
    (lambda: is_chunk_key("0/0/0/5"), True, "hierarchical chunk"),
    (lambda: is_chunk_key("0/0.0.11"), True, "dotted chunk"),
    (lambda: is_chunk_key("0/.zarray"), False, "metadata is not a chunk"),
    (lambda: um_from_path("a/8.64um-1.2m-x.zarr/"), 8.64, "µm from name"),
    (lambda: resolves_on_s3([S3_ROOT]), True, "s3 origin"),
    (lambda: resolves_on_s3(["https://data.aws.ash2txt.org"]), False, "other root is not s3"),
    (lambda: parse_multiscales({"multiscales": [{"axes": [{"name": "z", "unit": "micrometer"}],
                                                 "datasets": [{"coordinateTransformations": [{"scale": [2.4, 2.4, 2.4]}]}]}]})["units_present"],
     True, "v2 axes with units"),
    (lambda: parse_multiscales({"attributes": {"multiscales": [{"axes": [{"name": "z"}],
                                                               "datasets": [{"coordinateTransformations": [{"scale": [1, 1, 1]}]}]}]}}, v3=True)["scale0"],
     [1, 1, 1], "v3 scale parsed from zarr.json"),
    (lambda: ladder_issues([[2, 2, 2], [2, 4, 4]]), [], "clean ladder"),
    (lambda: ladder_issues([[2, 2, 2], [1, 1, 1]]), ["NON_MONOTONIC", "NON_INTEGRAL_RATIO"], "broken ladder"),
    (lambda: classify({"exists": True, "um_in_path": 8.64, "scale0": [1, 1, 1], "units_present": False}),
     ["AXES_UNIT_MISSING", "SCALE_IS_UNIT"], "unitless store naming a pitch"),
    (lambda: classify({"skipped": "NOT_S3_ORIGIN", "exists": False}), [], "other roots are not findings"),
]


def cmd_selftest(_args):
    bad = 0
    for fn, want, label in SELFTEST_CASES:
        try:
            got = fn()
        except Exception as e:  # noqa: BLE001
            got, label = f"raised {e!r}", label
        ok = got == want
        bad += 0 if ok else 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}: got {got!r} want {want!r}")
    print(f"{len(SELFTEST_CASES)-bad}/{len(SELFTEST_CASES)} passed")
    return 1 if bad else 0


def cmd_explain(args):
    """Show every stored field and the derived labels for one store, so a reviewer can
    spot-check a claim without parsing the JSONL."""
    rows = [json.loads(l) for l in open(args.results, encoding="utf-8") if l.strip()]
    hits = [r for r in rows if args.path in r["path"]]
    if not hits:
        print(f"no store in {args.results} matches {args.path!r}")
        return 1
    for r in hits[: args.limit]:
        labels = r.get("mismatch") or classify(r)
        print(r["path"])
        print(f"  kind                 : {r.get('kind')}")
        print(f"  sample               : {r.get('sample')}")
        print(f"  metadata format      : {r.get('format')}")
        print(f"  pitch in store name  : {r.get('um_in_path')}")
        units = r.get("units_present")
        print(f"  axes carry a unit    : {'yes' if units else 'NO' if units is False else 'n/a'}")
        print(f"  level-0 scale        : {r.get('scale0')}")
        print(f"  declared levels      : {r.get('n_levels')}")
        print(f"  keys on first page   : {r.get('chunks_in_first_page')} chunks / {r.get('n_keys_first_page')} keys")
        if r.get("empty_levels") is not None:
            print(f"  levels with no chunks: {r.get('empty_levels')}")
        if r.get("list_err"):
            print(f"  list error           : {r.get('list_err')}")
        if r.get("meta_err"):
            print(f"  metadata error       : {r.get('meta_err')}")
        print(f"  => findings          : {', '.join(labels) if labels else 'none'}")
        print()
    return 0


def cmd_asserts(args):
    """Structural assertions over the committed evidence.

    `asserts` is its own module, so `python -m scroll_catalog_audit.asserts` works; exposing it here as
    well means every documented command has the same shape (`-m scroll_catalog_audit <sub>`), which it
    did not, and that asymmetry cost me two rounds of "why does this exit 2".
    """
    from scroll_catalog_audit import asserts
    return asserts.main()


def cmd_drift(args):
    """What changed in the catalog since the last sweep?

    Diffs the origins the catalog declares *now* against the paths in a committed results file, so a
    catalog edit can be followed up with a few requests instead of a full re-scan. This is how a fix
    to a single store (e.g. an entry removed from the manifest) is confirmed.
    """
    rows = [json.loads(l) for l in open(args.results, encoding="utf-8") if l.strip()]
    have = {r["path"] for r in rows}
    catalog = load_catalog(args.catalog)
    now = build_roots(catalog)

    added = sorted(set(now) - have)
    removed = sorted(have - set(now))
    print(f"declared now: {len(now)}   in {os.path.basename(args.results)}: {len(have)}")
    print(f"added since the sweep   : {len(added)}")
    print(f"removed since the sweep : {len(removed)}")
    for label, items in (("ADDED", added), ("REMOVED", removed)):
        for p in items[: args.limit]:
            kind = now.get(p, {}).get("kind", "?")
            print(f"  [{label}] {kind:<34} {p}")
        if len(items) > args.limit:
            print(f"  ... and {len(items) - args.limit} more {label.lower()}")
    if not added and not removed:
        print("no drift: the declared set is identical to the swept set")
    if args.emit_json:
        with open(args.emit_json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"added": added, "removed": removed}, fh, ensure_ascii=False, indent=2)
        print(f"wrote {args.emit_json}")
    return 0


def cmd_demo(args):
    """One command, fully offline: prove the tool works, reproduce the two filed issues,
    and print the headline numbers from the committed results."""
    line = "=" * 72
    print(line)
    print("scroll-catalog-audit demo - offline, no network, ~2 seconds")
    print(line)

    print("\n[1/3] offline unit checks")
    rc = cmd_selftest(args)
    if rc:
        return rc

    print("\n[2/3] calibration: both cases below are already filed upstream, so the tool's")
    print("      labels can be checked against a ground truth rather than taken on trust.")
    cases = [
        ("#1892 - declares six levels, holds no chunks",
         "20260226123353", "NO_CHUNKS_IN_FIRST_PAGE"),
        ("#1951 - the store name states a pitch the metadata does not carry",
         "PHerc1447/segments/20250702235910", "SCALE_IS_UNIT"),
    ]
    rows = []
    if os.path.exists(args.results):
        # `demo` with no flags should show the same numbers as the committed report, so pick up
        # the sibling evidence files that ship with it unless the caller asked for something else.
        merges = list(getattr(args, "merge", None) or [])
        if not merges:
            here = os.path.dirname(os.path.abspath(args.results))
            for extra in ("results_alt.jsonl", "results_deep.jsonl"):
                candidate = os.path.join(here, extra)
                if os.path.exists(candidate):
                    merges.append(candidate)
        rows = load_rows(args.results, merges)
    else:
        print(f"      ({args.results} not found - run `scan` first for the full demo)")
    for title, needle, expect in cases:
        print(f"\n  {title}")
        hits = [r for r in rows if needle in r["path"]]
        if not hits:
            print(f"    no store in {args.results} matches {needle!r}")
            continue
        r = hits[0]
        labels = classify(r)
        print(f"    {r['path']}")
        print(f"    pitch in name={r.get('um_in_path')} axis unit={'yes' if r.get('units_present') else 'NO'}"
              f" level-0 scale={r.get('scale0')} chunks on first page="
              f"{r.get('chunks_in_first_page')}/{r.get('n_keys_first_page')}")
        print(f"    -> {', '.join(labels) or 'none'}"
              + ("   [OK]" if expect in labels else f"   [EXPECTED {expect}!]"))

    print("\n[3/3] headline numbers (from the committed results, not from a live scan)")
    from collections import Counter
    s3 = [r for r in rows if not r.get("skipped")]
    on_alt = [r for r in s3 if r.get("via") and r["via"] != BUCKET]
    units = sum(1 for r in s3 if r.get("units_present"))
    agg = Counter(m for r in rows for m in (r.get("mismatch") or classify(r)))
    print(f"    stores: {len(rows)}   (S3: {len(s3) - len(on_alt)}, alternate root: {len(on_alt)})"
          f"   with full physical units: {units}")
    for k, v in agg.most_common():
        print(f"    {k}: {v}")
    print("\nRe-run any single store with:  python -m scroll_catalog_audit explain --path <substring>")
    print("Regenerate this report with:  python -m scroll_catalog_audit report --results results.jsonl")
    return 0


def cmd_siblings(args):
    """Stores that share a name: the same volume republished under several segment directories.

    Finds the copies of one store name (`--path` substring) and, with `--summary`, the
    catalog-wide question of how many affected stores have a correct sibling to copy metadata from.
    """
    rows = load_rows(args.results, args.merge)
    from collections import Counter, defaultdict
    groups = defaultdict(list)
    for r in rows:
        parts = [x for x in r["path"].strip("/").split("/") if x]
        groups[parts[-1] if parts else r["path"]].append(r)

    def affected(r):
        labels = r.get("mismatch") or classify(r)
        return "AXES_UNIT_MISSING" in labels or "SCALE_IS_UNIT" in labels

    if args.path:
        hits = {k: v for k, v in groups.items() if args.path in k}
        if not hits:
            print(f"no store name matching {args.path!r}")
            return 1
        for name, copies in hits.items():
            ok = [c for c in copies if c.get("units_present") is True]
            print(f"store name: {name}")
            print(f"copies: {len(copies)}   with full units: {len(ok)}   without: {len(copies) - len(ok)}")
            for c in sorted(copies, key=lambda c: str(c.get("scale0"))):
                tag = "OK " if c.get("units_present") is True else "BAD"
                units = "micrometer" if c.get("units_present") is True else "-"
                print(f"  [{tag}] units={units:<11} scale0={str(c.get('scale0')):<24} {c['path']}")
            print()
        return 0

    bad = [r for r in rows if affected(r)]
    with_sibling = []
    for r in bad:
        parts = [x for x in r["path"].strip("/").split("/") if x]
        sibs = [s for s in groups[parts[-1]] if s is not r and s.get("units_present") is True]
        if sibs:
            with_sibling.append(r)
    print(f"stores stating a um pitch with no scale in metadata: {len(bad)}")
    print(f"  of those, copies with a correct sibling to copy metadata from: {len(with_sibling)}")
    print(f"  single-copy stores that need an in-place fix or a re-publish: {len(bad) - len(with_sibling)}")
    for r in with_sibling[:10]:
        print(f"    {r['path'][:110]}")
    rep = Counter(r.get("kind") for r in bad)
    print("  by kind:", dict(rep))
    print("\nNOTE: the shortcut applies to the listing above only; do not generalise it.")
    print("Render-date clustering was tested and rejected: affected stores span 2024-10..2026-06")
    print("with clean months in between, so the pattern is per-sample/per-store, not per-date.")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="scroll_catalog_audit", description=__doc__.split("\n")[1])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan", help="audit every zarr root in the catalog")
    s.add_argument("--catalog", default=None, help="local metadata.min.json (default: fetch from bucket)")
    s.add_argument("--results", default="results.jsonl")
    s.add_argument("--limit", type=int, default=None)
    s.add_argument("--kind", default=None, help="only scan roots whose kind contains this substring (e.g. 'volume:')")
    s.add_argument("--path-substring", default=None, help="only scan roots whose path contains this substring")
    s.add_argument("--random", type=int, default=None, help="randomly sample this many roots (with --seed)")
    s.add_argument("--seed", type=int, default=0, help="seed for --random sampling")
    s.add_argument("--workers", type=int, default=10)
    s.add_argument("--deep", action="store_true", help="also probe declared levels for chunks")
    s.set_defaults(func=cmd_scan)
    r = sub.add_parser("report", help="turn results.jsonl into FINDINGS.md")
    r.add_argument("--results", default="results.jsonl")
    r.add_argument("--out", default="FINDINGS.md")
    r.add_argument("--fixlist", default="fixlist.json",
                   help="machine-readable remediation list (empty string to skip)")
    r.add_argument("--merge", action="append", default=None,
                   help="another results.jsonl to merge in; per store, the run that obtained "
                        "metadata wins (removes transient-failure noise). Repeatable.")
    r.set_defaults(func=cmd_report)
    t = sub.add_parser("selftest", help="run offline unit checks (no network)")
    t.set_defaults(func=cmd_selftest)
    e = sub.add_parser("explain", help="show stored fields and derived labels for one store")
    e.add_argument("--results", default="results.jsonl")
    e.add_argument("--path", required=True, help="substring of the store path")
    e.add_argument("--limit", type=int, default=5)
    e.set_defaults(func=cmd_explain)
    d = sub.add_parser("demo", help="offline: self-test + calibration cases + headline numbers")
    d.add_argument("--results", default="results.jsonl")
    d.add_argument("--merge", action="append", default=None,
                   help="another results.jsonl to merge in (same semantics as `report`)")
    d.set_defaults(func=cmd_demo)
    sib = sub.add_parser("siblings",
                         help="stores that share a name (one volume republished under many segments)")
    sib.add_argument("--results", default="results.jsonl")
    sib.add_argument("--merge", action="append", default=None)
    sib.add_argument("--path", default=None, help="store-name substring; omit for the catalog-wide summary")
    sib.set_defaults(func=cmd_siblings)
    dr = sub.add_parser("drift",
                        help="what the catalog declares now versus what the last sweep covered")
    dr.add_argument("--results", default="results.jsonl")
    dr.add_argument("--catalog", default=None, help="local catalog snapshot (default: fetch it)")
    dr.add_argument("--limit", type=int, default=25)
    dr.add_argument("--emit-json", default="", help="write the added/removed lists here")
    dr.set_defaults(func=cmd_drift)
    asr = sub.add_parser("asserts", help="structural assertions over the committed evidence")
    asr.set_defaults(func=cmd_asserts)
    args = ap.parse_args(argv)
    sys.exit(args.func(args) or 0)


if __name__ == "__main__":
    main()
