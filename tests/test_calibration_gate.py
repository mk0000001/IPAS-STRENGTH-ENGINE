"""Synthetic fixtures verify validation mechanics, not empirical accuracy."""
from copy import deepcopy
import unittest

from print_strength_engine.calibration import (
    compare_contexts, calibration_eligibility, validate_linear_candidate,
)
from print_strength_engine.process import process_adjustment, material_factors
from print_strength_engine.infill import infill_response
from print_strength_engine.evidence import literature_comparisons, evidence_coverage, research_coverage_catalog
from print_strength_engine.public_validation import public_data_report


def context():
    return dict(material_family='PLA', material_grade='TEST_ONLY_GRADE',
                property='tensile_strength', orientation='XY/X',
                stress_area_basis='GROSS_COUPON', test_standard='TEST_ONLY_STANDARD',
                moisture_condition='dry', annealing='none', printer='TEST_ONLY_PRINTER',
                nozzle_diameter_mm=.4, layer_height_mm=.2, line_width_mm=.45,
                nozzle_c=210, bed_c=60, chamber_c=25, fan_percent=100,
                speed_mm_s=50, speed_basis='PRINT_SETTING', infill_percent=100,
                pattern='rectilinear', walls=3, raster_angles_deg=[-45,45], flow_ratio=1.,
                test_temperature_c=23,test_relative_humidity_percent=50,
                crosshead_speed_mm_min=5,conditioning_duration_h=24)


def records():
    rows=[]
    for lineage in ('A','B','C'):
        for n,x in enumerate((.1,.2,.3)):
            c=context();c['layer_height_mm']=x
            rows.append(dict(sample_id=f'{lineage}-{n}',study_id=lineage,lineage_id=lineage,
                             batch_id=lineage,source_url=f'https://example.test/{lineage}',
                             source_locator=f'test fixture row {n}',value_mpa=50-40*x,context=c))
    return rows


class CalibrationGateTests(unittest.TestCase):
    def test_missing_unknowns_do_not_match(self):
        report=compare_contexts({'material_grade':'unknown'},{'material_grade':'unknown'})
        self.assertIn('material_grade',report['missing_source_fields'])
        self.assertIn('material_grade',report['missing_target_fields'])
        self.assertEqual(report['matched_fields'],[])

    def test_complete_equal_context_does_not_approve_model(self):
        c=context();c['grade_identity_verified']=True
        self.assertEqual(compare_contexts(c,c)['status'],'MATCHED_CONTEXT_ONLY')
        gate=calibration_eligibility(c,c,model_id='caller-claims-approved')
        self.assertEqual(gate['status'],'UNSUPPORTED_CALIBRATION')
        self.assertIsNone(gate['effective_mpa'])
        self.assertIn('UNRECOGNIZED_OR_UNAPPROVED_MODEL_ID',gate['blocking_reasons'])

    def test_property_orientation_area_and_speed_basis_are_separate(self):
        c=context();d=deepcopy(c)
        d.update(property='interlayer_shear_strength',orientation='Z',
                 stress_area_basis='NET_CONTACT',speed_basis='COMMANDED_MOVE_MEDIAN')
        self.assertEqual({x['field'] for x in compare_contexts(c,d)['mismatches']},
                         {'property','orientation','stress_area_basis','speed_basis'})

    def test_test_temperature_is_not_nozzle_temperature(self):
        c=context();d=deepcopy(c);d['test_temperature_c']=100
        mismatch=compare_contexts(c,d)['mismatches']
        self.assertEqual([x['field'] for x in mismatch],['test_temperature_c'])
        self.assertEqual(c['nozzle_c'],d['nozzle_c'])

    def test_holdout_beats_baseline_without_approving_runtime(self):
        result=validate_linear_candidate(records(),variable='layer_height_mm')
        self.assertEqual(result['status'],'CANDIDATE_PASSED_REQUIRES_SOURCE_AND_SCOPE_REVIEW')
        self.assertFalse(result['accepted_for_runtime'])
        for fold in result['folds']:
            self.assertNotIn(fold['heldout_lineage'],fold['training_lineages'])
            self.assertAlmostEqual(fold['candidate_mae_mpa'],0,places=10)
            self.assertGreater(fold['baseline_mae_mpa'],0)

    def test_same_study_replicates_cannot_be_independent_validation(self):
        rows=records()
        for r in rows:r['lineage_id']='single-campaign'
        result=validate_linear_candidate(rows,variable='layer_height_mm')
        self.assertEqual(result['status'],'INSUFFICIENT_EVIDENCE')
        self.assertEqual(result['experimental_lineages'],['single-campaign'])

    def test_study_and_same_source_cannot_be_split_across_lineages(self):
        rows=records();rows[3]['study_id']='A'
        result=validate_linear_candidate(rows,variable='layer_height_mm')
        self.assertEqual(result['status'],'REJECTED_INPUT')
        self.assertIn('STUDY_SPLIT_ACROSS_LINEAGES',result['exclusions'][0]['reasons'])
        rows=records();rows[3].update(source_url=rows[0]['source_url'],source_locator=rows[0]['source_locator'],sample_id=rows[0]['sample_id'])
        result=validate_linear_candidate(rows,variable='layer_height_mm')
        self.assertIn('SOURCE_SPECIMEN_SPLIT_ACROSS_LINEAGES',result['exclusions'][0]['reasons'])

    def test_no_extrapolation_or_selected_subset_success(self):
        rows=records();rows[-1]['context']['layer_height_mm']=.4
        result=validate_linear_candidate(rows,variable='layer_height_mm')
        self.assertEqual(result['status'],'CANDIDATE_REJECTED')
        self.assertEqual(result['folds'][-1]['status'],'INCOMPLETE_HOLDOUT_COVERAGE')
        self.assertIsNone(result['folds'][-1]['predictions'][-1]['candidate_mpa'])

    def test_baseline_tie_does_not_approve_more_complex_model(self):
        rows=records()
        for r in rows:r['value_mpa']=30
        result=validate_linear_candidate(rows,variable='layer_height_mm')
        self.assertEqual(result['status'],'CANDIDATE_REJECTED')
        self.assertTrue(all(f['status']=='DOES_NOT_BEAT_BASELINE' for f in result['folds']))

    def test_confounded_settings_rejected_not_fitted(self):
        rows=records();rows[0]['context']['nozzle_c']=220
        result=validate_linear_candidate(rows,variable='layer_height_mm')
        self.assertEqual(result['status'],'REJECTED_INPUT')
        self.assertTrue(any('INCOMPATIBLE_CONTEXT_STRATUM' in x['reasons'] for x in result['exclusions']))

    def test_duplicate_and_missing_labels_not_silent_zero_fill(self):
        for mutate,reason in ((lambda r:r.append(deepcopy(r[0])),'DUPLICATE_SPECIMEN'),
                              (lambda r:r[0].update(value_mpa=float('nan')),'INVALID_STRENGTH'),
                              (lambda r:r[0]['context'].pop('moisture_condition'),'MISSING_CONTEXT_MOISTURE_CONDITION')):
            rows=records();mutate(rows)
            result=validate_linear_candidate(rows,variable='layer_height_mm')
            self.assertEqual(result['status'],'REJECTED_INPUT')
            self.assertTrue(any(reason in x['reasons'] for x in result['exclusions']))

    def test_replicates_are_averaged_before_scoring(self):
        rows=records()
        for n in range(10):
            extra=deepcopy(rows[0]);extra['sample_id']=f'replicate-{n}';rows.append(extra)
        result=validate_linear_candidate(rows,variable='layer_height_mm')
        self.assertEqual(result['condition_batch_means'],9)
        self.assertEqual(result['input_rows'],19)
        self.assertEqual(result['folds'][1]['train_condition_batches'],6)

    def test_process_context_cannot_override_observed_gcode(self):
        result=process_adjustment({'configuration':{'nozzle_temperature':220}},
                                  {'X':50,'Y':50,'Z':30},reference_context=context(),
                                  target_context={'nozzle_c':210})
        self.assertEqual(result['target_context']['nozzle_c'],220)
        self.assertIn('SUPPLIED_CONTEXT_CONFLICTS_WITH_GCODE',result['calibration']['blocking_reasons'])
        self.assertIsNone(result['effective_mpa'])
        self.assertEqual(result['reference_mpa']['X'],'50')

    def test_all_families_get_explicit_calibration_absence(self):
        for family in ('PLA','PETG','ABS','ASA','PA','PC','TPU','PPA-CF','PPS-CF','PEI','NEW_UNKNOWN'):
            result=process_adjustment({'configuration':{'filament_type':family}}, {'X':50,'Y':50,'Z':30})
            self.assertEqual(result['calibration']['status'],'UNSUPPORTED_CALIBRATION')
            self.assertFalse(result['is_prediction'])
            self.assertIsNone(result['effective_mpa'])

    def test_infill_scaled_reference_is_explicitly_illustrative(self):
        result=infill_response('PLA',50,reference_mpa=100)
        self.assertFalse(result['is_prediction'])
        self.assertIsNone(result['effective_mpa'])
        self.assertEqual(result['comparison_mpa_status'],'ILLUSTRATIVE_RESCALED_REFERENCE_NOT_TARGET_STRENGTH')

    def test_public_raw_curve_extraction_is_reproducible_but_not_model_validation(self):
        report=public_data_report()
        self.assertTrue(report['saved_extraction_arithmetic_passed'])
        self.assertEqual(sum(r['specimen_count'] for r in report['materials']),18)
        self.assertEqual(report['experimental_lineages'],2)
        self.assertEqual(report['accepted_runtime_models'],0)
        self.assertFalse(report['is_empirical_model_accuracy_validation'])
        for material in report['materials']:
            self.assertEqual(material['calibration_audit']['status'],'REJECTED_INPUT')
            self.assertTrue(material['raw_file_provenance']['sha256'])
            self.assertIn('MISSING_BATCH_ID',material['calibration_audit']['exclusions'][0]['reasons'])

    def test_public_asa_comparisons_never_become_generic_material_strength(self):
        for family in ('ASA','ASA-CF'):
            rows=literature_comparisons({'material_family':family})
            self.assertEqual(len(rows),1)
            self.assertEqual(rows[0]['material_match'],'SAME_FAMILY_NOT_GRADE_MATCH')
            self.assertEqual(len(rows[0]['specimen_records']),9)
            self.assertIsNone(rows[0]['transfer_factor'])
            self.assertFalse(rows[0]['runtime_calibration_eligible'])
            self.assertEqual(evidence_coverage({'material_family':family})['comparison_count'],1)
        self.assertEqual(evidence_coverage({'material_family':'ABS'})['other_properties_available'],['interlayer_shear_strength'])

    def test_missing_directional_reference_still_has_material_factor_evidence(self):
        result=material_factors({'configuration':{'filament_type':'ASA'}})
        self.assertEqual(result['evidence_coverage']['comparison_count'],1)
        self.assertEqual(result['calibration']['status'],'UNSUPPORTED_CALIBRATION')

    def test_host_reference_metadata_keeps_margin_out_of_measured_strength(self):
        result=process_adjustment({'configuration':{'filament_type':'PLA','nozzle_temperature':210}},
                                  {'X':42.5,'Y':42.5,'Z':25.5},reference_context={
                                      'reference_product':'eSUN PLA Basic',
                                      'internal_conservative_factor':.85,
                                      'test_conditions':{'nozzle_c':220}})
        self.assertEqual(result['reference_matching_context']['nozzle_c'],220)
        self.assertEqual(result['reference_matching_context']['material_grade'],'eSUN PLA Basic')
        self.assertIsNone(result['target_context']['material_grade'])
        self.assertIn('REFERENCE_CONTAINS_UNVALIDATED_INTERNAL_MARGIN',result['calibration']['blocking_reasons'])
        self.assertEqual(result['reference_strength_kind'],'MARGIN_ADJUSTED_REFERENCE_NOT_MEASURED_ALLOWABLE')
        self.assertIsNone(result['effective_mpa'])

    def test_research_matrix_covers_all_registered_families_without_strength_claim(self):
        catalog=research_coverage_catalog()
        expected={'PLA','PETG','ABS','ASA','PETG-CF','PETG-GF','ABS-CF','ABS-GF',
                  'PA6-CF','PA6-GF','PA12-CF','PA12-GF','PPA-CF','PPA-GF','PPS-CF','PC','TPU','TPE'}
        self.assertEqual({r['material_family'] for r in catalog['materials']},expected)
        self.assertEqual(catalog['registered_material_count'],18)
        self.assertEqual(sum(r['status']=='COMPARISON_ONLY' for r in catalog['materials']),6)
        self.assertEqual(catalog['approved_transfer_models'],0)
        self.assertEqual(catalog['independent_study_holdouts'],0)
        for family in expected:
            report=evidence_coverage({'material_family':family})
            self.assertEqual(len(report['registered_material_coverage']),18)
            self.assertEqual(report['research_manifest']['source_coverage_sha256'],catalog['source_coverage_sha256'])
            self.assertIsNone(report['effective_mpa'])
            self.assertFalse(report['researched_comparison_evidence']['is_runtime_calibration'])

    def test_new_comparison_sources_do_not_masquerade_as_numeric_tensile_catalog(self):
        for family in ('PETG','PPA-CF'):
            report=evidence_coverage({'material_family':family})
            self.assertEqual(report['status'],'RESEARCH_COMPARISON_ONLY')
            self.assertEqual(report['curated_numeric_catalog']['comparison_count'],0)
            self.assertTrue(report['researched_comparison_evidence']['source_urls'])
            self.assertEqual(report['researched_comparison_evidence']['requested_property_match'],
                             'NOT_ASSERTED_BY_FAMILY_COVERAGE')
        pc=evidence_coverage({'material_family':'PC'})
        self.assertEqual(pc['comparison_count'],0)
        self.assertIn('interlayer_shear_strength',pc['other_properties_available'])
        self.assertEqual(evidence_coverage({'material_family':'PPA-GF'})['status'],'RESEARCH_REVIEWED_INSUFFICIENT')
        abs_report=evidence_coverage({'material_family':'ABS'})
        self.assertEqual(abs_report['status'],'COMPARISON_EVIDENCE_ONLY')
        self.assertGreater(abs_report['curated_numeric_catalog']['comparison_count'],0)
        self.assertIsNone(abs_report['effective_mpa'])

    def test_research_catalog_copies_and_nonregistered_numeric_sources(self):
        report=evidence_coverage({'material_family':'ASA-CF'})
        self.assertEqual(report['comparison_count'],1)
        self.assertEqual(report['researched_comparison_evidence']['status'],'NOT_IN_REGISTERED_MATERIAL_RESEARCH_MATRIX')
        catalog=research_coverage_catalog();catalog['materials'][0]['source_urls'].clear()
        self.assertTrue(research_coverage_catalog()['materials'][0]['source_urls'])
        report['registered_material_coverage'].clear()
        self.assertEqual(len(evidence_coverage({'material_family':'PLA'})['registered_material_coverage']),18)


if __name__=='__main__':unittest.main()
