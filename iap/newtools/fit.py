import numpy
import time
import logging
from .perm import perm
from .leastsq import leastsq
from .lprint import lprint
# import scipy.stats
# PARTICLES = 100
# LSQ = False

INCREASE = 0.5
ZERO = False
DOTS = 3
MIN_SIZE = 0.0001
STEPS = 8
STOP_STEP = 2
MIN_VAL = -15
MAX_VAL = 15
ERROR_REPR = "{error:.3g}"
R2_REPR = "{r2:.2f}"


def cube_find(scaled, error_value_function, cube):
    """find the best parameter within the cube"""
    # scaled_list = perm([
    #     numpy.linspace(scaled_elem - sd, scaled_elem + sd, DOTS)
    #     for scaled_elem, sd in zip(scaled, cube)])
    scaled_list = perm([
        numpy.linspace(scaled_elem - step_to_size(sd),
                       scaled_elem + step_to_size(sd), DOTS)
        for scaled_elem, sd in zip(scaled, cube)])

    # scaled_list = scipy.stats.norm.rvs(scaled, list(cube),
    #         size=(PARTICLES, len(scaled)))

    # remove elements which are bigger or smaller than allowed
    scaled_list = scaled_list[numpy.all(
        numpy.logical_and(scaled_list >= MIN_VAL, scaled_list <= MAX_VAL),
        axis=1)]

    error_list = numpy.array([error_value_function(scaled_elem)
                              for scaled_elem in scaled_list])
    scaled_new = scaled_list[error_list.argmin()]

#     if (ERROR_REPR.format(error=error_value_function(scaled)) ==
#             ERROR_REPR.format(error=error_value_function(scaled_new)) and
#             (r2_func is None or
#              R2_REPR.format(r2=r2_func(scaled)) ==
#              R2_REPR.format(r2=r2_func(scaled_new)))):
#         scaled_new = scaled

    # where the new value changed
#     changes = numpy.array([
#         -1 if val else INCREASE
#         for val in abs(scaled - scaled_new) < 0.3 * step_to_size(1)])
    changes = numpy.array([
        -1 if val else INCREASE
        for val in abs(scaled - scaled_new) == 0])
    cube += changes
    cube[cube < 0] = 0
    cube[cube > STEPS] = STEPS

    return scaled_new, cube


def step_to_size(step):
    """convert step to size-dif for scaled"""
    if step == 0 and ZERO:
        return 0
    return 2 ** step * MIN_SIZE


def fit(initial, error_value_function, errors=None, clear=None, r2_func=None):
    """Fit the parameters"""
    scaled = initial
    cube = numpy.array([STEPS] * len(scaled), dtype=float)

    if False:
        scaled, _suc = leastsq(errors, scaled)
        return scaled

    secs = 0
    step = 0
    while max(cube) > STOP_STEP:
        if clear is not None:
            clear()
        logging.debug(
            ("  {step}: " + ERROR_REPR + " {r2}" +
             " ({maxsize:.2g}, {secs:.0f} secs)\n" +
             "    -> {scaled}\n" +
             "    -> {cube}").format(
                 step=step,
                 error=error_value_function(scaled),
                 maxsize=step_to_size(max(cube)),
                 secs=secs,
                 r2="" if r2_func is None else "(R2=" + R2_REPR.format(
                     r2=r2_func(scaled)),
                 cube=lprint(cube, "{0:.2g}"),
                 scaled=lprint(scaled, "{0:.2g}")))
        time0 = time.time()
        scaled, cube = cube_find(scaled, error_value_function, cube)
        secs = time.time() - time0
        step += 1
    logging.info((ERROR_REPR + " (FINAL)-> {scaled}").format(
        error=error_value_function(scaled),
        scaled=lprint(scaled, "{0:.2g}")))
    if False:
        scaled, _suc = leastsq(errors, scaled)
    return scaled
