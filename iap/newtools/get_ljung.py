import rpy2
from .uncwrapper import uncwrapper


def get_ljung(data, fit, lag=None):
    """Get p value for Ljungbox test"""
    r_uc = uncwrapper
    run_r = rpy2.robjects.r

    det = run_r.residuals(fit)
    arma = r_uc(fit.rx2("arma"))
    if lag is None:
        freq = int(run_r.frequency(data)[0])
        lag = min(2 * len(det) // 5,
                  2 * freq if arma[2] + arma[3] > 0 else 10)
    ljung = run_r["Box.test"](
        det, lag=lag, fitdf=sum(arma[0:4]), type="Ljung-Box")
    if False:
        lag2 = int(round(len(det)**0.5))
        ljung2 = run_r["Box.test"](
            det, lag=lag2, fitdf=sum(arma[0:4]), type="Ljung-Box")
        return min(ljung.rx2("p.value")[0], ljung2.rx2("p.value")[0])
    else:
        return ljung.rx2("p.value")[0]
