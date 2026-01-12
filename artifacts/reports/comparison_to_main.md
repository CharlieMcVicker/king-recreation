# Performance Comparison: Current vs Main

**Baseline:** `main` branch
**Current:** `general-h-alt` (including recent `eli` fix)

The current branch shows a significant regression in coverage compared to `main` across all metrics. While recent changes improved stem derivation, the downstream classification and reconstruction steps are failing for a large number of verbs that work on `main`.

## Metric Comparison

| Metric | Main (Baseline) | Current | Difference |
| :--- | :--- | :--- | :--- |
| **Strict Reconstructs** | **50.4%** (313 verbs) | **37.7%** (234 verbs) | <span style="color:red">**-12.7%** (-79 verbs)</span> |
| **Strict Full Class** | 67.8% | 60.1% | <span style="color:red">-7.7%</span> |
| **Strict Ending** | 83.3% | 73.9% | <span style="color:red">-9.4%</span> |
| **Loose Full Class** | 75.7% | 67.3% | <span style="color:red">-8.4%</span> |
| **Loose Ending** | 86.2% | 76.8% | <span style="color:red">-9.4%</span> |

## Detailed Counts (Reconstructs)

| Category | Main | Current |
| :--- | :--- | :--- |
| **Zero Matches** | 308 | 387 |
| **One Match** | 307 | 230 |
| **Multiple Matches** | 6 | 4 |

## Analysis

The `general-h-alt` branch is currently underperforming `main` significantly.

1.  **Regressions:** We have lost reconstruction capability for ~79 verbs.
2.  **Coverage Drop:** Even basic "Ending" matches have dropped by ~10%, suggesting that the generalized h-alternation logic might be interfering with basic suffix matching or stem identification for a wide swath of verbs.
3.  **Recent Impact:** My recent change to relax stem derivation compatibility *improved* the situation (we saw +62 derived stems), but it was not enough to overcome the deficit inherent in this branch.

## Recommendation

Focus should shift to:
1.  Identifying the "Lost 79": Which specific verbs reconstruct on `main` but fail here?
2.  Debugging the `general-h-alt` logic for those specific cases.
