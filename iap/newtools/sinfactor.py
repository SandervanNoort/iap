import numpy


def sinfactor(time, coefs):
    """Sinusoide of a varying degree"""
    amplitude, horizontal, vertical = coefs
    # f = A sin ((time - H) * 2 pi / 365) + V
    return (amplitude * numpy.sin((time - horizontal) * 2 * numpy.pi / 365) +
            vertical)
