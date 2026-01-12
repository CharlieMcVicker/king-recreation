# Debug Analysis: "he thinks so" (eli)

**Status:** Derivation Failure
**Reason:** Strict compatibility check fails on short stem vowel alternation.

## Analysis

The verb "he thinks so" has the following forms:
- Present: `eli`
- Present 1sg: `keli`
- Imperfective: `elisk`
- Perfective: `uwelis`
- Imperative: `hela`
- Infinitive: `uwelist`

### Derived Stems (Set A, Normal)

The derivation logic successfully isolates the following potential stems:
- **Present:** `eli` (from `ø-` + `eli`)
- **Imperative:** `ela` (from `h-` + `ela`)
- **Perfective:** `elis` (among others, from `uw-` + `elis`)

### The Compatibility Issue

The core issue lies in the `is_compatible(s1, s2)` function in `king_recreation/derive_stems.py`. It requires one of the following:
1. Exact match.
2. One is a substring of the other (starting at index 0).
3. They share a common prefix of at least 3 characters.
4. They share a common prefix equal to the length of the shorter string (which is equivalent to #2).

Comparing `eli` (Present) and `ela` (Imperative):
- **s1:** "eli" (len 3)
- **s2:** "ela" (len 3)
- **Common Prefix:** "el" (len 2)

Check #2: "eli" is not start of "ela".
Check #3: Common len (2) is not >= 3.
Check #4: Common len (2) is not == min(3, 3).

**Result:** `False`

### Why `analyze_failure.py` reported "Success"

The debugging tool `analyze_failure.py` currently uses a simplified heuristic to group "Success" outcomes: it only checks if a valid stem *starts with the same character* across all forms. Since `eli` and `ela` both start with `e`, it flagged this as a consistent configuration, masking the stricter length-based failure that occurs in the production script.

## Resolution Plan

To support this verb, we need to either:
1. Relax the compatibility threshold for very short stems (allow 2-char overlap if stem length is 3?).
2. Explicitly handle `i`/`a` stem-final alternation as a known pattern.
3. Treat this as an irregular verb requiring manual override.
