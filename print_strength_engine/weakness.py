"""Integrated, mechanism-specific weakness assessment without invented weld laws.

Geometry, conditional reference loads, and declared interlayer contact have
different evidential meanings. Their diagnostics are retained separately; a
shared local reference scenario is the only numeric load-ranking basis here.
"""
from copy import deepcopy
from math import isfinite, isclose

VERSION='INTEGRATED_WEAKNESS_V4_COMMON_PRODUCT_REFERENCE'
GEOMETRY_BASIS='GEOMETRIC_SECTION_COMPARISON'
LOAD_BASIS='COMPARABLE_LOCAL_25MM_REFERENCE_LOADS'
COMPONENT_LOAD_BASIS='COMPARABLE_COMPONENT_25MM_REFERENCE_LOADS'
COMPONENT_AXIAL_BASIS='COMPARABLE_COMPONENT_AXIAL_REFERENCE_LOADS'
COMPONENT_GEOMETRY_BASIS='COMPONENT_REFERENCE_GEOMETRY_ORDER'
COMPONENT_KINDS=frozenset(('COMPONENT_NECK_SECTION','COMPONENT_REFERENCE_SECTION'))


def _finite(value,positive=False):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and isfinite(value) and (not positive or value>0)


def _reference_number(value):
    if isinstance(value,bool) or not isinstance(value,(int,float,str)):return None
    try:number=float(value)
    except (TypeError,ValueError,OverflowError):return None
    return number if isfinite(number) and 0<number<=100000 else None


def _common_reference_valid(value,tools,axis):
    if axis not in ('X','Y','Z'):return False
    assumption=value.get('homogeneous_material_assumption')
    reference=value.get('material_reference_provenance')
    if not isinstance(assumption,dict) or not isinstance(reference,dict):return False
    common=reference.get('common_product_tool_reference')
    if not isinstance(common,dict):return False
    if assumption.get('basis')!='CALLER_DECLARED_COMMON_PRODUCT_REFERENCE' or assumption.get('verified') is not False or assumption.get('tool_ids')!=sorted(tools):return False
    if common.get('basis')!='IDENTICAL_EXACT_PRODUCT_COUPON_REFERENCE_PER_TOOL' or common.get('verified') is not False or common.get('units')!='MPa' or common.get('tool_ids')!=sorted(tools):return False
    for key in ('reference_product','source_ref'):
        if not isinstance(common.get(key),str) or not common[key].strip() or common[key]!=reference.get(key):return False
    for field,axes in (('raw_reference_mpa',('XY','Z')),('directional_capacity_reference_mpa',('X','Y','Z'))):
        data=common.get(field)
        if not isinstance(data,dict) or data!=reference.get(field):return False
        if any(_reference_number(data.get(name)) is None for name in axes):return False
    basis=common.get('stress_area_basis')
    if basis not in ('UNKNOWN','NET_MATERIAL','GROSS_ENVELOPE','INTERLAYER_CONTACT') or basis!=reference.get('stress_area_basis') or basis!=value.get('reference_stress_area_basis'):return False
    bending=common.get('bending_supported')
    if not isinstance(bending,bool) or bending is not value.get('bending_supported',True):return False
    actual=_reference_number(value.get('material_reference_mpa'))
    expected=_reference_number(common['directional_capacity_reference_mpa'].get(axis))
    return actual is not None and expected is not None and isclose(actual,expected,rel_tol=1e-9,abs_tol=1e-9)


def _contact(candidate):
    from .interlayer_contact import VERSION as CONTACT_VERSION
    value=candidate.get('interlayer_contact')
    if not isinstance(value,dict) or value.get('version')!=CONTACT_VERSION:return None
    if value.get('status')!='COMPLETE' or value.get('complete') is not True or value.get('sampled') is not False:return None
    if value.get('provenance')!='GCODE_WIDTH_HEIGHT_ASSUMPTION' or value.get('scope')!='LOCAL_DECLARED_ROAD_INTERLAYER_WINDOW':return None
    if value.get('section_window_bounds_mm')!=candidate.get('section_window_bounds_mm'):return None
    if value.get('actual_bond_measured') is not False or value.get('molecular_weld_quality_verified') is not False:return None
    for name in ('interfaces_checked','qualifying_interface_count'):
        count=value.get(name)
        if not isinstance(count,int) or isinstance(count,bool) or count<0:return None
    if value['qualifying_interface_count']>value['interfaces_checked']:return None
    ratio=value.get('minimum_smaller_footprint_overlap_ratio')
    if ratio is not None and (not _finite(ratio) or not 0<=ratio<=1):return None
    if value['qualifying_interface_count']>0 and ratio is None:return None
    if not isinstance(value.get('observations'),list):return None
    return value


def _load_key(candidate,*,axial_only=False):
    from .capacity import VERSION as CAPACITY_VERSION
    from .automatic_sections import VERSION as SECTION_VERSION
    value=candidate.get('estimated_capacity') or {};section=candidate.get('deposited_section') or {}
    volume_selected=value.get('structure_model')=='LOCAL_COMMANDED_VOLUME_UNION'
    if volume_selected:section=candidate.get('commanded_volume_section') or {}
    if candidate.get('screening_quality')=='RESOLUTION_LIMITED_FEATURE':return None
    if value.get('model_version')!=CAPACITY_VERSION:return None
    if value.get('calculation_status')!='AUTOMATIC_REFERENCE_LOAD_ESTIMATE' or value.get('is_failure_prediction') is not False:return None
    if axial_only:
        if value.get('bending_supported') is not False or not _finite(value.get('axial_capacity_n'),True):return None
    elif value.get('bending_basis')!='MINIMUM_OVER_ALL_LOCAL_MOMENT_DIRECTIONS' or not _finite(value.get('bending_force_n'),True) or value.get('bending_lever_mm')!=25:return None
    tools=section.get('tools')
    if section.get('version')!=SECTION_VERSION or section.get('status')!='COMPLETE' or section.get('complete') is not True or section.get('sampled') is not False:return None
    provenance='GCODE_COMMANDED_VOLUME_RECTANGULAR_EQUIVALENT' if volume_selected else 'GCODE_WIDTH_HEIGHT_ASSUMPTION'
    if section.get('normal_axis')!=candidate.get('section_normal_axis') or section.get('scope')!='LOCAL_DECLARED_ROAD_REGION' or section.get('provenance')!=provenance:return None
    if not isinstance(tools,list) or not tools:return None
    if any(isinstance(tool,bool) or not isinstance(tool,int) or tool<0 for tool in tools):return None
    if len(set(tools))!=len(tools):return None
    if len(tools)>1 and not _common_reference_valid(value,tools,section.get('normal_axis')):return None
    basis=value.get('reference_stress_area_basis')
    if basis not in ('UNKNOWN','NET_MATERIAL','GROSS_ENVELOPE','INTERLAYER_CONTACT'):return None
    transfer=value.get('reference_transfer_assumption')
    if not isinstance(transfer,dict) or transfer.get('source_area_basis')!=basis:return None
    target='COMMAND_VOLUME_EQUIVALENT_NET_SECTION' if volume_selected else 'DECLARED_NET_ROAD_ENVELOPE'
    if transfer.get('target_area_basis')!=target or transfer.get('basis')!='COUPON_REFERENCE_AS_HOMOGENEOUS_NET_SECTION_STRESS':return None
    if not isinstance(transfer.get('verified'),bool):return None
    comparison=(value.get('geometry_scenarios') or {}).get('selection',target)
    return tuple(tools),basis,comparison,transfer['basis'],transfer['verified'],candidate.get('material_reference_id'),candidate.get('source_sha256')


def _component_load_key(candidate):
    from .automatic_sections import valid_component_selection
    capacity=candidate.get('estimated_capacity') or {}
    section=candidate.get('commanded_volume_section') if capacity.get('structure_model')=='LOCAL_COMMANDED_VOLUME_UNION' else candidate.get('deposited_section')
    if not valid_component_selection(section):return None
    key=_load_key(candidate)
    if key is not None:return ('BENDING',key)
    key=_load_key(candidate,axial_only=True)
    return ('AXIAL',key) if key is not None else None


def assess_candidates(candidates):
    """Return an immutable integrated assessment and consistently numbered rows.

    Missing/incompatible reference evidence keeps the geometric ordering intact.
    Good geometric contact never verifies molecular welding or removes an
    end-feature delamination warning. No overlap-to-MPa conversion is performed.
    """
    rows=deepcopy(list(candidates or []));local=[row for row in rows if row.get('kind')=='LOCAL_THIN_SECTION']
    keys=[_load_key(row) for row in local]
    comparable=bool(keys) and all(key is not None and key==keys[0] for key in keys)
    basis=LOAD_BASIS if comparable else GEOMETRY_BASIS
    references=[row for row in rows if row.get('kind') in COMPONENT_KINDS]
    reference_keys={id(row):_component_load_key(row) for row in references}
    ready=[row for row in references if reference_keys[id(row)] is not None]
    reference_comparable=bool(ready) and all(reference_keys[id(row)]==reference_keys[id(ready[0])] for row in ready)
    reference_basis=(COMPONENT_LOAD_BASIS if reference_keys[id(ready[0])][0]=='BENDING' else COMPONENT_AXIAL_BASIS) if reference_comparable else COMPONENT_GEOMETRY_BASIS
    for index,row in enumerate(rows):
        row.setdefault('geometry_rank',row.get('rank',index+1))
        mechanisms=[];gaps=[];contact=None
        if row.get('kind')=='LOCAL_THIN_SECTION':
            terminal=row.get('end_role') in ('LOW_END','HIGH_END') or 'TERMINAL_ROOT' in str(row.get('selection_reason',''))
            mechanisms.append('TERMINAL_ROOT_BENDING' if terminal else 'LOCAL_THIN_SECTION_BENDING')
            if row.get('terminal_kind')=='OBJECT_FREE_END':mechanisms.append('FREE_EDGE_LAYER_SEPARATION_EXPOSURE')
            if row.get('selection_reason')=='LOCAL_SECTION_REDUCTION':mechanisms.append('LOCAL_SECTION_REDUCTION')
            contact=_contact(row)
            if contact:
                kinds={observation.get('kind') for observation in contact['observations'] if isinstance(observation,dict)}
                kinds.update(kind for kind in contact.get('observation_kinds',[]) if isinstance(kind,str))
                mechanisms.extend(sorted(kinds & {'LOW_DECLARED_LAYER_OVERLAP','DECLARED_VERTICAL_GAP','NO_DECLARED_LAYER_OVERLAP','OVERLAPPING_DECLARED_LAYER_INTERVALS'}))
                if contact['qualifying_interface_count']==0:gaps.append('NO_QUALIFYING_LOCAL_INTERFACE')
            else:gaps.append('COMPLETE_DECLARED_CONTACT_DIAGNOSTIC_REQUIRED')
        elif row.get('kind') in COMPONENT_KINDS:
            mechanisms.append('COMPONENT_NECK_ROAD_SECTION_COMPARISON' if row.get('kind')=='COMPONENT_NECK_SECTION' else 'REPRESENTATIVE_COMPONENT_ROAD_SECTION')
            gaps.append('CONNECTED_ROAD_POLYGON_NOT_VERIFIED_SOURCE_OBJECT_ID')
        else:mechanisms.append('LAYER_EXTRUSION_CONSTRICTION_COMPARISON')
        gaps.extend(['MOLECULAR_WELD_STRENGTH_UNMEASURED','LOCAL_BOND_THERMAL_HISTORY_UNMEASURED',
                     'WHOLE_PART_RESTRAINT_AND_LOAD_PATH_UNVERIFIED','NOTCH_CRACK_AND_FATIGUE_UNCALIBRATED'])
        row['weakness_assessment']={'version':VERSION,'mechanisms':list(dict.fromkeys(mechanisms)),
            'selection_reason':row.get('selection_reason',row.get('reason')),
            'contact_geometry_status':'COMPLETE' if contact else 'UNAVAILABLE',
            'minimum_smaller_footprint_overlap_ratio':contact.get('minimum_smaller_footprint_overlap_ratio') if contact else None,
            'qualifying_interface_count':contact['qualifying_interface_count'] if contact else 0,
            'contact_observations':deepcopy(contact['observations']) if contact else [],
            'contact_observation_count':contact.get('observation_count',len(contact['observations'])) if contact else 0,
            'contact_observations_sampled':bool(contact.get('observations_sampled')) if contact else False,
            'weld_strength_status':'UNMEASURED','interlayer_failure_load_n':None,
            'mechanism_evaluations':{'local_section_geometry':'GEOMETRIC_SCREENING',
                'terminal_root':'GEOMETRIC_EXPOSURE' if row.get('terminal_kind') else 'NOT_DETECTED',
                'axial_and_bending':'CONDITIONAL_REFERENCE_SCENARIOS' if _load_key(row) is not None else 'AXIAL_REFERENCE_ONLY_BENDING_WITHHELD' if _load_key(row,axial_only=True) is not None else 'INCOMPLETE_OR_INCOMPATIBLE_EVIDENCE',
                'declared_interlayer_contact':'GEOMETRIC_DIAGNOSTIC' if contact else 'UNAVAILABLE',
                'interlayer_opening_and_tearing':'MATCHED_FRACTURE_PROPERTIES_REQUIRED',
                'notch_and_crack_growth':'MATCHED_GEOMETRY_AND_FRACTURE_PROPERTIES_REQUIRED',
                'shear_torsion_buckling_fatigue_creep':'NOT_SOLVED'},
            'commanded_process_context':deepcopy((row.get('estimated_capacity') or {}).get('structure_settings')),
            'is_failure_prediction':False,'empirically_validated':False,
            'assessment_gaps':gaps,'reference_load_rank_comparable':reference_comparable if row.get('kind') in COMPONENT_KINDS else comparable if row.get('kind')=='LOCAL_THIN_SECTION' else False}
    if comparable:
        local.sort(key=lambda row:(row['estimated_capacity']['bending_force_n'],row['geometry_rank'],str(row.get('region_id',''))))
    else:
        # A previously load-ranked snapshot may lose its material reference.
        # Available reference loads represent the file before withheld rows.
        # Within each group, restore geometry order without comparing unlike
        # material/section assumptions or claiming an actual failure ranking.
        local.sort(key=lambda row:(_load_key(row) is None and _load_key(row,axial_only=True) is None,
                                   row['geometry_rank'],str(row.get('region_id',''))))
    geometry_order=lambda row:(row['geometry_rank'],str(row.get('region_id','')))
    if reference_comparable:
        force='bending_force_n' if reference_keys[id(ready[0])][0]=='BENDING' else 'axial_capacity_n'
        ready.sort(key=lambda row:(row['estimated_capacity'][force],*geometry_order(row)))
    else:ready.sort(key=geometry_order)
    withheld=sorted((row for row in references if reference_keys[id(row)] is None),key=geometry_order)
    reference_fallback=bool(ready) and not any(_load_key(row) is not None or _load_key(row,axial_only=True) is not None for row in local)
    primary=ready+local if reference_fallback else local+ready
    rows=primary+withheld+[row for row in rows if row.get('kind')!='LOCAL_THIN_SECTION' and row.get('kind') not in COMPONENT_KINDS]
    for index,row in enumerate(rows):
        row.update(rank=index+1,rank_basis=basis if row.get('kind')=='LOCAL_THIN_SECTION' else reference_basis if row.get('kind') in COMPONENT_KINDS and reference_keys[id(row)] is not None else COMPONENT_GEOMETRY_BASIS if row.get('kind') in COMPONENT_KINDS else 'LAYER_GEOMETRY_COMPARISON')
        row['weakness_assessment']['rank_basis']=row['rank_basis']
    return {'version':VERSION,'status':'CANDIDATES_ASSESSED' if rows else 'NO_CANDIDATES',
            'rank_basis':reference_basis if reference_fallback else basis if local or not references else reference_basis,'is_failure_prediction':False,'empirically_validated':False,
            'candidate_scope':'BOUNDED_LOCAL_SCREENING_CANDIDATES',
            'reference_lever_mm':25 if comparable or reference_comparable and reference_basis==COMPONENT_LOAD_BASIS else None,'candidates':rows,
            'coverage':{'geometry_screening':bool(local or references),'reference_load_comparison':comparable or reference_comparable,
                        'declared_interlayer_contact':sum(row['weakness_assessment']['contact_geometry_status']=='COMPLETE' for row in local),
                        'molecular_weld_strength':False,'whole_part_first_fracture':False}}
