"""Reproduce eligibility/arithmetical checks for the bundled public tensile data.

Usage: python -m print_strength_engine.public_validation --output report.json
This verifies the saved extraction and explains why it cannot calibrate a
process transfer. It does not pretend to re-download/re-extract XLSX curves.
"""
import argparse
from hashlib import sha256
import json
from math import isclose
from pathlib import Path
from statistics import mean, stdev

from .calibration import validate_linear_candidate


def public_data_report():
    path=Path(__file__).with_name('public_tensile_catalog.json')
    catalog=json.loads(path.read_text(encoding='utf-8'))
    result={'status':'COMPARISON_DATA_ONLY','catalog_sha256':sha256(path.read_bytes()).hexdigest(),
            'is_empirical_model_accuracy_validation':False,'accepted_runtime_models':0,
            'experimental_lineages':len(catalog),'materials':[],
            'scope':'Saved public raw-curve extraction arithmetic and calibration eligibility; no raw-file re-download.'}
    for entry in catalog:
        rows=[]
        errors=[]
        for r in entry['specimen_records']:
            computed=r['peak_load_n']/r['area_mm2']
            if not isclose(computed,r['uts_mpa'],rel_tol=1e-12):
                errors.append(r['file']+'#'+r['sheet'])
            context=dict(entry['source_context'],material_family=entry['material_family'],
                         material_grade=entry['material_grade'],property=entry['property'],
                         raster_angles_deg=[int(x) for x in r['orientation'].split('/')])
            rows.append(dict(sample_id=r['file']+'#'+r['sheet'],study_id=entry['doi'],
                             lineage_id=entry['source_id'],batch_id=None,
                             source_url=entry['raw_file_provenance']['url'],source_locator=r['sheet']+'!'+r['peak_cell'],
                             value_mpa=r['uts_mpa'],context=context))
        for observation in entry['observations']:
            ids=set(observation['specimens'])
            values=[r['value_mpa'] for r in rows if r['sample_id'] in ids]
            if (len(values)!=observation['n'] or
                not isclose(mean(values),observation['value_mpa'],rel_tol=1e-12) or
                not isclose(stdev(values),observation['sd_mpa'],rel_tol=1e-12)):
                errors.append('GROUP_STATISTICS:'+str(observation['raster_angles_deg']))
        result['materials'].append({'material_family':entry['material_family'],
                                    'material_grade':entry['material_grade'],
                                    'source_url':entry['source_url'],
                                    'raw_file_provenance':entry['raw_file_provenance'],
                                    'specimen_count':len(rows),'arithmetic_errors':errors,
                                    'calibration_audit':validate_linear_candidate(rows,variable='speed_mm_s')})
    result['saved_extraction_arithmetic_passed']=not any(r['arithmetic_errors'] for r in result['materials'])
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    output=json.dumps(public_data_report(),indent=2,ensure_ascii=False,allow_nan=False)+'\n'
    if args.output:args.output.write_text(output,encoding='utf-8')
    else:print(output,end='')


if __name__=='__main__':main()
