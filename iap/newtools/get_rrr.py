from .get_rr import get_rr


def get_rrr(h_new, n_new, h_orig, n_orig, alpha=0.05):
    """Get the reduced risk ratio"""
    # (Invalid name) pylint: disable=C0103

    min_rr, rr, max_rr = get_rr(h_new, n_new, h_orig, n_orig, alpha)
    return (1 - max_rr, 1 - rr, 1 - min_rr)
