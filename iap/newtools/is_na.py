import rpy2


def is_na(elem):
    """And R-element is NA"""
    if isinstance(elem, (
            rpy2.robjects.rinterface.NACharacterType,
            rpy2.robjects.rinterface.NAComplexType,
            rpy2.robjects.rinterface.NAIntegerType,
            rpy2.robjects.rinterface.NALogicalType,
            rpy2.robjects.rinterface.NARealType)):
        return True
    else:
        return False
