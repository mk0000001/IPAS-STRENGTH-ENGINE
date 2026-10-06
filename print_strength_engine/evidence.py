"""Curated primary observations, never a strength-transfer or calibration model.

Sources were checked in reports/strength-empirical-validation-20260925.md.
Keep test property, conditions and derivation attached to every numeric value.
"""
from copy import deepcopy
import json
from pathlib import Path
from .calibration import compare_contexts
from .provenance import prepare_provenance_map, catalog_provenance

VERSION = 'PRIMARY_LITERATURE_COMPARISONS_V3_OBSERVATION_PROVENANCE'

_CATALOG = [
    {
        'source_id': 'S050', 'doi': '10.3390/ma16134574',
        'source_url': 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10342851/fullTextXML',
        'locator': 'Methods/Table 4; Results/Table 6; conclusion',
        'property': 'tensile_strength', 'material_family': 'PLA',
        'material_grade': 'PrimaSelect PLA PRO', 'comparison_variable': 'layer_height_mm',
        'source_context': {'printer': 'Wanhao Duplicator i3 Plus', 'nozzle_c': 210,
                           'bed_c': 60, 'speed_mm_s': 50, 'speed_basis': 'PRINT_SETTING',
                           'infill_percent': 75, 'pattern': 'cubic', 'wall_thickness_mm': .6,
                           'top_bottom_thickness_mm': .6, 'annealing': 'none',
                           'test_standard': 'ASTM D638-14 Type I',
                           'load_axis_relative_to_build': None, 'moisture_condition': None},
        'observations': [
            {'layer_height_mm': .1, 'value_mpa': 32.15,
             'value_kind': 'DERIVED_FROM_REPORTED_VALUES', 'derivation': '33.37 - 1.22 MPa',
             'sd_mpa': None, 'n': None},
            {'layer_height_mm': .2, 'value_mpa': 30.07,
             'value_kind': 'REPORTED', 'sd_mpa': None, 'n': None}],
        'observed_ratio': 30.07 / 32.15, 'ratio_definition': '0.2 mm / 0.1 mm, unannealed',
        'statistical_comparison': 'DISPERSION_NOT_VERIFIED',
        'limitations': ['0.1 mm baseline is derived from rounded reported values.',
                        'Load axis and replicate dispersion were not verified.',
                        'Reported print speed is not a measured commanded-speed median.',
                        'Do not apply this ratio to another grade, part, or process.'],
    },
    {
        'source_id': 'S088', 'doi': '10.3390/app10093170',
        'source_url': 'https://www.mdpi.com/2076-3417/10/9/3170',
        'locator': 'Methods; Table 3 experimental UTS columns (not datasheet columns)',
        'property': 'tensile_strength', 'material_family': 'PEI',
        'material_grade': 'ULTEM 9085', 'comparison_variable': 'orientation',
        'source_context': {'printer': 'Fortus 450mc', 'infill_percent': 100,
                           'walls': 3, 'line_width_mm': .508, 'air_gap_mm': 0,
                           'raster_angles_deg': [-45, 45],
                           'test_standard': 'ASTM D638-14 Type I',
                           'crosshead_speed_mm_min': 5, 'nozzle_c': None,
                           'layer_height_mm': None, 'speed_mm_s': None},
        'observations': [
            {'orientation': 'XY', 'load_axis': 'X', 'value_mpa': 65.9,
             'sd_mpa': .7, 'n': 5, 'tukey_subset': 'b', 'value_kind': 'REPORTED'},
            {'orientation': 'XZ', 'load_axis': 'X', 'value_mpa': 73.,
             'sd_mpa': 1.3, 'n': 5, 'tukey_subset': 'b', 'value_kind': 'REPORTED'}],
        'observed_ratio': 65.9 / 73., 'ratio_definition': 'XY / XZ',
        'statistical_comparison': 'SAME_TUKEY_GROUP',
        'limitations': ['Orientation labels retain largest-face plane as well as longitudinal axis.',
                        'Different means in the same Tukey group do not establish statistical significance.',
                        'These observations do not validate a material reference or transfer model.'],
    },
]

for _family, _mean, _sd, _n in [('PLA', 25.74, 1.03, 10), ('ABS', 23.01, 1.63, 10), ('PC', 30.16, 1.64, 9)]:
    _CATALOG.append({
        'source_id': 'S028', 'doi': '10.1016/j.jmrt.2022.12.147',
        'source_url': 'https://doi.org/10.1016/j.jmrt.2022.12.147', 'locator': 'Table 2',
        'property': 'interlayer_shear_strength', 'material_family': _family,
        'material_grade': None, 'comparison_variable': None,
        'source_context': {'test_method': 'necking-shaped pure shear', 'print_surface_angle_deg': 90,
                           'printer': None, 'nozzle_c': None, 'layer_height_mm': None,
                           'speed_mm_s': None, 'infill_percent': None},
        'observations': [{'value_mpa': _mean, 'sd_mpa': _sd, 'n': _n, 'value_kind': 'REPORTED'}],
        'observed_ratio': None, 'ratio_definition': None,
        'statistical_comparison': 'REPORTED_MEAN_AND_STANDARD_DEVIATION',
        'limitations': ['Interlayer shear cannot be substituted for Z tensile or bending strength.',
                        'Grade and deposition conditions have not been independently verified.'],
    })

# Public raw-curve evidence retains source hashes and individual specimen
# calculations. These observations expand comparison coverage, not calibration.
_CATALOG.extend(json.loads(Path(__file__).with_name('public_tensile_catalog.json').read_text(encoding='utf-8')))
_CATALOG.extend(json.loads(Path(__file__).with_name('process_interaction_catalog.json').read_text(encoding='utf-8')))
_RESEARCH_COVERAGE=json.loads(Path(__file__).with_name('research_coverage_catalog.json').read_text(encoding='utf-8'))


def literature_comparisons(target_context, *, property_name='tensile_strength', provenance_map=None):
    """Return same-family observations with applicability gaps, never a factor.

    Callers must request shear explicitly. Exact grade text is only an identity
    match; it does not establish matching test conditions or validated transfer.
    No material family is inferred from a slicer profile or an unknown grade.
    """
    target = deepcopy(target_context) if isinstance(target_context, dict) else {}
    family = str(target.get('material_family') or '').strip().upper()
    grade = str(target.get('material_grade') or '').strip().casefold()
    rows = []
    prepared_map = prepare_provenance_map(provenance_map)
    for entry in _CATALOG:
        if entry['material_family'] != family or entry['property'] != property_name:
            continue
        row = deepcopy(entry)
        source_grade = str(row['material_grade'] or '').strip().casefold()
        row.update({'evidence_version': VERSION, 'status': 'LITERATURE_COMPARISON_ONLY',
                    'confidence': 'OBSERVATIONS_VERIFIED_TRANSFER_UNVALIDATED',
                    'applied': False, 'is_prediction': False, 'transfer_factor': None,
                    'material_match': 'EXACT_GRADE_NAME_ONLY' if grade and source_grade == grade
                                      else 'SAME_FAMILY_NOT_GRADE_MATCH',
                    'target_context': deepcopy(target), 'condition_mismatches': [],
                    'unknown_conditions': []})
        for key, source_value in row['source_context'].items():
            target_value = target.get(key)
            if source_value is None or target_value is None:
                row['unknown_conditions'].append(key)
            elif source_value != target_value:
                row['condition_mismatches'].append({'field': key, 'source': source_value, 'target': target_value})
        variable = row['comparison_variable']
        source_context = dict(row['source_context'], material_family=row['material_family'],
                              material_grade=row['material_grade'], property=row['property'])
        row['calibration_context_match'] = compare_contexts(source_context, target,
                                                           varying=(variable,) if variable else ())
        identity = catalog_provenance(entry, prepared_map)
        row.update(identity)
        row['experimental_lineage_id'] = identity['experimental_lineages'][0] if len(identity['experimental_lineages']) == 1 else None
        row['provenance_map'] = deepcopy(prepared_map[0])
        row['runtime_calibration_eligible'] = False
        row['calibration_blocking_reason'] = 'NO_INDEPENDENTLY_VALIDATED_TRANSFER_MODEL'
        if variable:
            observed = [o[variable] for o in row['observations']]
            row['target_within_observed_levels'] = target.get(variable) in observed
            row['applicability'] = ('OBSERVED_LEVEL_ONLY_NOT_VALIDATED_TRANSFER'
                                    if row['target_within_observed_levels'] else
                                    'TARGET_LEVEL_UNKNOWN' if target.get(variable) is None else
                                    'OUTSIDE_OBSERVED_LEVELS')
            if not row['target_within_observed_levels']:
                row['observed_ratio'] = None
        else:
            row['applicability'] = 'PROPERTY_OBSERVATION_ONLY'
        rows.append(row)
    return rows


def evidence_coverage(target_context, *, property_name='tensile_strength', provenance_map=None):
    """Every requested family gets an explicit evidence status, including gaps.

    Keep property-filtered numeric observations separate from family-level
    research coverage. A reviewed shear/load/temperature study is evidence but
    cannot fill a tensile-process calibration gap. Candidate source URLs in an
    INSUFFICIENT research row do not imply verified numerical observations.
    """
    target=target_context if isinstance(target_context,dict) else {}
    family=str(target.get('material_family') or '').strip().upper()
    matching=[r for r in _CATALOG if r['material_family']==family and r['property']==property_name]
    prepared_map=prepare_provenance_map(provenance_map)
    identities=[catalog_provenance(r,prepared_map) for r in matching]
    publications=sorted({p for r in identities for p in r['publication_ids']})
    campaigns=sorted({p for r in identities for p in r['experimental_lineages']})
    other=sorted({r['property'] for r in _CATALOG if r['material_family']==family and r['property']!=property_name})
    researched=next((deepcopy(r) for r in _RESEARCH_COVERAGE['materials'] if r['material_family']==family),None)
    numeric_status='COMPARISON_EVIDENCE_ONLY' if matching else 'NO_MATCHING_CURATED_PROPERTY_EVIDENCE'
    status=numeric_status
    if not matching and researched:
        status=('RESEARCH_COMPARISON_ONLY' if researched['status']=='COMPARISON_ONLY'
                else 'RESEARCH_REVIEWED_INSUFFICIENT')
    return {'version':VERSION,'material_family':family or None,'property':property_name,
            'status':status,
            'experimental_lineages':campaigns,
            'publication_ids':publications,'publication_count':len(publications),
            'declared_campaigns':sorted({p for r in identities for p in r['declared_campaigns']}),
            'canonical_campaigns':sorted({p for r in identities for p in r['canonical_campaigns']}),
            'independent_validation_established':False,
            'provenance_map':deepcopy(prepared_map[0]),
            'unresolved_observation_count':sum(bool(p['errors']) or p['canonical_campaign_id'] is None
                for r in identities for p in r['observation_provenance']),
            'comparison_count':len(matching),'other_properties_available':other,
            'approved_transfer_models':0,'effective_mpa':None,
            'grade_identity_verified':target.get('grade_identity_verified') is True,
            'scope':'NUMERIC_CATALOG_AND_REGISTERED_MATERIAL_RESEARCH_COVERAGE',
            'curated_numeric_catalog':{
                'status':numeric_status,'property':property_name,'comparison_count':len(matching),
                'source_urls':sorted({r['source_url'] for r in matching}),
                'is_runtime_calibration':False},
            'researched_comparison_evidence':{
                'status':researched['status'] if researched else 'NOT_IN_REGISTERED_MATERIAL_RESEARCH_MATRIX',
                'source_urls':researched['source_urls'] if researched else [],
                'reason':researched['reason'] if researched else 'No registered-material research row; numeric catalog is reported separately.',
                'scope':'FAMILY_LEVEL_RESEARCH_MULTIPLE_PROPERTIES',
                'requested_property_match':'NOT_ASSERTED_BY_FAMILY_COVERAGE',
                'is_runtime_calibration':False,'independent_holdout_n':0},
            'research_manifest':{
                'version':_RESEARCH_COVERAGE['version'],
                'registered_material_count':_RESEARCH_COVERAGE['registered_material_count'],
                'source_coverage_sha256':_RESEARCH_COVERAGE['source_coverage_sha256'],
                'source_manifest_sha256':_RESEARCH_COVERAGE['source_manifest_sha256']},
            'registered_material_coverage':deepcopy(_RESEARCH_COVERAGE['materials'])}


def research_coverage_catalog():
    """Portable all-registered-material research matrix plus acquisition hashes."""
    return deepcopy(_RESEARCH_COVERAGE)
