import numpy
from .get_z import get_z


def get_rr(h_new, n_new, h_orig, n_orig, alpha=0.05):
    """Calculate the reduced risk ratio"""
    # http://en.wikipedia.org/wiki/Relative_risk
#     h_new = min(h_new, n_new)
#     h_orig = min(h_orig, n_orig)

    # to prevent dividing by zero
#     if h_new == 0:
#         print("Warning: h_new=0")
#         h_new = 1
#     if h_orig == 0:
#         print("Warning: h_orig=0")
#         h_orig = 1

#     if h_orig == 0 or h_new == 0:
#         return None, None, None

    if h_orig == 0:
        return 1, 1, 1
    if h_new == 0:
        return 0, 0, 0

    p_new = h_new / n_new
    p_orig = h_orig / n_orig
    log_rr = numpy.log(p_new / p_orig)

    log_var = ((n_new - h_new) / (h_new * n_new) +
               (n_orig - h_orig) / (h_orig * n_orig))
    log_error = get_z(1 - alpha / 2) * log_var ** 0.5
    result = (numpy.exp(log_rr - log_error), numpy.exp(log_rr),
              numpy.exp(log_rr + log_error))

    return result
