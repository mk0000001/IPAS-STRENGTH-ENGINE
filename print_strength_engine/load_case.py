"""Conditional nominal normal stress of a connected declared deposition beam."""
from math import hypot,isfinite
from .deposition_section import finite_number,vector,beam_sections,UnsupportedGeometry

GRAVITY=9.80665
AREA_BASES=('UNKNOWN','GROSS_ENVELOPE','NET_MATERIAL','INTERLAYER_CONTACT')
MODEL='CONNECTED_DEPOSITION_STATIC_BEAM'
LIMITATIONS=[
    'Declared G-code widths/heights define rectangular road envelopes, not measured printed bead or void geometry.',
    'Geometric contact is not verified bonding; the scenario assumes a bonded homogeneous continuum.',
    'This slender axis-aligned piecewise constant-section beam scenario assumes planar sections and small linear-elastic deformation; it is not FEA or validated failure prediction.',
    'Stress at section changes is nominal beam stress; local stress concentrations and load redistribution are not solved.',
    'Shear failure, torsion, local force introduction, notches, cracks, delamination, buckling, fatigue and creep are not solved.',
    'No pattern efficiency, infill power-law multiplier, or nominal full-infill solid-section assumption is used.',
]


def validate_load_case(value):
    """Validate finite JSON before persistence and return a normalized copy."""
    if not isinstance(value,dict):raise ValueError('LOAD_CASE_OBJECT_REQUIRED')
    if set(value)-{'fixed_region_mm','load_point_mm','direction','force_n'}:raise ValueError('UNKNOWN_LOAD_CASE_FIELD')
    fixed=value.get('fixed_region_mm')
    if not isinstance(fixed,(list,tuple)) or len(fixed)!=3:raise ValueError('FIXED_REGION_REQUIRED')
    normalized=[]
    for pair in fixed:
        if not isinstance(pair,(list,tuple)) or len(pair)!=2:raise ValueError('FIXED_REGION_REQUIRED')
        lo,hi=[finite_number(x) for x in pair]
        if lo>=hi:raise ValueError('FIXED_REGION_MUST_HAVE_POSITIVE_EXTENT')
        normalized.append([lo,hi])
    point=vector(value.get('load_point_mm'));direction=vector(value.get('direction'));norm=hypot(*direction)
    if norm==0:raise ValueError('NONZERO_LOAD_DIRECTION_REQUIRED')
    force=value.get('force_n')
    if force is not None:
        force=finite_number(force,1e9)
        if force<=0:raise ValueError('POSITIVE_FORCE_REQUIRED')
    return {'fixed_region_mm':normalized,'load_point_mm':point,
            'direction':[v/norm for v in direction],'force_n':force}


def evaluate_load_case(load_case,geometry,directional_mpa=None,*,reference_area_basis='UNKNOWN'):
    case=validate_load_case(load_case)
    if reference_area_basis not in AREA_BASES:raise ValueError('INVALID_STRESS_AREA_BASIS')
    base={'schema_version':1,'model':MODEL,'load_case':case,'is_failure_prediction':False,
          'empirically_validated':False,'failure_load_n':None,'normal_stress_mpa':None,
          'normal_stress_per_n_mpa':None,'assessment_gaps':[],
          'limitations':list(LIMITATIONS),'calibration_status':'UNVALIDATED_CONDITIONAL_STRESS',
          'force_kgf':case['force_n']/GRAVITY if case['force_n'] is not None else None}
    try:
        sections,axis,u,v,sign,face,span=beam_sections(geometry,case)
        point=case['load_point_mm'];force=case['direction']
        maximum=-float('inf');minimum=float('inf');maximum_point=minimum_point=None
        for properties,rectangles,left,right in sections:
            cu,cv=properties['centroid_uv_mm'];ru=point[u]-cu;rv=point[v]-cv
            if abs(ru*force[v]-rv*force[u])>1e-8:raise UnsupportedGeometry('TORSION_NOT_SUPPORTED')
            tensor=properties['coordinate_second_moment_mm4'];c00,c01=tensor[0];c11=tensor[1][1]
            det=c00*c11-c01*c01
            if det<=0:raise UnsupportedGeometry('DEGENERATE_SECTION_INERTIA')
            uniform=force[axis]/properties['area_mm2']
            # Each interval has constant A, centroid and inertia. Its fiber
            # stresses are affine in station, so both endpoint limits are
            # exact extrema of this nominal model, including both step sides.
            for station in ((left,right) if sign>0 else (right,left)):
                arm=point[axis]-station
                moment_u=rv*force[axis]-arm*force[v];moment_v=arm*force[u]-ru*force[axis]
                gradient_u=(-moment_v*c11-moment_u*c01)/det
                gradient_v=(moment_u*c00+moment_v*c01)/det
                for a,b,c,d in rectangles:
                    for pu,pv in ((a,c),(a,d),(b,c),(b,d)):
                        stress=sign*(uniform+gradient_u*(pu-cu)+gradient_v*(pv-cv))
                        position=[0.,0.,0.];position[axis]=station;position[u]=pu;position[v]=pv
                        if stress>maximum:maximum=stress;maximum_point=position;maximum_section=properties
                        if stress<minimum:minimum=stress;minimum_point=position;minimum_section=properties
        extreme=max(abs(maximum),abs(minimum))
        if not isfinite(extreme):raise UnsupportedGeometry('NONFINITE_SECTION_RESPONSE')
        critical=maximum_point if abs(maximum)>=abs(minimum) else minimum_point
        section=maximum_section if abs(maximum)>=abs(minimum) else minimum_section
        section={**section,'station_mm':critical[axis]}
    except UnsupportedGeometry as error:
        return {**base,'status':'WITHHELD','assessment_gaps':[str(error)],'section':None,
                'reference_comparison':None,'beam_axis':None,'critical_section':None,'section_profile':[]}
    reference=None
    if isinstance(directional_mpa,dict):
        try:
            reference=float(directional_mpa.get('XYZ'[axis]))
            if not isfinite(reference) or not 0<reference<=1e5:reference=None
        except (TypeError,ValueError):pass
    comparison={'reference_mpa':reference,'reference_area_basis':reference_area_basis,
                'local_stress_area_basis':'DECLARED_ROAD_ENVELOPE_UNION',
                'load_at_tensile_reference_n':None,'load_at_tensile_reference_kgf':None,
                'is_failure_prediction':False,'empirically_validated':False}
    if reference_area_basis!='NET_MATERIAL':comparison['status']='INCOMPATIBLE_STRESS_AREA_BASIS'
    elif reference is None:comparison['status']='DIRECTIONAL_REFERENCE_UNAVAILABLE'
    elif maximum<=0:comparison['status']='NO_TENSILE_NORMAL_STRESS'
    else:
        comparison.update(status='CONDITIONAL_TENSILE_REFERENCE_EQUALITY',
            load_at_tensile_reference_n=reference/maximum,
            load_at_tensile_reference_kgf=reference/maximum/GRAVITY)
    return {**base,'status':'CONDITIONAL_NORMAL_STRESS','beam_axis':'XYZ'[axis],
            'section':section,'section_profile':[item[0] for item in sections],
            'free_span_mm':span,'reference_comparison':comparison,
            'normal_stress_per_n_mpa':extreme,
            'normal_stress_mpa':extreme*case['force_n'] if case['force_n'] is not None else None,
            'tensile_normal_stress_per_n_mpa':max(0.,maximum),
            'compressive_normal_stress_per_n_mpa':max(0.,-minimum),
            'critical_section':{'position_mm':critical,'station_mm':critical[axis],
                'basis':'MAX_ENDPOINT_NOMINAL_BEAM_STRESS' if section['section_geometry_status']=='CONNECTED_PRISMATIC_ROAD_ENVELOPE'
                        else 'MAX_INTERVAL_ENDPOINT_NOMINAL_BEAM_STRESS'},
            'assessment_gaps':['PRINTED_BEAD_AND_BOND_GEOMETRY_UNMEASURED',
                               'SHEAR_AND_FAILURE_MECHANISMS_NOT_SOLVED','NO_MATCHED_PART_FAILURE_TESTS']}
