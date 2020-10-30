import rpy2
from .Capturing import Capturing
from .arima import arima


def auto_arima(data, prev_arma=None, cache=None, **kwargs):
    """Return the best fit, starting with <old_arma>"""
    run_r = rpy2.robjects.r

    if prev_arma is None:
        prev_arma = (0, 0, 0, 0,
                     int(run_r.frequency(data)[0]),
                     kwargs.pop("d"), kwargs.pop("D"))

    next_arma = prev_arma
    with Capturing():
        run_r.library("fpp")

    if cache is None:
        cache = {}

    values = arima(data, prev_arma, cache, **kwargs)
    aic = values["aic"]
    ljung = values["ljung"]
    fit = values["fit"]
    if sum(list(prev_arma)[0:4]) == 0:
        print(next_arma, aic, ljung)

    for index in range(4):
        arma = list(prev_arma)
        arma[index] += 1
        arma = tuple(arma)
        values = arima(data, arma, cache)
        if ((values["ljung"] > 0.05 and values["aic"] < aic) or
                (ljung <= 0.05 and values["ljung"] > ljung) or
                (values["ljung"] == 0 and ljung == 0 and
                 values["aic"] < aic)):
            next_arma = arma
            aic = values["aic"]
            ljung = values["ljung"]
            fit = values["fit"]
    print(next_arma, aic, ljung)
    if next_arma != prev_arma:
        return auto_arima(data, prev_arma=next_arma, cache=cache)
    else:
        return fit
