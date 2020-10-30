def dewp_temp_to_rh(D, T):
    """Determine relative humidity from the Dewpoint and the temperature"""
    # (Invalid name) pylint: disable=C0103

    d = 273
    a1 = -4.9283
    a = -4.9283
    c = 23.5518
    c1 = 23.5518
    b = -2937.4
    b1 = -2937.4
    return ((T + d) ** (-a1) * (D + d) ** a *
            10 ** ((c - c1) + b / (D + d) - b1 / (T + d)))
