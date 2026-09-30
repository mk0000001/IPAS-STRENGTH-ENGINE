"""Auditable process calibration eligibility and grouped validation.

No model is approved by this module. A successful holdout experiment is a
candidate for scientific review, not authorization to change part strength.
The deliberately simple candidate is one preselected process variable with
ordinary least squares; the comparator is the training-only mean. Replicate
specimens are averaged within condition/batch before study-lineage holdout.
"""
from copy import deepcopy
from hashlib import sha256
import json
from math import isfinite, sqrt
from statistics import mean

VERSION = 'PROCESS_CALIBRATION_AUDIT_V1'
# No public evidence reviewed so far establishes a transferable, independently
# validated model for the registered manufacturer references. Do not populate
# this registry merely because a fitted curve has small training residuals.
APPROVED_MODEL_IDS = ()
IDENTITY_FIELDS = ('material_family', 'material_grade', 'property',
                   'orientation', 'stress_area_basis', 'test_standard',
                   'moisture_condition', 'annealing')
PROCESS_FIELDS = ('printer', 'nozzle_diameter_mm', 'layer_height_mm',
                  'line_width_mm', 'nozzle_c', 'bed_c', 'chamber_c',
                  'fan_percent', 'speed_mm_s', 'speed_basis', 'infill_percent',
                  'pattern', 'walls', 'raster_angles_deg', 'flow_ratio')
TEST_FIELDS = ('test_temperature_c', 'test_relative_humidity_percent',
               'crosshead_speed_mm_min', 'conditioning_duration_h')
MATCH_FIELDS = IDENTITY_FIELDS + PROCESS_FIELDS + TEST_FIELDS
VARIABLES = ('layer_height_mm', 'line_width_mm', 'nozzle_c', 'bed_c',
             'chamber_c', 'fan_percent', 'speed_mm_s', 'infill_percent',
             'flow_ratio')
UNKNOWN = ('', 'unknown', 'not reported', 'unreported', 'n/a', 'unspecified')


def known(value):
    if value is None or isinstance(value, bool):
        return False
    if isinstance(value, str):
        return value.strip().casefold() not in UNKNOWN
    if isinstance(value, (int, float)):
        return isfinite(value)
    if isinstance(value, (list, tuple)):
        return bool(value) and all(known(item) for item in value)
    return False


def compare_contexts(source, target, *, varying=()):
    """Exact semantic field comparison. Unknown/unknown is never a match.

    No family-to-grade aliases, XY-to-X/Z substitutions, nozzle-to-line-width
    substitutions, or median-speed-to-print-setpoint conversions are allowed.
    """
    source = source if isinstance(source, dict) else {}
    target = target if isinstance(target, dict) else {}
    missing_source, missing_target, mismatches = [], [], []
    matched = []
    for key in MATCH_FIELDS:
        if key in varying:
            continue
        a, b = source.get(key), target.get(key)
        if not known(a):
            missing_source.append(key)
        if not known(b):
            missing_target.append(key)
        if not known(a) or not known(b):
            continue
        if a != b:
            mismatches.append({'field': key, 'source': deepcopy(a), 'target': deepcopy(b)})
        else:
            matched.append(key)
    return {'status': 'MATCHED_CONTEXT_ONLY' if not (missing_source or missing_target or mismatches)
            else 'INCOMPLETE_OR_MISMATCHED_CONTEXT',
            'matched_fields': matched, 'missing_source_fields': missing_source,
            'missing_target_fields': missing_target, 'mismatches': mismatches,
            'is_prediction': False}


def calibration_eligibility(source, target, *, model_id=None):
    result = compare_contexts(source, target)
    reasons = ['NO_REVIEWED_TRANSFER_MODEL']
    if model_id is not None:
        reasons.append('UNRECOGNIZED_OR_UNAPPROVED_MODEL_ID')
    if not isinstance(target, dict) or target.get('grade_identity_verified') is not True:
        reasons.append('TARGET_GRADE_IDENTITY_UNVERIFIED')
    if result['missing_source_fields']:
        reasons.append('REFERENCE_CONTEXT_INCOMPLETE')
    if result['missing_target_fields']:
        reasons.append('TARGET_CONTEXT_INCOMPLETE')
    if result['mismatches']:
        reasons.append('REFERENCE_TARGET_CONTEXT_MISMATCH')
    if isinstance(target,dict) and target.get('line_width_source') == 'NOZZLE_DIAMETER_ASSUMPTION':
        reasons.append('LINE_WIDTH_IS_NOZZLE_PROXY')
    result.update(version=VERSION, status='UNSUPPORTED_CALIBRATION',
                  requested_model_id=model_id, approved_model_ids=list(APPROVED_MODEL_IDS),
                  blocking_reasons=reasons, effective_mpa=None,
                  reference_only=True, extrapolation_permitted=False)
    return result


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value)


def validate_linear_candidate(records, *, variable):
    """Leave-one-experimental-lineage-out evaluation, with no extrapolation.

    Each row requires sample_id, study_id, lineage_id, batch_id, source_url,
    source_locator, value_mpa and a context containing MATCH_FIELDS. Rows must
    describe one grade/property/orientation/conditioning/process stratum except
    for the declared variable. Lineage IDs must group papers and datasets from
    the same experiment. Caller-provided IDs are audited, not independently
    authenticated. Never random-split specimens from the same experiment.
    """
    if variable not in VARIABLES:
        raise ValueError('UNSUPPORTED_CALIBRATION_VARIABLE')
    records = deepcopy(list(records))
    # Hash retains input values and metadata; report does not conceal rejected
    # rows or convert missing labels to zero. NaN is explicitly invalid below.
    digest = sha256(json.dumps(records, sort_keys=True, separators=(',', ':'),
                               default=str).encode()).hexdigest()
    report = {'version': VERSION, 'variable': variable,
              'candidate': 'SINGLE_VARIABLE_OLS', 'baseline': 'TRAINING_MEAN',
              'split': 'LEAVE_ONE_EXPERIMENTAL_LINEAGE_OUT',
              'input_sha256': digest, 'input_rows': len(records),
              'status': 'INSUFFICIENT_EVIDENCE', 'accepted_for_runtime': False,
              'is_prediction': False, 'exclusions': [], 'folds': [],
              'replicate_policy': 'AVERAGE_WITHIN_LINEAGE_BATCH_CONDITION',
              'acceptance_rule': 'At least three lineages; full holdout coverage; MAE at least 1e-12 MPa lower than training mean in every fold (numerical tie tolerance only).',
              'limitations': ['Lineage/provenance supplied by caller requires source review.',
                              'A passing candidate is not an approved model or a design allowable.',
                              'No independent-laboratory or universal-accuracy claim.']}
    valid, seen, study_lineages, sample_lineages = [], set(), {}, {}
    for index, row in enumerate(records):
        errors = []
        if not isinstance(row, dict):
            report['exclusions'].append({'row': index, 'reasons': ['INVALID_ROW']})
            continue
        context = row.get('context') if isinstance(row.get('context'), dict) else {}
        for field in ('sample_id', 'study_id', 'lineage_id', 'batch_id', 'source_url', 'source_locator'):
            if not isinstance(row.get(field), str) or not known(row.get(field)):
                errors.append('MISSING_' + field.upper())
        for field in MATCH_FIELDS:
            if not known(context.get(field)):
                errors.append('MISSING_CONTEXT_' + field.upper())
        if not _number(row.get('value_mpa')) or row['value_mpa'] <= 0:
            errors.append('INVALID_STRENGTH')
        if not _number(context.get(variable)):
            errors.append('INVALID_VARIABLE')
        if errors:
            report['exclusions'].append({'row': index, 'reasons': errors})
            continue
        key = (row['lineage_id'], row['sample_id'])
        if key in seen:
            errors.append('DUPLICATE_SPECIMEN')
        seen.add(key)
        prior = study_lineages.setdefault(row['study_id'], row['lineage_id'])
        if prior != row['lineage_id']:
            errors.append('STUDY_SPLIT_ACROSS_LINEAGES')
        specimen_source = (row['source_url'], row['source_locator'], row['sample_id'])
        prior = sample_lineages.setdefault(specimen_source, row['lineage_id'])
        if prior != row['lineage_id']:
            errors.append('SOURCE_SPECIMEN_SPLIT_ACROSS_LINEAGES')
        if valid:
            matching = compare_contexts(valid[0]['context'], context, varying=(variable,))
            if matching['mismatches']:
                errors.append('INCOMPATIBLE_CONTEXT_STRATUM')
        if errors:
            report['exclusions'].append({'row': index, 'reasons': errors})
        else:
            valid.append(row)
    report['eligible_rows'] = len(valid)
    lineages = sorted({r['lineage_id'] for r in valid})
    report['experimental_lineages'] = lineages
    if report['exclusions']:
        report['status'] = 'REJECTED_INPUT'
        return report
    if len(lineages) < 3:
        report['blocking_reason'] = 'FEWER_THAN_THREE_MATCHED_EXPERIMENTAL_LINEAGES'
        return report
    cells = {}
    for row in valid:
        key = (row['lineage_id'], row['batch_id'], row['context'][variable])
        cells.setdefault(key, []).append(row['value_mpa'])
    points = [(lineage, batch, x, mean(values)) for (lineage, batch, x), values in sorted(cells.items())]
    report['condition_batch_means'] = len(points)
    for heldout in lineages:
        train = [p for p in points if p[0] != heldout]
        test = [p for p in points if p[0] == heldout]
        xs, ys = [p[2] for p in train], [p[3] for p in train]
        xbar, ybar = mean(xs), mean(ys)
        denom = sum((x-xbar)**2 for x in xs)
        fold = {'heldout_lineage': heldout,
                'training_lineages': [x for x in lineages if x != heldout],
                'train_condition_batches': len(train), 'test_condition_batches': len(test),
                'training_domain': [min(xs), max(xs)], 'predictions': []}
        if denom == 0:
            fold['status'] = 'UNIDENTIFIABLE_VARIABLE'
            report['folds'].append(fold)
            continue
        slope = sum((x-xbar)*(y-ybar) for x, y in zip(xs, ys))/denom
        intercept = ybar-slope*xbar
        fold.update(slope=slope, intercept=intercept, baseline_mpa=ybar)
        for _, batch, x, observed in test:
            in_range = min(xs) <= x <= max(xs)
            predicted = intercept+slope*x
            fold['predictions'].append({'batch_id': batch, 'x': x, 'observed_mpa': observed,
                                        'candidate_mpa': predicted if in_range and predicted > 0 else None,
                                        'baseline_mpa': ybar,
                                        'status': 'EVALUATED' if in_range and predicted > 0 else 'OUTSIDE_VALID_DOMAIN'})
        if any(p['candidate_mpa'] is None for p in fold['predictions']):
            fold['status'] = 'INCOMPLETE_HOLDOUT_COVERAGE'
        else:
            errors = [p['candidate_mpa']-p['observed_mpa'] for p in fold['predictions']]
            baseline_errors = [ybar-p['observed_mpa'] for p in fold['predictions']]
            fold.update(candidate_mae_mpa=mean(abs(e) for e in errors),
                        baseline_mae_mpa=mean(abs(e) for e in baseline_errors),
                        candidate_rmse_mpa=sqrt(mean(e*e for e in errors)),
                        baseline_rmse_mpa=sqrt(mean(e*e for e in baseline_errors)))
            fold['status'] = ('BEATS_BASELINE' if fold['candidate_mae_mpa'] < fold['baseline_mae_mpa']-1e-12
                              else 'DOES_NOT_BEAT_BASELINE')
        report['folds'].append(fold)
    if all(f['status'] == 'BEATS_BASELINE' for f in report['folds']):
        report['status'] = 'CANDIDATE_PASSED_REQUIRES_SOURCE_AND_SCOPE_REVIEW'
    else:
        report['status'] = 'CANDIDATE_REJECTED'
    return report


def main():
    """Reproduce an audit from a JSON array; never install or approve a model."""
    import argparse
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('records',type=Path,help='JSON array of source-linked measurement records')
    parser.add_argument('--variable',required=True,choices=VARIABLES)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    records=json.loads(args.records.read_text(encoding='utf-8-sig'))
    if not isinstance(records,list):
        parser.error('records must be a JSON array')
    report=validate_linear_candidate(records,variable=args.variable)
    output=json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    if args.output:
        args.output.write_text(output,encoding='utf-8')
    else:
        print(output,end='')


if __name__=='__main__':
    main()
