"""Preserve process context without inventing a calibrated strength transfer."""
from math import isfinite
from copy import deepcopy
import re
from .evidence import literature_comparisons, evidence_coverage
from .calibration import calibration_eligibility

VERSION='GCODE_PROCESS_EVIDENCE_V3_THERMAL_CONTEXT'
AXES=('X','Y','Z')


def number(value,low,high):
    if isinstance(value,(list,tuple)):
        return uniform([number(item,low,high) for item in value])
    if isinstance(value,str) and re.search('[,;]',value):
        return uniform([number(item,low,high) for item in re.split('[,;]',value)])
    try:value=float(str(value).strip().rstrip('%'))
    except (TypeError,ValueError):return None
    return value if isfinite(value) and low<=value<=high else None


def numeric_values(value, low, high):
    """Preserve per-tool slots, including invalid entries; no first-tool proxy."""
    values=value if isinstance(value,(list,tuple)) else re.split('[,;]',str(value)) if value is not None else []
    return [number(item,low,high) for item in values]


def uniform(values):
    return values[0] if values and values[0] is not None and all(v==values[0] for v in values) else None


def settings(analysis):
    """Only values the scanner actually read from the file; never slicer defaults."""
    analysis=analysis or {}
    config=analysis.get('configuration') or {}
    metrics=analysis.get('process_metrics') or {}
    speeds=metrics.get('commanded_speed_mm_s') or {}
    def first(*keys):
        return next((config[k] for k in keys if config.get(k) not in (None,'')),None)
    detected=analysis.get('detected_materials')
    family_value=detected if detected else first('filament_type','material_family')
    family_values=family_value if isinstance(family_value,(list,tuple)) else [family_value]
    families={part.strip(' \"').upper() for value in family_values if value is not None
              for part in re.split('[,;]',str(value)) if part.strip(' \"')}
    family=next(iter(families)) if len(families)==1 else None
    nozzle_value=first('nozzle_diameter')
    if nozzle_value is None:nozzle_value=analysis.get('nozzle_diameter_mm')
    nozzles=numeric_values(nozzle_value,.05,3)
    width_values=[]
    for key in ('outer_wall_line_width','external_perimeter_extrusion_width','line_width','extrusion_width'):
        raw=config.get(key)
        if '%' in str(raw):continue
        values=numeric_values(raw,.05,3)
        # Auto/zero dimensions can fall through to a configured absolute width.
        # A mixed valid/invalid tool list instead retains its uncertainty.
        if any(value is not None for value in values):width_values=values;break
    width=uniform(width_values)
    width_source='GCODE_LINE_WIDTH' if width is not None else 'UNKNOWN'
    if not width_values:
        width=uniform(nozzles)
        width_source='NOZZLE_DIAMETER_ASSUMPTION' if width is not None else 'UNKNOWN'
    temperatures=numeric_values(first('nozzle_temperature','temperature'),50,600)
    bed_temperatures=numeric_values(first('bed_temperature'),0,300)
    flows=numeric_values(first('filament_flow_ratio','extrusion_multiplier'),0,5)
    return {'infill_percent':number(first('sparse_infill_density','fill_density'),0,100),
            'pattern':(str(config.get('sparse_infill_pattern') or config.get('fill_pattern') or '').strip().lower() or None),
            'walls':number(first('wall_loops','perimeters'),0,40),
            'line_width_mm':width,'line_width_source':width_source,'line_widths_mm':width_values,
            'layer_height_mm':number(config.get('layer_height') or config.get('first_layer_height'),.01,3),
            'speed_mm_s':number(speeds.get('p50_approx'),1,2000),
            'speed_basis':'COMMANDED_MOVE_MEDIAN' if number(speeds.get('p50_approx'),1,2000) is not None else None,
            'nozzle_diameter_mm':uniform(nozzles),'nozzle_diameters_mm':nozzles,
            'nozzle_c':uniform(temperatures),'nozzle_temperatures_c':temperatures,
            'bed_c':uniform(bed_temperatures),'bed_temperatures_c':bed_temperatures,
            'flow_ratio':uniform(flows),'flow_ratios':flows,
            'top_shell_layers':number(first('top_shell_layers','top_solid_layers'),0,1000),
            'bottom_shell_layers':number(first('bottom_shell_layers','bottom_solid_layers'),0,1000),
            'minimum_layer_time_setting_s':number(first('slow_down_layer_time','min_layer_time'),0,86400),
            # Slicer setpoints and duration/layer count cannot establish local heat history.
            'local_interlayer_return_time_s':None,
            'measured_substrate_temperature_c':None,
            'measured_void_fraction':None,
            'measured_bonded_contact_fraction':None,
            'chamber_c':number(first('chamber_temperature'),0,300),
            'fan_percent':number(first('fan_speed','fan_speed_percent'),0,100),
            'material_family':family,
            # A slicer profile name is not a verified manufacturer grade.
            'material_grade':first('filament_grade','material_grade'),
            'grade_identity_verified':False,
            'filament_profile':first('filament_settings_id'),
            'moisture_condition':first('moisture_condition','filament_moisture'),
            'annealing':first('annealing','anneal_condition'),
            'process_context_raw':deepcopy({k:v for k,v in config.items()
                if any(token in k.lower() for token in ('temperature','fan','moisture','anneal','grade','filament'))})}


def material_factors(analysis):
    """Identity factors are legacy placeholders, never equal-strength predictions."""
    read=settings(analysis)
    return {'version':VERSION,'status':'UNCALIBRATED_PROCESS_MODEL',
            'factor_status':'NOT_APPLIED','is_prediction':False,
            'factors':{axis:1. for axis in AXES},'applied':[],'settings':read,
            'literature_comparisons':literature_comparisons(read),
            'evidence_coverage':evidence_coverage(read),
            'calibration':calibration_eligibility(None,read),
            'limitations':['No calibrated transfer from reference coupon to target process is available.',
                           'Identity factors mean no correction applied, not unchanged physical strength.',
                           'Literature observations are not applied to target material strength or force.',
                           'Reference and target grade, thermal history, orientation and test conditions must be established.']}


def process_adjustment(analysis,directional_mpa,*,reference_context=None,target_context=None,calibration_id=None):
    """Reference data and process evidence; no effective stress without calibration."""
    if not isinstance(directional_mpa,dict):return None
    report=material_factors(analysis)
    for axis in AXES:
        base=number(directional_mpa.get(axis),0,1e5)
        if base is None:return None
    report['reference_mpa']={axis:str(directional_mpa.get(axis)) for axis in AXES}
    report['effective_mpa']=None
    report['adjusted']=False
    report['reference_context']=deepcopy(reference_context) if isinstance(reference_context,dict) else None
    report['target_context']=deepcopy(report['settings'])
    # External, authenticated measurements can add context. Observed G-code
    # fields cannot be silently overwritten with desired source conditions.
    conflicts=[]
    if isinstance(target_context,dict):
        for key,value in deepcopy(target_context).items():
            observed=report['target_context'].get(key)
            if observed is not None and key != 'grade_identity_verified' and observed != value:
                conflicts.append({'field':key,'gcode':observed,'supplied':value})
            else:
                report['target_context'][key]=value
    reference=report['reference_context'] or {}
    matching_context=deepcopy(reference.get('test_conditions')) if isinstance(reference.get('test_conditions'),dict) else {}
    matching_context.update({k:v for k,v in reference.items() if k!='test_conditions'})
    # Product name describes only the source specimen. It never establishes the
    # target spool's identity, nor substitutes a family for a manufacturer grade.
    if not matching_context.get('material_grade') and reference.get('reference_product'):
        matching_context['material_grade']=reference['reference_product']
    report['reference_matching_context']=matching_context
    report['calibration']=calibration_eligibility(matching_context,report['target_context'],model_id=calibration_id)
    if reference.get('reference_margin_applied',True) and reference.get('internal_conservative_factor') not in (None,1,1.):
        report['calibration']['blocking_reasons'].append('REFERENCE_CONTAINS_UNVALIDATED_INTERNAL_MARGIN')
        report['reference_strength_kind']='MARGIN_ADJUSTED_REFERENCE_NOT_MEASURED_ALLOWABLE'
    else:
        report['reference_strength_kind']='REFERENCE_ONLY_NOT_MEASURED_TARGET_ALLOWABLE'
    report['calibration']['target_context_conflicts']=conflicts
    if conflicts:
        report['calibration']['blocking_reasons'].append('SUPPLIED_CONTEXT_CONFLICTS_WITH_GCODE')
    return report
