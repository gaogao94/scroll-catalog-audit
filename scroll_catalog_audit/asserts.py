#!/usr/bin/env python3
"""Structural assertions over the committed evidence files.

Run by CI on every push. Deliberately *structural* rather than totals: a catalog that grows should not
fail the build, but a catalog that starts filling blanks with a non-zero value, or publishing a chunk
larger than its array, should.

    python -m scroll_catalog_audit.asserts

Exit code 0 when every assertion holds, 1 otherwise (failing ones are printed).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

from scroll_catalog_audit import audit as A  # noqa: E402


def rows(name: str):
    p = HERE / name
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


_CACHE: dict = {}


def catalog_rows():
    """The catalog rows as the tool itself reads them.

    results.jsonl holds the S3 pass, where the ten origins that declare an alternate access root
    legitimately fail; their successful records are in results_alt.jsonl. Reading the first file
    alone makes those ten look like broken stores, so merge exactly as `report` does.
    """
    if "rows" not in _CACHE:
        _CACHE["rows"] = A.load_rows(str(HERE / "results.jsonl"), [str(HERE / "results_alt.jsonl")])
    return _CACHE["rows"]


def catalog_paths():
    rs = catalog_rows()
    bad = [r for r in rs if not r.get("exists")]
    return not bad, f"{len(rs) - len(bad)}/{len(rs)} roots resolve"


def catalog_chunks():
    """At most one store may show no chunks - and only where a listing was actually possible.

    The alternate access root has no listing API, so its records carry n_keys_first_page = None:
    that is "unknown", not "empty", and counting it as empty is how a check like this produces a
    false alarm. One store really does have a header but no chunks (#1892).
    """
    rs = [r for r in catalog_rows() if r.get("n_keys_first_page") is not None]
    empty = [r for r in rs if (r.get("chunks_in_first_page") or 0) == 0]
    return len(empty) <= 1, f"{len(empty)} of {len(rs)} listable store(s) have no chunks on the first page"


def header_fill_value():
    rs = rows("results_zarray.jsonl")
    bad = [r for r in rs if r.get("fill_value") not in (0, 0.0)]
    return not bad, f"{len(bad)} non-zero fill_value"


def header_chunk_size():
    rs = rows("results_zarray.jsonl")
    bad = [r for r in rs if r.get("chunks") and r.get("shape")
           and any(c > s for c, s in zip(r["chunks"], r["shape"]))]
    return not bad, f"{len(bad)} oversized chunk(s)"


def header_dtype():
    rs = rows("results_zarray.jsonl")
    seen = sorted({str(r.get("dtype")) for r in rs})
    return all(d in ("|u1", "uint8", "<u1") for d in seen), str(seen)


def header_v3_compressed():
    rs = [r for r in rows("results_zarray.jsonl") if r.get("format") == "v3"]
    bad = [r for r in rs if r.get("compressor") in (None, "null", "")]
    return not bad, f"{len(rs) - len(bad)}/{len(rs)} v3 stores compressed"


def levels_contiguous():
    rs = rows("results_levels.jsonl")
    bad = [r for r in rs if r.get("contiguous_from_zero") is False]
    return not bad, f"{len(bad)} non-contiguous declaration(s)"


def levels_last_exists():
    rs = [r for r in rows("results_levels.jsonl") if r.get("status") == "OK"]
    bad = [r for r in rs if not r.get("last_level_header")]
    return not bad, f"{len(rs) - len(bad)}/{len(rs)} have their last declared level"


def deep_no_empty():
    rs = rows("results_deep.jsonl")
    bad = [r for r in rs if r.get("n_chunks") == 0 or r.get("empty")]
    return not bad, f"{len(bad)} header-only level(s)"


def level_chunks_present():
    """At most one store may have a level with a header and no chunks behind it (#1892)."""
    rs = rows("results_level_chunks.jsonl")
    empty = [1 for r in rs for l in r.get("levels", []) if l.get("status") == "OK" and l.get("n_chunks") == 0]
    stores = {r["path"] for r in rs for l in r.get("levels", []) if l.get("status") == "OK" and l.get("n_chunks") == 0}
    return len(stores) <= 1, f"{len(empty)} level(s) across {len(stores)} store(s) hold no chunks"


CHECKS = [
    ("catalog: every declared root resolves", catalog_paths),
    ("catalog: at most one store has no chunks on the first page", catalog_chunks),
    ("headers: fill_value is zero everywhere", header_fill_value),
    ("headers: no chunk larger than its array", header_chunk_size),
    ("headers: every dtype is uint8", header_dtype),
    ("headers: every v3 store is compressed", header_v3_compressed),
    ("levels: declared pyramid paths are contiguous from zero", levels_contiguous),
    ("levels: the last declared level has a header", levels_last_exists),
    ("deep: no header-only level in the probed volumes or segments", deep_no_empty),
    ("level chunks: at most one store has a level with no chunks", level_chunks_present),
]


def main() -> int:
    failed = 0
    for name, fn in CHECKS:
        try:
            ok, detail = fn()
        except Exception as exc:  # a malformed evidence file must fail loudly
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        if not ok:
            failed += 1
        print(f"  [{'ok' if ok else 'FAIL'}] {name}" + ("" if ok else f"  ({detail})"))
    print(f"{len(CHECKS) - failed}/{len(CHECKS)} structural assertions hold")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
