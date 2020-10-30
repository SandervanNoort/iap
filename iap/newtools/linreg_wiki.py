import numpy
import scipy.stats


def linreg_wiki(x, y, intercept0=False, conf=0.95):
    """Simple linear regression based on wikipedia code
       http://en.wikipedia.org/wiki/Simple_linear_regression
    """
    # (Invalid name) pylint: disable=C0103
    # (Too many local variables) pylint: disable=R0914

    if None in x or None in y:
        x, y = zip(*[(x1, y1) for x1, y1 in zip(x, y)
                     if x1 is not None and y1 is not None])

    if len(x) < 2 or len(y) < 2:
        return None, None, None, None, None

    x = numpy.array(x)
    y = numpy.array(y)

    n = len(x)
    alpha = 1 - conf

    y_mean = y.mean()
    sumx = x.sum()
    sumy = y.sum()
    sumxx = (x * x).sum()
    sumyy = (y * y).sum()
    sumxy = (x * y).sum()

    if intercept0:
        gradient = sumxy / sumxx

        if n > 2:
            # for only 2 points no R2 or confidence interval
            ssres = sum((y - gradient * x) ** 2)
            sst = sum((y - y_mean) ** 2)
            r2 = 1 - ssres / sst

            s2 = sum((y - gradient * x) ** 2) / (n - 1)
            t = scipy.stats.distributions.t.ppf(1 - alpha / 2, n - 1)
            sd_gradient = t * numpy.sqrt(s2 / sumxx)
        else:
            sd_gradient = None
            r2 = None
        return r2, gradient, sd_gradient, 0, 0
    else:
        gradient = (n * sumxy - sumx * sumy) / (n * sumxx - sumx ** 2)
        intercept = sumy / n - gradient * sumx / n

        if n > 2:
            # for only 2 points no R2 or confidence interval
            se2 = (n * sumyy - sumy ** 2 -
                   gradient ** 2 * (n * sumxx - sumx ** 2)) / (n * (n - 2))
            sb2 = (n * se2) / (n * sumxx - sumx ** 2)
            sa2 = sb2 * sumxx / n

            t = scipy.stats.distributions.t.ppf(1 - alpha / 2, n - 2)
            sd_gradient = numpy.sqrt(sb2) * t
            sd_intercept = numpy.sqrt(sa2) * t

            ssres = sum((y - (gradient * x + intercept)) ** 2)
            sst = sum((y - y_mean) ** 2)
            r2 = 1 - ssres / sst
        else:
            sd_gradient = None
            sd_intercept = None
            r2 = None

    return r2, gradient, sd_gradient, intercept, sd_intercept
