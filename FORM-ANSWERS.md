# Progress Prize 提交 · 照抄粘贴清单

> 表单入口：<https://scrollprize.org/prizes> → **Progress Prizes** 一节的 **Submission Form**
> （我已抓到的直链是 <https://docs.google.com/forms/d/e/1FAIpQLSc4flEfgK2nyjoczz2_U_XrIGMlgrnSknWatLqrFPnbtKfZwg/viewform>，但 Google 在我这边被墙、无法核实它对应哪个奖项，请以页面上的 "Submission Form" 链接为准。）
> **截止：2026-10-31 23:59 太平洋时间**
> 规则允许**每月多次提交**，所以下面两份都可以交。

---

## 提交 1 / 2 · 目录一致性审计工具

**Title / 标题**

```
scroll-catalog-audit: read-only consistency audit of the Vesuvius open-data catalog
```

**Link / 链接**

```
https://github.com/gaogao94/scroll-catalog-audit
```

**Short description / 简短说明（若表单只有一个说明框，用这段）**

```
A metadata-only audit of every Zarr store the Vesuvius catalog publishes (894 roots, ~1,900
requests, zero chunk bytes downloaded). It resolves each origin against its own declared access
root, checks pyramid levels for chunks, and compares the physical pitch stated in a store's name
with the scale its OME metadata carries.

Findings (2026-10-03 snapshot, two sweeps merged per store):
- 81 stores state a um pitch in their own name while their OME metadata carries no scale;
  76 of them are raw CT volumes -- the input to every downstream step -- across 39 samples.
- 1 store declares six pyramid levels and holds no chunks (reproduces issue #1892).
- 14 stores carry no metadata object at all.
- Negative result: no broken level ladders; deep sweeps of all 120 raw volumes and of a
  reproducible 60-root random sample of segment volumes found no header-only level.

Reproducibility: `python -m scroll_catalog_audit demo` runs the offline self-test, reproduces both
already-filed issues, and prints every headline number. A CI job regenerates all committed reports
from the committed per-store data and fails on any diff, so no number in the repository can be
hand-edited. The repository also documents every check that came back clean, with the scope each
one actually covered (NEGATIVE_RESULTS.md), so the negative side is as reviewable as the positive.

Motivated three upstream pull requests and one new issue (see submission 2). MIT licensed, stdlib only.
```

**Longer detail / 更长说明（若表单允许长文本）**

把 `work/publish/SUBMISSION.md` 的正文整段粘贴。

---

## 提交 2 / 2 · 三处"静默物理尺度"修复

**Title / 标题**

```
Three fixes for silent physical-scale defaults in the Vesuvius toolchain (reader and writer side)
```

**Links / 链接**

```
https://github.com/ScrollPrize/villa/pull/1954
https://github.com/ScrollPrize/villa/pull/1955
https://github.com/ScrollPrize/villa/pull/1956
https://github.com/ScrollPrize/villa/issues/1957
https://github.com/gaogao94/scroll-catalog-audit
```

**Short description / 简短说明**

```
Three places read or write a physical voxel size that may simply be absent, and substitute 1.0
without a word: two reader paths in lasagna, two more in tifxyz_label_transfer, and one writer in
spiral-fitting that bakes 1.0 into newly produced OME-Zarr metadata. Nothing distinguishes
"this store is unitless" from "this store is 1 um per voxel", so downstream distances are wrong by
the ratio of the real pitch (8.64x for the PHerc1447 set in issue #1951).

The patches make the absence visible -- a single warning naming the affected levels, plus an
opt-in --require-scale that fails instead of proceeding unitless -- and leave every produced and
consumed value byte-identical. Both sides are covered: the reader fix makes the 81 existing stores
in the catalog stop being silently misread; the writer fix stops new instances being created.

Evidence: a metadata-only audit of all 894 published stores (link above) quantifies the class;
each patch adds tests in the repository's existing style and applies cleanly to current main.
```

**Longer detail / 更长说明**

把 `work/publish/SUBMISSION-2-scale-fallback.md` 的正文整段粘贴。

---

## 提交前请顺手确认两件事

1. **表单里若有"类别/Category"字段**：选与 *analytic tools / tooling / bug fixes* 最接近的一项；
   两份提交选不同类别即可，不必相同。
2. **是否需要 Discord**：我在官方条款里读到一句 "To qualify, you must have registered on the
   Vesuvius Challenge Discord at the time of the submission"。它出现在**大奖**条款段落附近，
   是否同样适用于 Progress Prize 我无法确认。若要保险，花 2 分钟注册并加入他们的 Discord 服务器即可。

---

## 提交后

回来说一句「已提交」。我会：把提交时间与链接写入 `ops/ledger.md`，建立 11 月初的跟进提醒，
并按维护者在三份 PR 上的反馈做修改（改动都在一行以内，很快）。
