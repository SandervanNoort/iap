import time

time0 = time.time()


def time_it(text=None):
    global time0  # pylint: disable=W0603
    time1 = time.time()
    if text is not None:
        print("{0:<40s} {1:.1f}".format(text, time1 - time0))
    time0 = time1
