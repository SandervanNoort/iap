def dewp_temp_to_ah(D, T):
    """Determine absolute humidity from the Dewpoint and the temperature"""
    # (Invalid name) pylint: disable=C0103

    k = 0.21668
    d = 273
    a = -4.9283
    c = 23.5518
    b = -2937.4
    return k / (T + d) * (D + d) ** a * 10 ** (c + (b / (D + d)))
