from typing import List, Dict, Optional, Tuple

def get_root_candidate(stem: str, ending_pattern: str) -> Optional[str]:
    """
    Statically strips class endings from a stem to find the root.
    Handles * and @ modifiers in the ending pattern.
    """
    if not ending_pattern:
        return stem
        
    literal_ending = ending_pattern.replace("*", "").replace("@", "")
    
    # If there's a literal ending, stem must end with it
    if literal_ending and not stem.endswith(literal_ending):
        return None
        
    # Strip literal ending
    root = stem[:-len(literal_ending)] if literal_ending else stem
    
    # Apply modifiers to the root
    if "*" in ending_pattern:
        if len(root) >= 1:
            root = root[:-1]
        else:
            return None # Cannot apply * to empty root
    elif "@" in ending_pattern:
        if len(root) >= 2:
            root = root[:-2]
        else:
            return None # Cannot apply @ to short root
            
    return root

def check_root_consistency(stem_row: Dict[str, str], class_info: Dict[str, str]) -> Tuple[bool, Optional[str], List[str]]:
    """
    Verifies if all available forms in stem_row yield the same root for a given King Class.
    Returns (is_consistent, root, mismatch_details).
    """
    forms = ['present', 'imperfective', 'perfective', 'imperative', 'infinitive']
    possible_roots = {}
    mismatch_details = []
    is_consistent = True
    
    for fn in forms:
        stem = stem_row.get(fn)
        pattern = class_info.get(fn)
        
        if not stem:
            # Policy: Skip missing forms in consistency check
            continue
            
        root = get_root_candidate(stem, pattern)
        if root is None:
            is_consistent = False
            mismatch_details.append(f"{fn}: Suffix mismatch")
        else:
            possible_roots[fn] = root
            
    if not possible_roots:
        return False, None, ["No forms available to extract root"]
        
    if is_consistent:
        roots_list = list(possible_roots.values())
        first_root = roots_list[0]
        if not all(r == first_root for r in roots_list):
            is_consistent = False
            diffs = [f"{fn}: '{r}'" for fn, r in possible_roots.items() if r != first_root]
            mismatch_details.append(f"Root mismatch: " + ", ".join(diffs))
            return False, None, mismatch_details
        return True, first_root, []
    
    return False, None, mismatch_details
