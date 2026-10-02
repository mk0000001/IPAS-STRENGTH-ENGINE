"""Keep manufacturer stress references separate from an assumed load margin.

The margin is an uncalibrated scenario choice. It neither recalibrates the
manufacturer's material data nor establishes an allowable or breaking load.
"""
from collections.abc import Mapping
from decimal import Decimal, DecimalException, localcontext, MAX_EMAX, MIN_EMIN

MAX_REFERENCE_MPA=Decimal('100000')  # Same stress-input bound as process.number.


def _positive_decimal(value,maximum=None):
    if isinstance(value,bool) or not isinstance(value,(str,int,float,Decimal)):
        raise ValueError('INVALID_REFERENCE_NUMBER')
    number=value if isinstance(value,Decimal) else Decimal(str(value))
    if not number.is_finite() or number<=0 or (maximum is not None and number>maximum):
        raise ValueError('INVALID_REFERENCE_NUMBER')
    return number


def reference_inputs(raw_reference_mpa,internal_margin_factor=None):
    """Return fresh raw-material and once-adjusted load-reference dictionaries.

    Accept XY/Z manufacturer data or explicit X/Y/Z references. Conflicting
    representations, missing directions and invalid numbers withhold the whole
    directional reference. A missing or invalid margin leaves valid raw material
    references available, but never publishes adjusted load inputs.
    """
    result={'directional_material_mpa':None,'directional_capacity_mpa':None,
            'internal_margin_factor':None,'status':'WITHHELD_INVALID_REFERENCE',
            'margin_basis':'UNCALIBRATED_LOAD_SCENARIO_MARGIN',
            'margin_is_calibrated':False,'factor_applied_to_material':False,
            'factor_applied_to_capacity':False}
    try:
        if not isinstance(raw_reference_mpa,Mapping):return result
        if 'XY' in raw_reference_mpa:
            xy=_positive_decimal(raw_reference_mpa['XY'],MAX_REFERENCE_MPA)
            references={'X':xy,'Y':xy,'Z':_positive_decimal(raw_reference_mpa['Z'],MAX_REFERENCE_MPA)}
            for axis in ('X','Y'):
                if axis in raw_reference_mpa and _positive_decimal(raw_reference_mpa[axis])!=xy:
                    return result
        else:
            references={axis:_positive_decimal(raw_reference_mpa[axis],MAX_REFERENCE_MPA) for axis in ('X','Y','Z')}
    except (KeyError,TypeError,ValueError,DecimalException):
        return result
    result['directional_material_mpa']={axis:str(value) for axis,value in references.items()}
    if internal_margin_factor is None:
        result['status']='MATERIAL_REFERENCE_ONLY'
        return result
    try:
        factor=_positive_decimal(internal_margin_factor)
        if factor>1:raise ValueError('INVALID_MARGIN_FACTOR')
    except (TypeError,ValueError,DecimalException):
        result['status']='WITHHELD_INVALID_MARGIN'
        return result
    adjusted={}
    try:
        for axis,value in references.items():
            # A coefficient product needs at most the sum of its digit counts.
            # Do not round long source strings through the default Decimal context.
            with localcontext() as context:
                context.prec=len(value.as_tuple().digits)+len(factor.as_tuple().digits)+1
                context.Emax=MAX_EMAX;context.Emin=MIN_EMIN
                product=value*factor
                if not product.is_finite() or product<=0:
                    raise ValueError('UNREPRESENTABLE_CAPACITY_REFERENCE')
                adjusted[axis]=str(product.normalize())
    except (ValueError,DecimalException):
        result['status']='WITHHELD_CAPACITY_ARITHMETIC'
        return result
    result.update(directional_capacity_mpa=adjusted,internal_margin_factor=str(factor),
                  status='READY',factor_applied_to_capacity=True)
    return result
