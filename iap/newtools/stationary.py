import rpy2


def stationary(data, name=None):
    """Check with 3 tests whether data is stationary"""
    run_r = rpy2.robjects.r
    points = 0

    test = run_r["adf.test"](data, alternative="stationary")
    if test.rx2("p.value")[0] > 0.05:
        if name is not None:
            print("{0} fails adf test".format(name))
        points += 1

#     test = run_r["Box.test"](data, type="Ljung-Box")
#     if test.rx2("p.value")[0] <= 0.05:
#         points += 1

    test = run_r["kpss.test"](data)
    if test.rx2("p.value")[0] <= 0.05:
        if name is not None:
            print("{0} fails kpss test".format(name))
        points += 1

    return points
