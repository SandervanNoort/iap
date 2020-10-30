from .get_z import get_z


def get_sample(p1, p2, k=None, alpha=0.05, beta=0.20):
    """Calculate sample size

    http://books.google.pt/books?id=-CQtWiJJL0cC&pg=PA381&lpg=PA381
    &dq=sample+size+compare+proportions+binomial&source=bl&ots=W1I0yjXwas
    &sig=z6Pw8ZqhV7iWTUR8cPeN64mC_3Q&hl=en&sa=X&ei=WEUuUdSnGsfEswa314GgBw
    &ved=0CEgQ6AEwAw#v=onepage

    Fundamentals of Biostatistics
    By Bernard A. Rosner
    10.5
    """
    # (Invalid name) pylint: disable=C0103

    q1 = 1 - p1
    q2 = 1 - p2
    delta = abs(p1 - p2)

    # alpha = 0.05 => z = 1.96
    # beta  = 0.20 => z = 0.84
    if k is not None:
        pp = (p1 + k * p2) / (1 + k)
        qq = 1 - pp

        n1 = (
            (((pp * qq * (1 + 1 / k)) ** 0.5 * get_z(1 - alpha / 2) +
              (p1 * q1 + (p2 * q2) / k) ** 0.5 * get_z(1 - beta)) ** 2) /
            delta ** 2)
        n2 = k * n1
    else:
        # k is infinity
        # pp = p2
        # qq = 1 - p2 = q2
        n1 = (
            (((p2 * q2) ** 0.5 * get_z(1 - alpha / 2) +
              (p1 * q1) ** 0.5 * get_z(1 - beta)) ** 2) / delta ** 2)
        n2 = None
    return n1, n2
