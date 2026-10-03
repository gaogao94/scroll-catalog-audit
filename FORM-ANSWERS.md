# Progress Prize 提交 · 照抄粘贴清单

> 这份是仓库内的公开副本；**对外粘贴以工作区的 `表单填写内容.md` 为准**（它受 `ops/check_numbers.py` 校验）。

> **表单入口（已由官方流水线确认）：** 奖项文案 `scrollprize.org/docs/34_prizes.md` 第 347 行在
> `{/* progress-prizes:form:start */}` 机器标记之间写着这个表单地址——即官方自动化本身在维护它，
> 不是我的推断。同一节的截止日期标记（第 326 行）写明 **11:59pm Pacific, October 31st, 2026**。
>
> **表单入口：** <https://docs.google.com/forms/d/e/1FAIpQLSc4flEfgK2nyjoczz2_U_XrIGMlgrnSknWatLqrFPnbtKfZwg/viewform>
>
> **⚠️ 奖项页上有 4 个表单链接，只有第 1 个是 Progress Prize。** 其余三个我逐一解析并核对了它们在页面中的位置：
>
> | 链接 | 页面上下文 | 属于 |
> |---|---|---|
> | `1FAIpQLSc4flEf…` ← **用这个** | "Technical Integration / Accept standard community formats (OME-Zarr…)" | **Progress Prizes** |
> | `forms.gle/4zeVPPBtNdSCAQa88` | "As with the Grand Prize, you must not make your discovery public…" | Title Prize |
> | `forms.gle/TM5ao8GwC2mDrdLk9` | "train a model on it … grow from a few visible strokes" | First Letters |
> | `forms.gle/wvNK7DkNKuRKjHJdA` | "unroll large areas … same problem as the First Letters prize below" | 大奖 / Open Problems |
>
> **提交错表单等于没提交**，所以请从上面的直链进入，或从 <https://scrollprize.org/prizes> 的 **Progress Prizes** 一节点 "Submission Form"。
>
> **截止：2026-10-31 23:59 太平洋时间。** 规则允许**每月多次提交**，下面两份都可以交。

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
- Negative result: no broken level ladders; every declared level of every root was listed and counted
  (884 roots, 5,304 level listings, all successful) and only six levels hold a header with no chunks -
  the six levels of one store (#1892).

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

## 官方公布的"提交核心要求"→ 对应内容（可直接粘贴）

奖项文案（`scrollprize.org/docs/34_prizes.md`，由官方流水线用机器标记维护）在 Progress Prizes
一节里明确列出三条核心要求。如果表单按这三条提问，用下面这段回答：

```
1. Problem identification and solution
   Challenge: the published catalog is not self-describing. A metadata-only sweep of all 894 Zarr
   roots shows 81 stores whose own name states a micrometre pitch while their OME metadata carries
   no scale (76 of them raw CT volumes, the input to every downstream step, across 39 samples), 43
   prediction stores with no scale at all, 14 stores with no metadata object, and one store that
   declares six levels and holds no chunks.
   Implementation path: `scan` (metadata only, resumable) -> `report` (FINDINGS.md + machine-readable
   fixlist.json) -> `explain` for a single store. One command reproduces the two already-filed issues
   offline: `python -m scroll_catalog_audit demo`.
   Advantages over existing solutions: the identity of the failure is not the pyramid geometry
   (checked elsewhere, and clean here) but the metadata layer - and specifically the gap between what
   the catalog manifest records and what the store publishes. For 77 of the 81 stores the pitch is
   already in `metadata.min.json` and simply is not propagated, so the repair is mechanical rather
   than archaeological. No existing tool cross-references manifest and store metadata; that
   comparison is what produced issues #1957, #1958 and #1959 and the fix plans committed with this
   repository. In total 124 stores publish no axis unit at all: 81 state a pitch in the name, and 43
   are prediction stores with no pitch in the name.
   The three upstream pull requests are the fixes the audit motivated.

2. Documentation
   README (usage, every finding class, both traps that produced false findings before they were
   handled), NEGATIVE_RESULTS.md (every check that came back clean, with the scope it covered and
   its limits), REMEDIATION.md and the two machine-readable fix plans, plus contrib/ which carries
   the upstream issue texts and patches. 12 offline unit checks; a CI job regenerates every
   committed report from the committed per-store data and fails on any diff, so no number can be
   hand-edited.

3. Technical integration
   Reads standard community formats: OME-Zarr metadata in both Zarr v2 (.zattrs) and v3 (zarr.json)
   form, resolved per declared access root. Emits stable machine-readable output (per-store JSONL,
   JSON fix list) that other tooling can consume, and the audit module is importable for use inside
   a publish pipeline. Stdlib only, no dependencies, no chunk bytes downloaded; the whole sweep is
   ~1,900 requests.
```

---

## 提交前请顺手确认一件事

1. **表单里若有"类别/Category"字段**：选与 *analytic tools / tooling / bug fixes* 最接近的一项；
   两份提交选不同类别即可，不必相同。

> **Discord 不需要——已查证。** 我先前提示过"提交时必须已注册 Discord"，那其实是**大奖（2027 Grand
> Prize）**的条款：在官方权威文案 `scrollprize.org/docs/34_prizes.md` 中，Discord 要求**只出现一次**，
> 位于第 167 行的 `## 2027 Grand Prize` 一节；**Progress Prizes 一节（302–348 行）完全没有这条**，
> 而评奖自动化脚本（`.github/progress-prizes-*.mjs`）里也**不检查 Discord**。
> 所以这份提交不依赖 Discord——登不上不影响。

---

## 提交后

回来说一句「已提交」。我会：把提交时间与链接写入 `ops/ledger.md`，建立 11 月初的跟进提醒，
并按维护者在三份 PR 上的反馈做修改（改动都在一行以内，很快）。
