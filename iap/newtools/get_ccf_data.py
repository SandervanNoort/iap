import rpy2
import numpy
from .get_z import get_z


def get_ccf_data(series1, series2, freq=None, **kwargs):
    """CCF data"""
    run_r = rpy2.robjects.r

    alpha = 0.05
    rdata = run_r.ccf(
        run_r.ts(series1, frequency=freq) if freq is not None else series1,
        run_r.ts(series2, frequency=freq) if freq is not None else series2,
        plot=False, **kwargs)
    data = {"y": list(rdata.rx2("acf")),
            "x": list(rdata.rx2("lag")),
            "significant": (get_z(1 - alpha / 2) /
                            numpy.sqrt(rdata.rx2("n.used"))),
            "type": "ccf"}
    return data
