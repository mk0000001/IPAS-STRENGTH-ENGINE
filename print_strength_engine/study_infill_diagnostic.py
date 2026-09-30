"""Within-study infill holdout diagnostic, never a production calibration.

The fixed protocol fits a straight line to 25% and 75% infill condition means
within each material/pattern, and predicts the six unseen 50% specimens.
The training-only mean is the baseline. With two equidistant endpoints and
equal replicate counts both methods are algebraically identical at 50%.
This reports that limitation rather than selecting a different model after
observing test errors. One study cannot validate cross-study transfer.
"""
from collections import defaultdict
from hashlib import sha256
import json
from math import isfinite, sqrt
from statistics import mean


def diagnose_infill_holdout(records):
    records=list(records)
    digest=sha256(json.dumps(records,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    groups=defaultdict(list)
    seen=set()
    for row in records:
        if row.get('unit')!='MPa' or row.get('property')!='tensile_stress':
            raise ValueError('TENSILE_STRESS_MPA_REQUIRED')
        if not row.get('study_id') or not row.get('source_locator') or not row.get('specimen_id'):
            raise ValueError('SOURCE_IDENTIFIERS_REQUIRED')
        key=(row['study_id'],row['specimen_id'])
        if key in seen:raise ValueError('DUPLICATE_SPECIMEN')
        seen.add(key)
        if not isinstance(row.get('value_mpa'),(int,float)) or isinstance(row['value_mpa'],bool) or not isfinite(row['value_mpa']) or row['value_mpa']<=0:
            raise ValueError('INVALID_STRESS')
        if not isinstance(row.get('infill_percent'),(int,float)) or isinstance(row['infill_percent'],bool) or not isfinite(row['infill_percent']) or not 0<=row['infill_percent']<=100:
            raise ValueError('INVALID_INFILL')
        groups[(row['study_id'],row['material_label'],row['pattern'])].append(row)
    report={'version':'WITHIN_STUDY_INFILL_HOLDOUT_DIAGNOSTIC_V1',
            'input_sha256':digest,'input_specimens':len(records),
            'status':'DIAGNOSTIC_ONLY_NO_RUNTIME_CALIBRATION',
            'candidate':'LINEAR_THROUGH_TRAINING_CONDITION_MEANS',
            'baseline':'TRAINING_SPECIMEN_MEAN',
            'train_infill_percent':[25,75],'holdout_infill_percent':50,
            'split_unit':'WITHIN_STUDY_INFILL_CONDITION',
            'independent_study_holdouts':0,'independent_batch_holdouts':0,
            'is_prediction_of_current_part':False,'accepted_for_runtime':False,
            'cells':[],'excluded_groups':[],
            'limitations':['The same study supplies training and held-out infill conditions.',
                           'Manufacturing batches are not independently identified.',
                           'Grade, stress-area definition and contradictory reported layer heights remain unresolved.',
                           'No target-part strength, independent-study accuracy or confidence interval follows.',
                           'No model or hyperparameter selection is performed using held-out outcomes.']}
    all_errors=[];all_baseline_errors=[];train_count=0
    for (study,material,pattern),rows in sorted(groups.items()):
        levels={density:[r for r in rows if r['infill_percent']==density] for density in (25,50,75)}
        if not all(levels.values()):
            report['excluded_groups'].append({'study_id':study,'material_label':material,'pattern':pattern,
                                               'specimens':len(rows),'reason':'MISSING_REQUIRED_25_50_75_LEVELS'})
            continue
        low=mean(r['value_mpa'] for r in levels[25]);high=mean(r['value_mpa'] for r in levels[75])
        prediction=low+(high-low)*(50-25)/(75-25)
        training=levels[25]+levels[75]
        baseline=mean(r['value_mpa'] for r in training)
        observed=mean(r['value_mpa'] for r in levels[50])
        errors=[prediction-r['value_mpa'] for r in levels[50]]
        baseline_errors=[baseline-r['value_mpa'] for r in levels[50]]
        all_errors.extend(errors);all_baseline_errors.extend(baseline_errors);train_count+=len(training)
        report['cells'].append({'study_id':study,'material_label':material,'pattern':pattern,
                                'training_specimen_ids':[r['specimen_id'] for r in training],
                                'holdout_specimen_ids':[r['specimen_id'] for r in levels[50]],
                                'training_mean_mpa_by_density':{'25':low,'75':high},
                                'candidate_mpa':prediction,'baseline_mpa':baseline,
                                'observed_holdout_mean_mpa':observed,
                                'candidate_group_mean_absolute_error_mpa':abs(prediction-observed),
                                'baseline_group_mean_absolute_error_mpa':abs(baseline-observed),
                                'candidate_specimen_mae_mpa':mean(abs(e) for e in errors),
                                'baseline_specimen_mae_mpa':mean(abs(e) for e in baseline_errors),
                                'candidate_specimen_rmse_mpa':sqrt(mean(e*e for e in errors)),
                                'baseline_specimen_rmse_mpa':sqrt(mean(e*e for e in baseline_errors))})
    report.update(training_specimens=train_count,holdout_specimens=len(all_errors),
                  holdout_conditions=len(report['cells']))
    if all_errors:
        report.update(candidate_specimen_mae_mpa=mean(abs(e) for e in all_errors),
                      baseline_specimen_mae_mpa=mean(abs(e) for e in all_baseline_errors),
                      candidate_specimen_rmse_mpa=sqrt(mean(e*e for e in all_errors)),
                      baseline_specimen_rmse_mpa=sqrt(mean(e*e for e in all_baseline_errors)))
        # Numerical summation order is not scientific improvement.
        report['beats_baseline']=report['candidate_specimen_mae_mpa']<report['baseline_specimen_mae_mpa']-1e-12
        report['decision']='NO_EVIDENCE_OF_IMPROVEMENT' if not report['beats_baseline'] else 'DIAGNOSTIC_ONLY_REQUIRES_INDEPENDENT_VALIDATION'
    else:
        report.update(beats_baseline=False,decision='NO_EVALUABLE_HOLDOUT_CONDITIONS')
    return report


def main():
    import argparse
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('records',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    result=diagnose_infill_holdout(json.loads(args.records.read_text(encoding='utf-8-sig')))
    output=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    if args.output:args.output.write_text(output,encoding='utf-8')
    else:print(output,end='')


if __name__=='__main__':main()
