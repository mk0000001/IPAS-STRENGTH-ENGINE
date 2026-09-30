from copy import deepcopy
import json
from pathlib import Path
import unittest

from print_strength_engine.study_infill_diagnostic import diagnose_infill_holdout


class StudyInfillDiagnosticTests(unittest.TestCase):
    def records(self):
        return json.loads((Path(__file__).parents[1]/'docs/public-infill-holdout-records-20261001.json').read_text())

    def test_real_public_table_protocol_has_no_independent_validation_claim(self):
        report=diagnose_infill_holdout(self.records())
        self.assertEqual(report['input_specimens'],180)
        self.assertEqual(report['training_specimens'],108)
        self.assertEqual(report['holdout_specimens'],54)
        self.assertEqual(report['holdout_conditions'],9)
        self.assertEqual(sum(g['specimens'] for g in report['excluded_groups']),18)
        self.assertEqual(report['independent_study_holdouts'],0)
        self.assertEqual(report['independent_batch_holdouts'],0)
        self.assertFalse(report['accepted_for_runtime'])
        self.assertFalse(report['beats_baseline'])
        self.assertEqual(report['decision'],'NO_EVIDENCE_OF_IMPROVEMENT')
        self.assertAlmostEqual(report['candidate_specimen_mae_mpa'],report['baseline_specimen_mae_mpa'])
        for cell in report['cells']:
            self.assertFalse(set(cell['training_specimen_ids']) & set(cell['holdout_specimen_ids']))

    def test_holdout_outcomes_cannot_change_fitted_predictions(self):
        rows=self.records()
        before=diagnose_infill_holdout(rows)
        for row in rows:
            if row['infill_percent']==50:row['value_mpa']*=2
        after=diagnose_infill_holdout(rows)
        self.assertEqual([c['candidate_mpa'] for c in before['cells']],
                         [c['candidate_mpa'] for c in after['cells']])
        self.assertEqual([c['baseline_mpa'] for c in before['cells']],
                         [c['baseline_mpa'] for c in after['cells']])
        self.assertNotEqual(before['candidate_specimen_mae_mpa'],after['candidate_specimen_mae_mpa'])

    def test_newtons_cannot_enter_mpa_benchmark(self):
        rows=self.records();rows[0]['unit']='N'
        with self.assertRaisesRegex(ValueError,'TENSILE_STRESS_MPA_REQUIRED'):
            diagnose_infill_holdout(rows)

    def test_duplicate_specimens_cannot_weight_benchmark(self):
        rows=self.records();rows.append(deepcopy(rows[0]))
        with self.assertRaisesRegex(ValueError,'DUPLICATE_SPECIMEN'):
            diagnose_infill_holdout(rows)


if __name__=='__main__':unittest.main()
