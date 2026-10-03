# 待提交材料 · #1951 补充证据（定稿）

> 状态：**已定稿（数字已按最终全量重扫刷新），等 G1（GitHub 身份）解锁后作为 comment 提交到 [ScrollPrize/villa#1951](https://github.com/ScrollPrize/villa/issues/1951)**。
> 数据来源：2026-10-03 对目录全部 **894 个 Zarr 根**的只读扫描（匿名 S3 `ListObjectsV2` + `.zattrs` / `zarr.json` 头，**未下载任何 chunk 字节**；1,904 次请求 / 1,406 秒）。
> 证据纪律：工具先在官方已确认案例上做过 ground-truth 校准；批量结论均抽样回原始元数据复核并设对照组；两次自我纠错（见文末）发生在上报之前。

---

## 提交正文（英文，仓库语言）

**Catalog-wide extent of the missing-physical-scale pattern — raw CT volumes included, and a negative result on level ladders**

Method: read-only sweep of **all 894 Zarr roots** the catalog publishes (`metadata.min.json`, 2026-10-03). Every root was resolved against **its own declared `access_roots`** (the catalog publishes some volumes twice, once on `s3://vesuvius-challenge-open-data` and once on `https://data.aws.ash2txt.org`; resolving everything against S3 manufactures false "missing path" hits). Metadata was read from `.zattrs` (Zarr v2) with a `zarr.json` fallback (Zarr v3). No chunk bytes were downloaded.

**Result 1 — the pattern is catalog-wide and hits the primary data.**
Full sweep, 2026-10-03: 894 roots, of which **884 resolve on the S3 bucket** (the other 10 declare a non-S3 access root and are skipped by design). **755 (85.4 %) carry full physical units**; and **71 stores have a µm token in their own name while their OME metadata carries no `scale`**, i.e. the store name states a physical pitch that the metadata does not:

| kind | count | example |
|---|---:|---|
| `volume:ome-zarr` (**raw CT**) | **66** | `PHerc0139/volumes/20260413113053-1.129um-0.2m-59keV-masked.zarr` |
| `segment:layers-zarr` (surface volumes — the 4 reported here) | 4 | `PHerc1447/.../8.64um-1.2m-116keV-volume-20250521151220.zarr` |
| `volume:surface-prediction-zarr` | 1 | — |

The 71 roots span **39 samples**. So the failure mode described in this issue affects the **raw scans** — the input to everything else — not just the four surface volumes: a consumer that reads physical voxel size from OME metadata gets `unit: null` / `scale: [1,1,1]` for 66 raw volumes, and the filename is the only place the true pitch appears. Meanwhile segment surface volumes in the same samples (e.g. `PHerc0172/segments/.../7.91um-53keV-volume-20241024131838.zarr`) do carry `"unit": "micrometer"` and the correct scale, so the catalog is **not** uniformly unitless and a reader cannot rely on either behaviour.

*Counting method, stated because it matters*: the numbers come from **two independent sweeps merged per store** (`report --merge`): for each store the run that actually obtained metadata wins. A single sweep gave 67 / 62 / 35 — the difference is entirely transient metadata-fetch failures, which the tool labels `META_ERROR` and re-runs rather than reporting. Anyone reproducing this should expect a few stores to move between classes on a re-run.

Two adjacent classes came out of the same sweep, both reproducible with the same tool:
* **1 store** declares six pyramid levels and contains **no chunks at all** — it reads back as `fill_value` with no error (this is #1892, reproduced here as a calibration case).
* **14 stores** carry no metadata object at all (`.zattrs` and `zarr.json` both 404). Stores whose metadata fetch failed transiently are labelled `META_ERROR` and re-run rather than reported.
* **Deep sweep** (every declared level probed for chunks, not just level 0): all **120 raw volumes** and a reproducible random sample of **60 segment surface volumes** (`--random 60 --seed 20261003`, 8.7 % of that family) → **no header-only level**. Level 0 was checked on every root, and exactly one store lacks chunks there (#1892). So the empty-pyramid class is real but rare; 0 hits in 60 draws bounds the segment rate at <5 % (95 %, rule of three) rather than proving absence.

**Result 2 — negative result on level ladders (please do not flag these).**
Across all **794 roots with parseable multiscale metadata**: 0 non-monotonic ladders, 0 ladders with non-integral level ratios. The 681 segment surface volumes are *systematically* anisotropic — z keeps the base pitch while the in-plane axes double per level (`[8.64, 8.64, 8.64] → [8.64, 17.28, 17.28] → …`). This is uniform across the catalog and consistent with z being the through-sheet sampling axis, so it should not be reported as a scale defect. Recording it here so the next audit does not re-file it.

**Reproduction.** `scroll-catalog-audit` (read-only, stdlib only, resumable): `scan` sweeps every root in ~1,900 requests with no chunk bytes; `report` emits `FINDINGS.md` plus a machine-readable `fixlist.json` (per class: count, recommended remediation, store paths). The published tool name/section also handles both Zarr v2 and v3 metadata and resolves each origin against its own declared access root. Link to be added once published.

**Three corrections made before filing** (in case they are useful to other auditors):
1. chunk keys occur in **two** naming styles — hierarchical `0/0/0/5` **and** dotted `0/0.0.11`; a digit-only matcher declares populated stores empty (false positives across a whole class).
2. Zarr **v3** stores keep metadata in `zarr.json` (keys `0/c/0/0`), not `.zattrs`; treating them as "no metadata" hides 81 roots that in fact **do** carry units.
3. the catalog publishes some volumes on **two access roots**; resolving every path against the bucket manufactures false "missing path" hits (10 of them). Resolving each origin against its own declared root gives 0.

---

## 附件（本地就绪，发布后即为公开链接）

| 文件 | 内容 |
|---|---|
| `work/publish/scroll_catalog_audit/audit.py` | 发布版审计器（只读 / 标准库 / v2+v3 / 按 access_roots 解析 / 可断点续跑 / 12 项离线自测） |
| `work/publish/results.jsonl` | **最终全量结果：894 行明细**（1,904 次请求 / 1,406 秒） |
| `work/publish/FINDINGS.md` | 自动生成：分类表 + 按 sample 汇总 + **阴性结论**一节 |
| `work/publish/fixlist.json` | 机器可读整改清单：每类的数量、建议动作与受影响 store 路径 |
| `work/audit/`（过程件） | 早期版本工具与中间结果，保留以证明校准过程 |

## 提交前检查清单

- [x] **R1 查重**：已确认 #1354（文件名 µm 语义）、#1892/#1755/#1756（空金字塔）、#1949（镜像缺卷）、#1950（未压缩）、#1730（日期倒挂）均在案；本材料只做**未覆盖部分的量化**并附阴性结论
- [x] **R2 校准**：工具在 #1892（零 chunk 卷）与 #1951（4 个卷）上精确复现后才开始全量扫描；最终版 `report` 可**从已有 JSONL 重算分类**，因此 #1892 在非 deep 模式下也能被标出
- [x] **R4 access_roots**：修正了 10 条"路径缺失"假阳性（真值 0）
- [x] **R5 抽样复核**：5 个原始卷 + 4 个表面卷 + 对照组逐一手工核对原始元数据
- [x] **R6 限速与错误分类**：瞬时失败单列 `LIST_ERROR` / `META_ERROR`（本轮均为 0 / 9），不并入结论
- [x] 数字已按 2026-10-03 最终全量重扫刷新（67 个 store / 35 个 sample）
- [ ] 等 G1 解锁后提交（同时把发布版工具推到公开仓库，提供可复现链接）
