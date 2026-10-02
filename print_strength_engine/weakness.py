"""Integrated, mechanism-specific weakness assessment without invented weld laws.

Geometry, conditional reference loads, and declared interlayer contact have
different evidential meanings. Their diagnostics are retained separately; a
shared local reference scenario is the only numeric load-ranking basis here.
"""
from copy import deepcopy
from math import isfinite

VERSION='INTEGRATED_WEAKNESS_V2_LOCAL_PROCESS_CONTEXT'
GEOMETRY_BASIS='GEOMETRIC_SECTION_COMPARISON'
LOAD_BASIS='COMPARABLE_LOCAL_25MM_REFERENCE_LOADS'


def _finite(value,positive=False):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and isfinite(value) and (not positive or value>0)


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


def _load_key(candidate):
    from .capacity import VERSION as CAPACITY_VERSION
    from .automatic_sections import VERSION as SECTION_VERSION
    value=candidate.get('estimated_capacity') or {};section=candidate.get('deposited_section') or {}
    volume_selected=value.get('structure_model')=='LOCAL_COMMANDED_VOLUME_UNION'
    if volume_selected:section=candidate.get('commanded_volume_section') or {}
    if candidate.get('screening_quality')=='RESOLUTION_LIMITED_FEATURE':return None
    if value.get('model_version')!=CAPACITY_VERSION or value.get('bending_basis')!='MINIMUM_OVER_ALL_LOCAL_MOMENT_DIRECTIONS':return None
    if value.get('calculation_status')!='AUTOMATIC_REFERENCE_LOAD_ESTIMATE' or value.get('is_failure_prediction') is not False:return None
    if not _finite(value.get('bending_force_n'),True) or value.get('bending_lever_mm')!=25:return None
    tools=section.get('tools')
    if section.get('version')!=SECTION_VERSION or section.get('status')!='COMPLETE' or section.get('complete') is not True or section.get('sampled') is not False:return None
    provenance='GCODE_COMMANDED_VOLUME_RECTANGULAR_EQUIVALENT' if volume_selected else 'GCODE_WIDTH_HEIGHT_ASSUMPTION'
    if section.get('normal_axis')!=candidate.get('section_normal_axis') or section.get('scope')!='LOCAL_DECLARED_ROAD_REGION' or section.get('provenance')!=provenance:return None
    if not isinstance(tools,list) or len(tools)!=1:return None
    if isinstance(tools[0],bool) or not isinstance(tools[0],int) or tools[0]<0:return None
    basis=value.get('reference_stress_area_basis')
    if basis not in ('UNKNOWN','NET_MATERIAL','GROSS_ENVELOPE','INTERLAYER_CONTACT'):return None
    transfer=value.get('reference_transfer_assumption')
    if not isinstance(transfer,dict) or transfer.get('source_area_basis')!=basis:return None
    target='COMMAND_VOLUME_EQUIVALENT_NET_SECTION' if volume_selected else 'DECLARED_NET_ROAD_ENVELOPE'
    if transfer.get('target_area_basis')!=target or transfer.get('basis')!='COUPON_REFERENCE_AS_HOMOGENEOUS_NET_SECTION_STRESS':return None
    if not isinstance(transfer.get('verified'),bool):return None
    comparison=(value.get('geometry_scenarios') or {}).get('selection',target)
    return tools[0],basis,comparison,transfer['basis'],transfer['verified'],candidate.get('material_reference_id'),candidate.get('source_sha256')


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
                'axial_and_bending':'CONDITIONAL_REFERENCE_SCENARIOS' if _load_key(row) is not None else 'INCOMPLETE_OR_INCOMPATIBLE_EVIDENCE',
                'declared_interlayer_contact':'GEOMETRIC_DIAGNOSTIC' if contact else 'UNAVAILABLE',
                'interlayer_opening_and_tearing':'MATCHED_FRACTURE_PROPERTIES_REQUIRED',
                'notch_and_crack_growth':'MATCHED_GEOMETRY_AND_FRACTURE_PROPERTIES_REQUIRED',
                'shear_torsion_buckling_fatigue_creep':'NOT_SOLVED'},
            'commanded_process_context':deepcopy((row.get('estimated_capacity') or {}).get('structure_settings')),
            'is_failure_prediction':False,'empirically_validated':False,
            'assessment_gaps':gaps,'reference_load_rank_comparable':comparable}
    if comparable:
        local.sort(key=lambda row:(row['estimated_capacity']['bending_force_n'],row['geometry_rank'],str(row.get('region_id',''))))
    else:
        # A previously load-ranked snapshot may lose its material reference.
        # Restore the original geometric order instead of relabeling stale ranks.
        local.sort(key=lambda row:(row['geometry_rank'],str(row.get('region_id',''))))
    rows=local+[row for row in rows if row.get('kind')!='LOCAL_THIN_SECTION']
    for index,row in enumerate(rows):
        row.update(rank=index+1,rank_basis=basis if row.get('kind')=='LOCAL_THIN_SECTION' else 'LAYER_GEOMETRY_COMPARISON')
        row['weakness_assessment']['rank_basis']=row['rank_basis']
    return {'version':VERSION,'status':'CANDIDATES_ASSESSED' if rows else 'NO_CANDIDATES',
            'rank_basis':basis,'is_failure_prediction':False,'empirically_validated':False,
            'candidate_scope':'BOUNDED_LOCAL_SCREENING_CANDIDATES',
            'reference_lever_mm':25 if comparable else None,'candidates':rows,
            'coverage':{'geometry_screening':bool(local),'reference_load_comparison':comparable,
                        'declared_interlayer_contact':sum(row['weakness_assessment']['contact_geometry_status']=='COMPLETE' for row in local),
                        'molecular_weld_strength':False,'whole_part_first_fracture':False}}
