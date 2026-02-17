import re


def add_h_in_final_cluster(pro_form: str):
    return re.sub("([^aeiouv]+)([aeiouv]?)$", r"\1h\2", pro_form)


def drop_h_in_final_cluster(pro_form: str):
    return re.sub("([^aeiouv]+)h([aeiouv]?)$", r"\1\2", pro_form)


def add_h_in_first_cluster(stem: str):
    return re.sub("^([aeiouv]?)([^aeiouv]+)", r"\1\2h", stem)


def drop_h_in_first_cluster(stem: str):
    return re.sub("^([aeiouv]?)([^aeiouv]+)h", r"\1\2", stem)


def metathesize_h(pro_form: str, stem: str):
    """
    Move an /h/ from stem to pro

    Returns pronoun (with h) and stem (without h)
    """
    return add_h_in_final_cluster(pro_form), drop_h_in_first_cluster(stem)


def demetathesize_h(h_less_form: str, joined: str):
    """
    Strip pronoun from joined form and re-insert stem h

    Returns stem (with h)
    """
    h_form = add_h_in_final_cluster(h_less_form)
    if not joined.startswith(h_form):
        return None

    stem = joined[len(h_form) :]
    return add_h_in_first_cluster(stem)
