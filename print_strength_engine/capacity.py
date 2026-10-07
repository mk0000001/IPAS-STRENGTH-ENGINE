"""Local declared-road reference scenarios and unsupported-geometry metadata."""
from math import isfinite,isclose,hypot,sqrt
from . import automatic_sections
from .process import settings as process_settings

GRAVITY=9.80665
VERSION='CAPACITY_SCENARIO_V10_COMMON_PRODUCT_REFERENCE'
AUTOMATIC_VERSION=VERSION
BASIS_ENVELOPE='OUTER_ENVELOPE_GEOMETRY_ONLY'
BASIS_PROXY='LAYER_EXTRUSION_GEOMETRY_COMPARISON_ONLY'


def _number(value,maximum=1e9):
    if isinstance(value,bool):return None
    try:value=float(value)
    except (TypeError,ValueError,OverflowError):return None
    return value if isfinite(value) and 0<value<=maximum else None


def _automatic_details_valid(deposited,axis,candidate=None):
    try:return _valid_automatic_details(deposited,axis,candidate)
    except (ValueError,TypeError,KeyError,OverflowError,ZeroDivisionError):return False


def _valid_automatic_details(deposited,axis,candidate=None):
    """Complete markers cannot replace finite required output metadata."""
    if candidate and candidate.get('kind') in automatic_sections.COMPONENT_KINDS and not automatic_sections.valid_component_selection(deposited):return False
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
    if abs(sum(value*value for value in gradient)-1)>1e-6 or abs(gradient['XYZ'.index(axis)])>1e-7:return False
    bounds=deposited.get('section_window_bounds_mm')
    if not isinstance(bounds,list) or len(bounds)!=3:return False
    if any(not isinstance(pair,list) or len(pair)!=2 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not isfinite(v) for v in pair) or pair[0]>=pair[1] for pair in bounds):return False
    if candidate is not None and bounds!=candidate.get('section_window_bounds_mm'):return False
    normal='XYZ'.index(axis);plane=[(normal+1)%3,(normal+2)%3]
    spans=[bounds[index][1]-bounds[index][0] for index in plane]
    crop_area=spans[0]*spans[1]
    def equal(left,right):
        return _number(left) is not None and _number(right) is not None and isclose(left,right,rel_tol=1e-6,abs_tol=0)
    for name in ('axial','bending'):
        section=deposited.get(name)
        if not isinstance(section,dict):return False
        if not automatic_sections.valid_plane_mechanics(section,[bounds[index] for index in plane]):return False
        area=_number(section.get('area_mm2'));station=section.get('station_mm')
        if area is None or area>crop_area+1e-6:return False
        if isinstance(station,bool) or not isinstance(station,(int,float)) or not isfinite(station) or not bounds[normal][0]<=station<=bounds[normal][1]:return False
        if candidate is not None:
            expected=candidate.get(name+'_section_station_mm',candidate.get('section_station_mm'))
            if expected is None and name=='bending':expected=candidate.get('axial_section_station_mm',candidate.get('section_station_mm'))
            if not isinstance(expected,(int,float)) or isinstance(expected,bool) or not isfinite(expected) or abs(station-expected)>1e-6:return False
        moduli=section.get('principal_section_moduli_mm3');minimum=_number(section.get('minimum_all_direction_section_modulus_mm3'))
        if not isinstance(moduli,list) or len(moduli)!=2 or any(_number(value) is None or value>area*hypot(*spans)+1e-6 for value in moduli):return False
        if minimum is None or minimum>min(moduli)+1e-6:return False
        tensor=section.get('coordinate_second_moment_mm4')
        if not isinstance(tensor,list) or len(tensor)!=2 or any(not isinstance(row,list) or len(row)!=2 for row in tensor):return False
        if any(isinstance(value,bool) or not isinstance(value,(int,float)) or not isfinite(value) for row in tensor for value in row):return False
        a,b=tensor[0];c,d=tensor[1]
        if a<=0 or d<=0 or abs(b-c)>1e-6*max(1.,abs(b),abs(c)) or a*d-b*c<=0:return False
        if any(tensor[index][index]>area*spans[index]**2/4+1e-6 for index in (0,1)):return False
        moments=section.get('principal_second_moments_mm4')
        expected=[(a+d-sqrt((a-d)**2+4*b*c))/2,(a+d+sqrt((a-d)**2+4*b*c))/2]
        if not isinstance(moments,list) or len(moments)!=2 or not all(equal(left,right) for left,right in zip(moments,expected)):return False
    if not equal(deposited.get('area_mm2'),deposited['axial']['area_mm2']):return False
    if not equal(deposited.get('minimum_all_direction_section_modulus_mm3'),deposited['bending']['minimum_all_direction_section_modulus_mm3']):return False
    if any(abs(gradient[plane[i]]-deposited['bending']['critical_stress_gradient_uv'][i])>1e-6 for i in range(2)):return False
    return True


def _common_tool_scope(tools,declared):
    """An explicit caller assumption may cover exactly the recorded tool set."""
    if not isinstance(tools,list) or not tools:return False
    if any(isinstance(tool,bool) or not isinstance(tool,int) or tool<0 for tool in tools) or len(set(tools))!=len(tools):return False
    if len(tools)==1:return True
    return isinstance(declared,list) and len(declared)==len(tools) and all(
        isinstance(tool,int) and not isinstance(tool,bool) and tool>=0 for tool in declared) and len(set(declared))==len(declared) and set(declared)==set(tools)


def capacity_for_candidate(candidate,directional_mpa,analysis=None,lever_mm=None,*,reference_area_basis='UNKNOWN',bending_supported=True,homogeneous_reference_tools=None):
    """Keep unsupported material bending out of every returned load scenario."""
    if not isinstance(bending_supported,bool):raise ValueError('INVALID_BENDING_SUPPORT_FLAG')
    result=_capacity_for_candidate(candidate,directional_mpa,analysis,lever_mm,reference_area_basis=reference_area_basis,homogeneous_reference_tools=homogeneous_reference_tools)
    tools=(candidate.get('deposited_section') or {}).get('tools')
    if result is not None and result.get('calculation_status')=='AUTOMATIC_REFERENCE_LOAD_ESTIMATE' and isinstance(tools,list) and len(tools)>1 and _common_tool_scope(tools,homogeneous_reference_tools):
        result['homogeneous_material_assumption']={'basis':'CALLER_DECLARED_COMMON_PRODUCT_REFERENCE','tool_ids':sorted(tools),'verified':False}
        result.setdefault('assessment_gaps',[]).append('MULTITOOL_COMMON_PRODUCT_HOMOGENEITY_ASSUMED')
        result.setdefault('limitations',[]).append('The caller assigns one common product reference to these tools and assumes homogeneous stiffness and perfect tool-to-tool bonding. Color, batch, moisture and boundary strength are unmeasured; no empirical homogenization or color factor is applied.')
    if result is None or bending_supported:return result
    result.update(bending_supported=False,bending_calculation_status='WITHHELD_UNSUPPORTED_MATERIAL_MODEL',
                  bending_force_n=None,bending_force_kgf=None,bending_capacity_nmm=None,bending_lever_mm=None,
                  bending_basis=None,section_modulus_mm3=None,principal_section_moduli_mm3=None,
                  weakest_local_bending_stress_gradient_xyz=None,
                  governing_capacity_n=None,governing_capacity_kgf=None,
                  governing_mode='AXIAL_REFERENCE_ONLY_BENDING_UNSUPPORTED_NOT_PART_FAILURE')
    for scenario in result.get('bending_scenarios') or []:
        scenario.update(force_n=None,force_kgf=None,calculation_status='WITHHELD_UNSUPPORTED_MATERIAL_MODEL')
    geometries=result.get('geometry_scenarios') or {}
    for name in ('declared','commanded_volume'):
        if isinstance(geometries.get(name),dict):
            geometries[name].update(bending_force_n=None,bending_calculation_status='WITHHELD_UNSUPPORTED_MATERIAL_MODEL')
    if geometries:
        geometries['selected_geometry']=None
        volume=geometries.get('selected_axial_geometry')=='COMMANDED_VOLUME_EQUIVALENT'
        result['structure_model']='LOCAL_COMMANDED_VOLUME_UNION' if volume else 'LOCAL_DECLARED_ROAD_UNION'
        result['basis']='MATERIAL_REFERENCE_TIMES_COMMANDED_VOLUME_EQUIVALENT_SECTION' if volume else 'MATERIAL_REFERENCE_TIMES_LOCAL_DECLARED_ROAD_SECTION'
        transfer=result.get('reference_transfer_assumption')
        if isinstance(transfer,dict):
            transfer['target_area_basis']=transfer.get('axial_target_area_basis') or ('COMMAND_VOLUME_EQUIVALENT_NET_SECTION' if volume else 'DECLARED_NET_ROAD_ENVELOPE')
            transfer['bending_target_area_basis']=None
    result.setdefault('assessment_gaps',[]).append('NONLINEAR_MATERIAL_BENDING_MODEL_UNSUPPORTED')
    result.setdefault('limitations',[]).append('The material reference does not support this linear bending model; only the conditional axial reference is retained.')
    return result


def _capacity_for_candidate(candidate,directional_mpa,analysis=None,lever_mm=None,*,reference_area_basis='UNKNOWN',homogeneous_reference_tools=None):
    """Compare two explicitly labelled geometric assumptions, never flow factors."""
    from copy import deepcopy
    from .local_process import valid_process_descriptor,VOLUME_PROVENANCE
    declared=_declared_capacity(candidate,directional_mpa,analysis,lever_mm,reference_area_basis=reference_area_basis,homogeneous_reference_tools=homogeneous_reference_tools)
    if declared is None:return None
    local=candidate.get('local_process')
    if not valid_process_descriptor(local) or local.get('section_window_bounds_mm')!=candidate.get('section_window_bounds_mm'):return declared
    result=deepcopy(declared);result['local_process']={k:deepcopy(v) for k,v in local.items() if k!='volume_section'}
    section=candidate.get('commanded_volume_section') or {}
    if not isinstance(section,dict):section={}
    axis=result.get('section_normal_axis');tools=section.get('tools')
    component_ambiguous=candidate.get('kind') in automatic_sections.COMPONENT_KINDS and (
        candidate.get('deposited_section',{}).get('component_count')!=1 or section.get('component_count')!=1)
    volume=None
    if not component_ambiguous and local.get('complete') is True and section.get('version')==automatic_sections.VERSION and section.get('status')=='COMPLETE' and \
       section.get('complete') is True and section.get('sampled') is False and section.get('provenance')==VOLUME_PROVENANCE and \
       section.get('scope')=='LOCAL_DECLARED_ROAD_REGION' and section.get('normal_axis')==axis and \
       section.get('width_capped_at_declared') is True and section.get('commanded_volume_is_measured') is False and \
       _common_tool_scope(tools,homogeneous_reference_tools) and tools==candidate.get('deposited_section',{}).get('tools') and \
       _automatic_details_valid(section,axis,candidate) and result.get('calculation_status')=='AUTOMATIC_REFERENCE_LOAD_ESTIMATE':
        volume=_automatic_reference(candidate,section,section['area_mm2'],section['minimum_all_direction_section_modulus_mm3'],
                                    result['material_reference_mpa'],axis,analysis,reference_area_basis)
        volume.update(structure_model='LOCAL_COMMANDED_VOLUME_UNION',basis='MATERIAL_REFERENCE_TIMES_COMMANDED_VOLUME_EQUIVALENT_SECTION')
        volume['reference_transfer_assumption']['target_area_basis']='COMMAND_VOLUME_EQUIVALENT_NET_SECTION'
        volume['limitations'].insert(0,'Programmed volume divided by path length and declared height defines an equivalent rectangle capped at declared width; this is not measured bead shape or a guaranteed capacity bound.')
    def summary(value,status='COMPLETE'):
        return {'status':status,'area_mm2':(value or {}).get('effective_load_bearing_area_mm2'),
                'bending_force_n':(value or {}).get('bending_force_n'),'axial_force_n':(value or {}).get('axial_capacity_n')}
    selected=volume is not None and volume['bending_force_n']<result['bending_force_n']
    if selected:
        context=result['local_process'];result=volume;result['local_process']=context
    axial_selected=volume is not None and volume['axial_capacity_n']<declared['axial_capacity_n']
    axial_reference=volume if axial_selected else declared
    if volume is not None:
        result.update(axial_capacity_n=axial_reference['axial_capacity_n'],axial_capacity_kgf=axial_reference['axial_capacity_kgf'],
                      effective_load_bearing_area_mm2=axial_reference['effective_load_bearing_area_mm2'],section_area_mm2=axial_reference['section_area_mm2'])
        result['governing_capacity_n']=min(result['axial_capacity_n'],result['bending_force_n'])
        result['governing_capacity_kgf']=result['governing_capacity_n']/GRAVITY
        result['reference_transfer_assumption']['axial_target_area_basis']=axial_reference['reference_transfer_assumption']['target_area_basis']
        result['reference_transfer_assumption']['bending_target_area_basis']=result['reference_transfer_assumption']['target_area_basis']
    result['geometry_scenarios']={'declared':summary(declared),
        'commanded_volume':{**summary(volume,'COMPLETE' if volume else 'WITHHELD'),
                            'assessment_gaps':(['COMMANDED_VOLUME_COMPONENT_IDENTITY_UNRESOLVED'] if component_ambiguous else
                                section.get('assessment_gaps') or ([] if volume else ['COMMANDED_VOLUME_SECTION_INCOMPLETE']))},
        'selection':'LOWER_CONDITIONAL_REFERENCE' if volume else 'DECLARED_ONLY',
        'selected_geometry':'COMMANDED_VOLUME_EQUIVALENT' if selected else 'DECLARED_ROADS',
        'selected_axial_geometry':'COMMANDED_VOLUME_EQUIVALENT' if axial_selected else 'DECLARED_ROADS',
        'is_measured':False,'temperature_strength_multiplier_applied':False}
    return result


def _declared_capacity(candidate,directional_mpa,analysis=None,lever_mm=None,*,reference_area_basis='UNKNOWN',homogeneous_reference_tools=None):
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
    if candidate.get('kind') in ({'LOCAL_THIN_SECTION'}|automatic_sections.COMPONENT_KINDS) and isinstance(deposited,dict) and deposited.get('status')=='COMPLETE' and \
       deposited.get('version')==automatic_sections.VERSION and \
       deposited.get('complete') is True and deposited.get('sampled') is False and \
       deposited.get('provenance')=='GCODE_WIDTH_HEIGHT_ASSUMPTION' and \
       deposited.get('scope')=='LOCAL_DECLARED_ROAD_REGION' and deposited.get('normal_axis')==axis:
        net_area=_number(deposited.get('area_mm2'))
        modulus=_number(deposited.get('minimum_all_direction_section_modulus_mm3'))
        tools=deposited.get('tools')
        if net_area is not None and modulus is not None and _common_tool_scope(tools,homogeneous_reference_tools) and \
           _automatic_details_valid(deposited,axis,candidate):
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
