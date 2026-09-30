"""Geometry screening metadata; force requires a separate explicit load case."""
from math import isfinite
from .process import settings as process_settings

GRAVITY=9.80665
VERSION='CAPACITY_SCENARIO_V5_EXPLICIT_LOAD_CASE_REQUIRED'
BASIS_ENVELOPE='OUTER_ENVELOPE_GEOMETRY_ONLY'
BASIS_PROXY='LAYER_EXTRUSION_GEOMETRY_COMPARISON_ONLY'


def _number(value,maximum=1e9):
    try:value=float(value)
    except (TypeError,ValueError):return None
    return value if isfinite(value) and 0<value<=maximum else None


def capacity_for_candidate(candidate,directional_mpa,analysis=None,lever_mm=None,*,reference_area_basis='UNKNOWN'):
    """Never turn an envelope or nominal infill setting into a force prediction.

    Use load_case.evaluate_load_case with complete deposition roads and explicit
    restraints for conditional stress. The legacy output shape remains compatible.
    """
    if not isinstance(directional_mpa,dict):return None
    axis=str(candidate.get('section_normal_axis') or candidate.get('axis') or 'Z').upper()
    if axis not in ('X','Y','Z'):return None
    area=_number(candidate.get('min_section_area_mm2'));is_proxy=area is None
    if is_proxy:area=_number(candidate.get('material_area_proxy_mm2'))
    reference=_number(directional_mpa.get(axis),1e5)
    if area is None or reference is None:return None
    if reference_area_basis not in ('UNKNOWN','GROSS_ENVELOPE','NET_MATERIAL','INTERLAYER_CONTACT'):
        raise ValueError('INVALID_STRESS_AREA_BASIS')
    return {'model_version':VERSION,'is_failure_prediction':False,'empirically_validated':False,
            'structure_settings':process_settings(analysis),'structure_model':'DEPOSITION_GEOMETRY_REQUIRED',
            'reference_stress_area_basis':reference_area_basis,
            'calibration_status':'NOT_A_MECHANICAL_CAPACITY','calibration_source_ids':[],
            'calculation_status':'GEOMETRY_COMPARISON_ONLY' if is_proxy else 'LOAD_CASE_AND_DEPOSITION_REQUIRED',
            'section_geometry_status':'LAYER_VOLUME_PROXY' if is_proxy else 'OUTER_ENVELOPE_ONLY',
            'effective_load_bearing_area_mm2':None,'bonded_contact_area_mm2':None,
            'solid_section_verified':False,'material_reference_mpa':reference,
            'scenario_adjusted_stress_mpa':None,'allowable_mpa':None,
            'section_normal_axis':axis,'section_area_mm2':area,
            'axial_capacity_n':None,'axial_capacity_kgf':None,
            'bending_capacity_nmm':None,'bending_lever_mm':None,
            'bending_force_n':None,'bending_force_kgf':None,
            'governing_capacity_n':None,'governing_capacity_kgf':None,
            'governing_mode':'LAYER_COMPARISON_ONLY' if is_proxy else 'EXPLICIT_LOAD_CASE_REQUIRED',
            'section_modulus_mm3':_number(candidate.get('section_modulus_mm3')) if not is_proxy else None,
            'basis':BASIS_PROXY if is_proxy else BASIS_ENVELOPE,'is_measured':False,
            'assumes_solid_section':False,'section_knockdown':None,'section_knockdown_reasons':[],
            'prediction_interval_n':None,
            'validation':{'status':'NO_MATCHED_PART_FAILURE_TESTS','property':'GEOMETRIC_SCREENING_ONLY',
                'source_grade_transfer_validated':False,'process_transfer_validated':False,
                'section_model_validated_against_printed_coupons':False,'uncertainty_quantified':False},
            'assessment_gaps':['EXPLICIT_LOAD_CASE_REQUIRED','COMPLETE_DEPOSITION_GEOMETRY_REQUIRED',
                'VOID_AND_CONTACT_GEOMETRY_UNKNOWN','NOTCH_AND_CRACK_FAILURE_NOT_SOLVED',
                'ACTUAL_LOAD_AND_RESTRAINTS_UNKNOWN'],
            'limitations':['An outer envelope or layer-summed extrusion proxy is not a connected deposited section.',
                'Nominal 100% infill does not verify a solid section, actual bead geometry or weld contact.',
                'No uncalibrated pattern multiplier, infill power law or guessed moment arm is used.',
                'Provide a fixed region, point load and complete dimensioned deposition roads for a conditional stress scenario.']}
