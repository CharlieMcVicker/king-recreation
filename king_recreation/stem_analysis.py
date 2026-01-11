from typing import List, Dict, Optional, Tuple
from king_recreation.phonology_data import get_pronominal_set_name, is_h_dropping_set, drop_first_h

def get_root_candidate(stem: str, ending_pattern: str) -> Optional[str]:
    """
    Statically strips class endings from a stem.
    Does NOT apply * or @ modifiers; these are handled by consistency 
    checks and reconstruction logic.
    """
    if not ending_pattern:
        return stem
        
    literal_ending = ending_pattern.replace("*", "").replace("@", "")
    
    # If there's a literal ending, stem must end with it
    if literal_ending and not stem.endswith(literal_ending):
        return None
        
    # Strip literal ending
    root = stem[:-len(literal_ending)] if literal_ending else stem
    return root

def check_root_consistency(stem_row: Dict[str, str], class_info: Dict[str, str]) -> Tuple[bool, Optional[str], List[str]]:
    """
    Verifies if all available forms in stem_row yield the same root for a given King Class.
    Accounts for expected truncation from * (1 char) and @ (2 chars) rules.
    Returns (is_consistent, root, mismatch_details).
    """
    forms = ['present', 'imperfective', 'perfective', 'imperative', 'infinitive']
    candidate_data = [] # List of (form, root, depth)
    mismatch_details = []
    
    # Extract metadata for set identification
    set_type = stem_row.get('set_a_b') # 'a' or 'b'
    imp_type = 'to_3rd' if stem_row.get('2_to_3') == 'True' else 'normal'

    for fn in forms:
        stem = stem_row.get(fn)
        pattern = class_info.get(fn, "")
        
        if not stem:
            continue
            
        root = get_root_candidate(stem, pattern)
        if root is None:
            mismatch_details.append(f"{fn}: Suffix mismatch")
            continue
            
        # Determine truncation depth
        depth = 0
        if "*" in pattern:
            depth = 1
        elif "@" in pattern:
            depth = 2
            
        candidate_data.append((fn, root, depth))
            
    if not candidate_data:
        if mismatch_details:
             return False, None, mismatch_details
        return False, None, ["No forms available to extract root"]
        
    # Find the target root: the one with the minimum truncation (most information)
    # Sort by depth (ascending) then by length (descending, if depth is same)
    candidate_data.sort(key=lambda x: (x[2], -len(x[1])))
    best_fn, target_root, target_depth = candidate_data[0]
    
    is_consistent = True
    for fn, root, depth in candidate_data:
        # Expected relationship: root == target_root[:len(target_root) - (depth - target_depth)]
        
        depth_diff = depth - target_depth
        if depth_diff < 0:
             is_consistent = False
             mismatch_details.append(f"{fn}: Unexpectedly longer than target")
             continue
             
        expected_root = target_root
        if depth_diff > 0:
            if len(target_root) >= depth_diff:
                expected_root = target_root[:-depth_diff]
            else:
                expected_root = "" # Truncated to nothing

        if root != expected_root:
            # Check if mismatch is due to allowed h-dropping
            set_name = get_pronominal_set_name(fn, set_type, imp_type) if set_type else None
            is_dropped_match = False
            
            if set_name and is_h_dropping_set(set_name):
                # If target has h, and root is dropped version
                if drop_first_h(expected_root) == root:
                    is_dropped_match = True
            
            if not is_dropped_match:
                is_consistent = False
                if depth_diff > 0:
                    mismatch_details.append(f"{fn}: Truncation mismatch (got '{root}', expected '{expected_root}' as {depth_diff}-char truncation of '{target_root}')")
                else:
                    mismatch_details.append(f"{fn}: Root mismatch (got '{root}', expected '{expected_root}')")
                
    if is_consistent:
        return True, target_root, []
    
    return False, None, mismatch_details
