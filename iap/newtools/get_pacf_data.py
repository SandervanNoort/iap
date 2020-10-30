import rpy2
from .get_z import get_z
import numpy


def get_pacf_data(series1, freq=None, **kwargs):
    """PACF data"""
    run_r = rpy2.robjects.r

    alpha = 0.05
    rdata = run_r.pacf(
        run_r.ts(series1, frequency=freq) if freq is not None else series1,
        plot=False, **kwargs)
    data = {"y": list(rdata.rx2("acf")),
            "x": list(rdata.rx2("lag")),
            "significant": (get_z(1 - alpha / 2) /
                            numpy.sqrt(rdata.rx2("n.used"))),
            "type": "pacf"}
    return data
