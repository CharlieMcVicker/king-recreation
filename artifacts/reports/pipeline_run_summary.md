# Pipeline Run Summary

**Date:** Monday, January 12, 2026

## Statistics

| Metric | Previous | Current | Change |
| :--- | :--- | :--- | :--- |
| **Stem Derivation Success** | 465 | 527 | **+62** |
| **Stem Derivation Failures** | 158 | 95 | **-63** |
| **Reconstructible Verbs** | ~238 | 238 | *No Change* |
| **Reconstruction Failures** | 131 | 217 | **+86** |

## Analysis

1.  **Stem Derivation:** The relaxation of compatibility checks significantly improved coverage, allowing **62 previously failing verbs** (including "he thinks so") to be successfully parsed into stems.
2.  **Downstream Impact:** These newly derived verbs have now moved downstream to the Classification and Reconstruction stages.
3.  **Reconstruction Bottle-neck:** Most of these new verbs are currently failing the **Reconstruction** or **Full Classification** checks. This is why "Reconstruction Failures" increased significantly while "Reconstructible Verbs" remained flat.
    *   *Example:* "he thinks so" is now successfully derived, but classifies only as `strict,ending` (not `strict,full`) for Classes Ia and Id, likely due to mismatches between the derived stem (e.g., `el-`) and the expected stem-final characters for those classes.

## Next Steps
-   Investigate `reconstruction_failures.csv` to identify why the newly derived stems are not fully matching their target classes.
-   Adjust Class definitions or Stem Derivation rules to bridge the gap.
