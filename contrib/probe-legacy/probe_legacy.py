"""Probe the legacy host's fragment stores: metadata only, resumable, no chunk bytes.

Why this exists: the catalog's six fragment samples carry no volumes or segments of their own - their
`legacy_data_url` points at dl.ash2txt.org, which the maintainers have said is no longer maintained
(#1760). Those files are still the only copies of the fragments, and fragments are training material,
so "is the legacy copy usable, and does it carry the same defects" is a question with a real audience
even though nothing will be fixed there.

Discovery is by directory listing (the host serves autoindex pages). Only `.zattrs` / `zarr.json` are
fetched; no chunk bytes, no data objects.

    python ops/probe_legacy.py --out work/publish/results_legacy.jsonl
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://dl.ash2txt.org"
UA = {"User-Agent": "Mozilla/5.0 (scroll-catalog-audit legacy probe; metadata only)"}
FAMILIES = [
    ("Frag1", "PHercParis2Fr47"),
    ("Frag2", "PHercParis2Fr143"),
    ("Frag3", "PHercParis1Fr34"),
    ("Frag4", "PHercParis1Fr39"),
    ("Frag5", "PHerc1667Cr1Fr3"),
    ("Frag6", "PHerc51Cr4Fr8"),
]
MAX_DEPTH = 5


def listing(url: str) -> list[str] | None:
    """Directory entries, or None when the URL is not a listing."""
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=45) as resp:
            body = resp.read(200_000).decode("utf-8", "replace")
    except Exception:
        return None
    hrefs = re.findall(r'href="([^"?][^"]*)"', body)
    out = []
    for h in hrefs:
        if h.startswith(("http://", "https://", "/", "..", "#")):
            continue
        out.append(h)
    return out


def fetch_json(url: str):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=45) as resp:
            raw = resp.read(1_000_000)
    except Exception:
        return None
    if raw[:2] == b"\x1f\x8b":
        try:
            raw = gzip.decompress(raw)
        except Exception:
            return None
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None


def find_zarr_roots(root_url: str, budget: list[int]) -> list[str]:
    """Walk the autoindex pages under `root_url` collecting `*.zarr/` directories."""
    found: list[str] = []
    queue = [(root_url, 0)]
    seen = set()
    while queue and budget[0] > 0:
        url, depth = queue.pop(0)
        if url in seen or depth > MAX_DEPTH:
            continue
        seen.add(url)
        budget[0] -= 1
        entries = listing(url)
        if entries is None:
            continue
        for e in entries:
            if e.endswith(".zarr/"):
                found.append(urllib.parse.urljoin(url, e))
            elif e.endswith("/") and depth < MAX_DEPTH:
                queue.append((urllib.parse.urljoin(url, e), depth + 1))
    return sorted(set(found))


def probe(url: str) -> dict:
    rec = {"url": url, "path": url[len(BASE):].lstrip("/")}
    attrs = fetch_json(url + ".zattrs") or fetch_json(url + "zarr.json")
    rec["format"] = "v2" if fetch_json(url + ".zattrs") is not None else ("v3" if attrs else "none")
    rec["has_metadata"] = attrs is not None
    units, scale0, n_levels, declared = None, None, None, None
    if isinstance(attrs, dict):
        ms = attrs.get("multiscales")
        if not isinstance(ms, list) and isinstance(attrs.get("attributes"), dict):
            ms = attrs["attributes"].get("multiscales")
        if isinstance(ms, list) and ms:
            m0 = ms[0]
            axes = [a for a in (m0.get("axes") or []) if isinstance(a, dict)]
            units = [a.get("unit") for a in axes] or None
            declared = [d.get("path") for d in (m0.get("datasets") or [])]
            n_levels = len(declared)
            for d in (m0.get("datasets") or [])[:1]:
                for t in d.get("coordinateTransformations") or []:
                    if isinstance(t, dict) and t.get("type") == "scale":
                        scale0 = t.get("scale")
    rec["units"] = units
    rec["scale0"] = scale0
    rec["declared_levels"] = n_levels
    # Which declared levels actually exist? One listing of the store root is enough.
    entries = listing(url)
    rec["root_entries"] = sorted(e.rstrip("/") for e in (entries or []))[:12]
    present = {e.rstrip("/") for e in (entries or [])}
    if declared:
        rec["levels_present"] = [p for p in declared if p in present]
        rec["levels_missing"] = [p for p in declared if p not in present]
    rec["unitless"] = units is not None and not any(units)
    rec["unit_is_one"] = scale0 in ([1, 1, 1], [1.0, 1.0, 1.0])
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="work/publish/results_legacy.jsonl")
    ap.add_argument("--budget", type=int, default=1200, help="max listing requests for discovery")
    args = ap.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done: set[str] = set()
    if out.exists():
        for line in out.read_text(encoding="utf-8").splitlines():
            if line.strip():
                done.add(json.loads(line)["url"])
        print(f"resuming: {len(done)} root(s) already probed")

    budget = [args.budget]
    targets: list[str] = []
    for fam, sample in FAMILIES:
        root = f"{BASE}/fragments/{fam}/{sample}.volpkg/"
        found = find_zarr_roots(root, budget)
        print(f"  {fam}/{sample}: {len(found)} zarr root(s)  (budget left {budget[0]})")
        targets += found
    targets = [t for t in targets if t not in done]
    print(f"probing {len(targets)} root(s)")

    with out.open("a", encoding="utf-8") as fh:
        for i, url in enumerate(targets, 1):
            rec = probe(url)
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            if i % 10 == 0:
                print(f"  {i}/{len(targets)}")
            time.sleep(0.05)
    print(f"done -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
