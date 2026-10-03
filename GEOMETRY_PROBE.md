shape/scale consistency probe - evidence log
============================================

Run A - all volume roots (--all --kind "volume:")
  stores probed : 120
  status        : {'OK': 119, 'INCOMPLETE': 1}
  mismatches    : 0
  note          : the single INCOMPLETE was a transient fetch failure; re-checking that store
                  directly shows 0/.zarray present (HTTP 200, 239 bytes) and 297 chunk keys on the
                  first page, so it is not a defect.

Run B - small segment sample (--limit 30):
  stores probed : 30
  status        : {'OK': 30}
  mismatches    : 0

Run C - the 81 stores carrying the units defect (--all --affected):
  stores probed : 81
  status        : {'OK': 81}
  mismatches    : 0

Totals: 231 store-probes, 0 mismatches.

Check performed: for every declared level, compare shape_i against shape_0 / (scale_i / scale_0)
with a tolerance of max(1 voxel, 1%).
