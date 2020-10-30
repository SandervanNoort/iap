import scipy.stats


def get_z(alpha):
    """Get z factor quantile"""
    return scipy.stats.distributions.norm.ppf(alpha)
