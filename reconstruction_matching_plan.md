# Reconstruction Matching Fix Plan

## Goal Description

The current reconstruction logic fails to identify consistent roots when a class uses `*` (strip 1 char) or `@` (strip 2 chars) rules alongside normal rules. This is because `check_root_consistency` strictly requires all forms to yield identical root strings. However, applying a `*` rule naturally results in a truncated root candidate relative to the full root. This plan proposes a "Best Root" algorithm that tolerates expected truncation, enabling valid reconstruction for these classes.

## Proposed Changes

### king_recreation

#### [MODIFY] [stem_analysis.py](file:///Users/charlesmcvicker/code/king-recreation/king_recreation/stem_analysis.py)

- Modified `get_root_candidate` to ONLY strip literal endings, deferring truncation logic.
- Modified `check_root_consistency` to:
  1. Collect all root candidates along with the "depth" of truncation implied by their rule (Normal=0, `*`=1, `@`=2).
  2. Determine a "Target Root" from the candidate with the _lowest_ truncation depth (most information).
  3. Validate all other candidates against this Target Root by checking if they match `TargetRoot[:-depth_diff]`.

#### [NEW] [tests/test_reconstruction_consistency.py](file:///Users/charlesmcvicker/code/king-recreation/tests/test_reconstruction_consistency.py)

- Created unit tests with real corpus examples (Ia\* and IIIa2) to verify truncation handling.

## Verification Results

- **Unit Tests**: All 4 tests passed (Consistency with `*`, consistency with `@`, inconsistency on wrong truncation, inconsistency on different stems).
- **Pipeline Impact**:
  - Reconstructible verbs increased to **263** (42.4% coverage).
  - Validation Success: **267/268** (99.6%).
