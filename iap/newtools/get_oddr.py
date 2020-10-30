import numpy
from .get_z import get_z


def get_oddr(h_new, n_new, h_orig, n_orig, alpha=0.05):
    """Return the odds ratio"""

    if h_orig == 0 or h_new == 0:
        return None, None, None

    m_new = n_new - h_new
    m_orig = n_orig - h_orig
    oddr = (h_new / m_new) / (h_orig / m_orig)

#     if h_new == 0 or h_orig == 0:
#         return None, oddr, None

    error = numpy.sqrt(1 / h_new + 1 / m_new + 1 / h_orig + 1 / m_orig)
    min_oddr = numpy.exp(numpy.log(oddr) - get_z(1 - alpha / 2) * error)
    max_oddr = numpy.exp(numpy.log(oddr) + get_z(1 - alpha / 2) * error)

    return [min_oddr, oddr, max_oddr]
