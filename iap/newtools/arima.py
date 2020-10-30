import rpy2
from .Capturing import Capturing
from .cwrapper import cwrapper
from .get_ljung import get_ljung


def arima(data, arma, cache=None, **kwargs):
    """Do an arima model with arma and return results
       cached if available"""
    r_c = cwrapper
    run_r = rpy2.robjects.r

    if cache is None:
        cache = {}

    if isinstance(arma, list):
        arma = tuple(arma)

    if arma not in cache:
        try:
            with Capturing():
                fit = run_r.Arima(data, order=r_c(arma[0], arma[5], arma[1]),
                                  seasonal=r_c(arma[2], arma[6], arma[3]),
                                  **kwargs)
            aic = fit.rx2("aic")[0]
            ljung = get_ljung(data, fit)
            cache[arma] = {"fit": fit, "aic": aic, "ljung": ljung}
        except rpy2.rinterface.RRuntimeError:
            cache[arma] = {"fit": None, "aic": 99999, "ljung": 0}
        print("  {arma}: {aic:.0f} - {ljung:.2g}".format(
            arma=arma, **cache[arma]))
    return cache[arma]
