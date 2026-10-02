"""Local declared-road reference scenarios and unsupported-geometry metadata."""
from math import isfinite
from . import automatic_sections
from .process import settings as process_settings

GRAVITY=9.80665
VERSION='CAPACITY_SCENARIO_V6_AUTOMATIC_LOCAL_REFERENCE_LOADS'
AUTOMATIC_VERSION=VERSION
BASIS_ENVELOPE='OUTER_ENVELOPE_GEOMETRY_ONLY'
BASIS_PROXY='LAYER_EXTRUSION_GEOMETRY_COMPARISON_ONLY'


def _number(value,maximum=1e9):
    if isinstance(value,bool):return None
    try:value=float(value)
    except (TypeError,ValueError,OverflowError):return None
    return value if isfinite(value) and 0<value<=maximum else None


def _automatic_details_valid(deposited,axis):
    """Complete markers cannot replace finite required output metadata."""
    bending=deposited.get('bending')
    if not isinstance(bending,dict):return False
    principal=bending.get('principal_section_moduli_mm3')
    gradient=deposited.get('weakest_local_bending_stress_gradient_xyz')
    if not isinstance(principal,list) or len(principal)!=2 or \
       not isinstance(gradient,list) or len(gradient)!=3:return False
    if any(isinstance(value,bool) or not isinstance(value,(int,float)) for value in principal+gradient):return False
    try:
        principal=[float(value) for value in principal];gradient=[float(value) for value in gradient]
    except (ValueError,OverflowError):return False
    if any(not isfinite(value) or value<=0 for value in principal):return False
    if any(not isfinite(value) or abs(value)>1+1e-7 for value in gradient):return False
    return abs(sum(value*value for value in gradient)-1)<=1e-6 and abs(gradient['XYZ'.index(axis)])<=1e-7


def capacity_for_candidate(candidate,directional_mpa,analysis=None,lever_mm=None,*,reference_area_basis='UNKNOWN'):
    """Never turn an envelope or nominal infill setting into a force prediction.

    Complete streamed local road sections support explicit reference-stress
    and moment-arm assumptions without an input force. Other candidates retain
    geometry-only output. Explicit restraint/stress evaluation is separate.
    """
    if not isinstance(directional_mpa,dict):return None
    axis=str(candidate.get('section_normal_axis') or candidate.get('axis') or 'Z').upper()
    if axis not in ('X','Y','Z'):return None
    area=_number(candidate.get('min_section_area_mm2'));is_proxy=area is None
    if is_proxy:area=_number(candidate.get('material_area_proxy_mm2'))
    reference=_number(directional_mpa.get(axis),1e5)
    if reference is None:return None
    if reference_area_basis not in ('UNKNOWN','GROSS_ENVELOPE','NET_MATERIAL','INTERLAYER_CONTACT'):
        raise ValueError('INVALID_STRESS_AREA_BASIS')
    deposited=candidate.get('deposited_section')
    if candidate.get('kind')=='LOCAL_THIN_SECTION' and isinstance(deposited,dict) and deposited.get('status')=='COMPLETE' and \
       deposited.get('version')==automatic_sections.VERSION and \
       deposited.get('complete') is True and deposited.get('sampled') is False and \
       deposited.get('provenance')=='GCODE_WIDTH_HEIGHT_ASSUMPTION' and \
       deposited.get('scope')=='LOCAL_DECLARED_ROAD_REGION' and deposited.get('normal_axis')==axis:
        net_area=_number(deposited.get('area_mm2'))
        modulus=_number(deposited.get('minimum_all_direction_section_modulus_mm3'))
        tools=deposited.get('tools')
        if net_area is not None and modulus is not None and isinstance(tools,list) and len(tools)==1 and \
           isinstance(tools[0],int) and not isinstance(tools[0],bool) and tools[0]>=0 and \
           _automatic_details_valid(deposited,axis):
            return _automatic_reference(candidate,deposited,net_area,modulus,reference,axis,analysis,reference_area_basis)
        if isinstance(tools,list) and len(tools)>1:
            blocked=capacity_for_candidate({key:value for key,value in candidate.items() if key!='deposited_section'},
                directional_mpa,analysis,lever_mm,reference_area_basis=reference_area_basis)
            if blocked is None:return None
            blocked['assessment_gaps'].insert(0,'MULTITOOL_STIFFNESS_UNVERIFIED')
            return blocked
    if area is None:return None
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


def _automatic_reference(candidate,deposited,area,modulus,reference,axis,analysis,reference_area_basis):
    """Conditional local tensile/all-direction bending comparisons, without force.

    Coupon stress is explicitly assumed transferable to the declared road union.
    This does not establish actual fixation, bonded area or a failure load.
    """
    axial=reference*area;moment=reference*modulus
    scenarios=[{'lever_mm':lever,'force_n':moment/lever,'force_kgf':moment/lever/GRAVITY,
                'lever_basis':'DECLARED_REFERENCE_MOMENT_ARM','actual_fixation_known':False}
               for lever in (10,25,50)]
    default=scenarios[1];comparison=min(axial,default['force_n'])
    return {'model_version':AUTOMATIC_VERSION,'is_failure_prediction':False,'empirically_validated':False,
            'structure_settings':process_settings(analysis),'structure_model':'LOCAL_DECLARED_ROAD_UNION',
            'reference_stress_area_basis':reference_area_basis,
            'reference_transfer_assumption':{'source_area_basis':reference_area_basis,
                'target_area_basis':'DECLARED_NET_ROAD_ENVELOPE','assumed_net_normal_stress_mpa':reference,
                'verified':False,'basis':'COUPON_REFERENCE_AS_HOMOGENEOUS_NET_SECTION_STRESS'},
            'calibration_status':'UNCALIBRATED_MATERIAL_REFERENCE_SCENARIO','calibration_source_ids':[],
            'calculation_status':'AUTOMATIC_REFERENCE_LOAD_ESTIMATE',
            'section_geometry_status':'COMPLETE_LOCAL_DECLARED_ROAD_SECTION',
            'section_scope':'LOCAL_DECLARED_ROAD_REGION','effective_load_bearing_area_mm2':area,
            'bonded_contact_area_mm2':None,'solid_section_verified':False,'material_reference_mpa':reference,
            'scenario_adjusted_stress_mpa':reference,'allowable_mpa':None,
            'section_normal_axis':axis,'section_area_mm2':area,
            'axial_capacity_n':axial,'axial_capacity_kgf':axial/GRAVITY,
            'bending_capacity_nmm':moment,'bending_lever_mm':25,
            'bending_force_n':default['force_n'],'bending_force_kgf':default['force_kgf'],
            'bending_scenarios':scenarios,
            'governing_capacity_n':comparison,'governing_capacity_kgf':comparison/GRAVITY,
            'governing_mode':'MINIMUM_OF_DECLARED_REFERENCE_SCENARIOS_NOT_PART_FAILURE',
            'section_modulus_mm3':modulus,'bending_basis':'MINIMUM_OVER_ALL_LOCAL_MOMENT_DIRECTIONS',
            'principal_section_moduli_mm3':deposited['bending']['principal_section_moduli_mm3'],
            'weakest_local_bending_stress_gradient_xyz':deposited['weakest_local_bending_stress_gradient_xyz'],
            'basis':'MATERIAL_REFERENCE_TIMES_LOCAL_DECLARED_ROAD_SECTION','is_measured':False,
            'assumes_solid_section':False,'section_knockdown':None,'section_knockdown_reasons':[],
            'prediction_interval_n':None,
            'validation':{'status':'NO_MATCHED_PART_FAILURE_TESTS','property':'LOCAL_REFERENCE_LOAD_COMPARISON',
                'source_grade_transfer_validated':False,'process_transfer_validated':False,
                'section_model_validated_against_printed_coupons':False,'uncertainty_quantified':False},
            'assessment_gaps':['REFERENCE_TO_NET_ROAD_STRESS_TRANSFER_ASSUMED','LOCAL_CROPPED_SECTION_NOT_COMPLETE_LOAD_PATH',
                'PRINTED_BEAD_AND_BOND_GEOMETRY_UNMEASURED','ACTUAL_LOAD_AND_RESTRAINTS_UNKNOWN',
                'SHEAR_TORSION_BUCKLING_AND_CRACK_FAILURE_NOT_SOLVED','NO_MATCHED_PART_FAILURE_TESTS'],
            'limitations':['Values compare a directional material reference with a local union of declared rectangular road envelopes.',
                'Coupon reference stress is assumed to represent homogeneous net-road normal stress; its recorded area basis remains unchanged and this transfer is unverified.',
                'Section-window boundaries clip the local region. Neighboring section material and whole-part load redistribution are not solved.',
                'All local road fragments are assumed to share strain as a perfectly bonded homogeneous continuum; actual contact and weld strength are unmeasured.',
                'Bending covers all moment orientations in this local linear section-stress model; it does not identify the governing whole-part load direction.',
                'The 10, 25 and 50 mm moment arms are declared comparison scenarios; actual fixtures and load positions are unknown.',
                'These are nominal local reference comparisons, not measured breaking forces, allowable loads or a validated whole-part capacity.',
                'Shear, torsion, buckling, cracks, notches, delamination, fatigue, creep and stress concentrations are not solved.',
                'No infill percentage, pattern coefficient or full-solid outer-envelope substitution is used.']}
