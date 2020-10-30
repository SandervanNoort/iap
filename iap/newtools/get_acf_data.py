import rpy2
import numpy
from .remove_nan import remove_nan
from .get_z import get_z


def get_acf_data(series1, freq=None, **kwargs):
    """ACF data"""
    # http://www.squaregoldfish.co.uk/2010/01/20/
    # r-the-acf-function-and-statistical-significance/
    run_r = rpy2.robjects.r

    alpha = 0.05
    rdata = run_r.acf(
        run_r.ts(series1, frequency=freq) if freq is not None else series1,
        plot=False, **kwargs)
    data = {"y": list(rdata.rx2("acf")),
            "x": list(rdata.rx2("lag")),
            "significant": (get_z(1 - alpha / 2) /
                            numpy.sqrt(rdata.rx2("n.used"))),
            "type": "acf"}
    remove_nan(data["x"], data["y"])
    return data
