"""Semantic regressions mined from anonymized fresh source metadata.

Public fixtures require independently reconciled whole-corpus completion.
Pilot and partial format probes remain private reporting artifacts.
The unit-area capacity probe is a schema probe, not source geometry or a
measured specimen label. No learned mechanical coefficient enters this suite.
"""
from copy import deepcopy
from decimal import Decimal
import json
from math import ulp
from pathlib import Path
import re
import unittest

from print_strength_engine.capacity import capacity_for_candidate
from print_strength_engine.material_reference import reference_inputs
from print_strength_engine.process import material_factors, settings


class FreshCorpusMetadataRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).parents[1]/'docs/full-corpus-regression-fixtures-20261003.json'
        cls.bundle = json.loads(path.read_text(encoding='utf-8'))
        cls.fixtures = cls.bundle['fixtures']
        if not cls.fixtures:
            raise AssertionError('Fresh full-source fixture inputs are required')

    def test_fixture_has_explicit_software_scope_without_private_source_or_force_labels(self):
        self.assertFalse(self.bundle['mechanical_training'])
        self.assertEqual(self.bundle['corpus_scope'], 'FULL_CURRENT_CORPUS')
        proof=self.bundle['independent_full_corpus_proof']
        self.assertTrue(proof['original_hash_rechecks_performed'])
        self.assertEqual(proof['artifact_occurrences'], 1682)
        self.assertEqual(proof['plate_occurrences'], 1693)
        self.assertEqual(proof['missing_count'], 0)
        self.assertEqual(proof['error_count'], 0)
        self.assertRegex(proof['independent_receipt_sha256'], r'^[0-9a-f]{64}$')
        self.assertRegex(proof['manifest_sha256'], r'^[0-9a-f]{64}$')
        forbidden={'source_path', 'source_sha256', 'selected_gcode_sha256', 'filename', 'filenames',
                   'artifact_id', 'artifact_key', 'plate_key', 'archive_member', 'outer_zip_member',
                   'scan_path', 'assessment_path', 'path', 'filament_settings_id',
                   'bounds', 'bounds_mm', 'coordinates', 'centroid', 'vertices', 'polygon',
                   'points', 'start', 'end', 'segments', 'deposited_section',
                   'commanded_volume_section', 'volume_section', 'section_area_mm2',
                   'section_modulus_mm3', 'estimated_capacity'}
        def inspect(value, location=()):
            if isinstance(value, dict):
                for key, item in value.items():
                    with self.subTest(field='.'.join(location+(key,))):
                        self.assertNotIn(key, forbidden)
                        for marker in ('path', 'filename', 'archive', 'coord', 'bounds', 'centroid',
                                       'vertex', 'vertices', 'contour', 'outline', 'polygon',
                                       'segment', 'length', 'volume'):
                            self.assertNotIn(marker, key.lower())
                        if 'section' in key:
                            self.assertTrue(key.endswith('_status'))
                            self.assertIn(item, ('COMPLETE', 'WITHHELD', 'PARTIAL', 'NOT_REPORTED', None))
                        if key.endswith('_sha256'):
                            self.assertIn(key, {'source_results_sha256', 'independent_receipt_sha256', 'manifest_sha256'})
                        if 'force' in key or key.endswith('load_n') or key=='numeric_fracture_ground_truth':
                            self.assertIsNone(item)
                    inspect(item, location+(key,))
            elif isinstance(value, list):
                for index, item in enumerate(value):inspect(item, location+(str(index),))
            elif isinstance(value, str):
                self.assertNotRegex(value, r'(?i)(?:[a-z]:[\\/]|\.(?:gcode|3mf|stl|zip)\b)')
        inspect(self.bundle)
        for case in self.fixtures:
            with self.subTest(case=case['id']):
                self.assertIsNone(case['numeric_fracture_ground_truth'])
                self.assertFalse(case['strength_training_eligible'])
                text=json.dumps(case)
                self.assertNotIn('source_path', text)
                self.assertNotIn('source_sha256', text)
                self.assertNotIn('filament_settings_id', text)
                self.assertNotIn('deposited_section', text)

    def test_fresh_process_inputs_preserve_unknowns_without_claiming_grade_or_calibration(self):
        for case in self.fixtures:
            with self.subTest(case=case['id']):
                analysis=deepcopy(case['input']['analysis']);before=deepcopy(analysis)
                report=material_factors(analysis);read=report['settings']
                self.assertEqual(report['factor_status'], 'NOT_APPLIED')
                self.assertFalse(report['is_prediction'])
                self.assertEqual(report['applied'], [])
                self.assertEqual(report['calibration']['approved_model_ids'], [])
                self.assertIsNone(report['calibration']['effective_mpa'])
                self.assertFalse(read['grade_identity_verified'])
                self.assertIsNone(read['material_grade'])
                for key in ('local_interlayer_return_time_s', 'measured_substrate_temperature_c',
                            'measured_void_fraction', 'measured_bonded_contact_fraction'):
                    self.assertIsNone(read[key])
                self.assertEqual(analysis, before)

    def test_conflicting_slots_and_command_temperature_are_independent(self):
        for case in self.fixtures:
            read=settings(case['input']['analysis'])
            config=case['input']['analysis']['configuration']
            for source, scalar, slots in (('nozzle_temperature','nozzle_c','nozzle_temperatures_c'),
                                         ('bed_temperature','bed_c','bed_temperatures_c'),
                                         ('filament_flow_ratio','flow_ratio','flow_ratios')):
                raw=config.get(source)
                values=raw if isinstance(raw,list) else re.split('[,;]',str(raw)) if raw is not None else []
                if len(values)>1 and len({str(v) for v in values})>1:
                    with self.subTest(case=case['id'],source=source):
                        self.assertIsNone(read[scalar])
                        self.assertEqual(len(read[slots]),len(values))
            command=case['input']['analysis']['process_metrics'].get('deposition_nozzle_setpoint_c')
            self.assertEqual(read['nozzle_command_range_c'],command)

    def test_raw_reference_and_margin_stay_separate_and_layer_proxy_never_gains_force(self):
        for case in self.fixtures:
            data=case['input'];raw=deepcopy(data['raw_reference_mpa']);before=deepcopy(raw)
            reference=reference_inputs(raw,data['internal_margin_factor'])
            with self.subTest(case=case['id']):
                self.assertFalse(reference['margin_is_calibrated'])
                self.assertFalse(reference['factor_applied_to_material'])
                self.assertEqual(raw,before)
                values=reference['directional_material_mpa']
                if values:
                    for axis,value in values.items():
                        source='XY' if axis in ('X','Y') and 'XY' in raw else axis
                        self.assertEqual(Decimal(value),Decimal(str(raw[source])))
                        adjusted=reference['directional_capacity_mpa']
                        if adjusted:
                            self.assertEqual(Decimal(adjusted[axis]),Decimal(str(raw[source]))*Decimal(str(data['internal_margin_factor'])))
                    load=capacity_for_candidate(data['capacity_probe'],values,data['analysis'])
                    self.assertIsNotNone(load)
                    self.assertEqual(load['calculation_status'],'GEOMETRY_COMPARISON_ONLY')
                    self.assertFalse(load['is_failure_prediction'])
                    self.assertFalse(load['empirically_validated'])
                    self.assertIsNone(load['axial_capacity_n'])
                    self.assertIsNone(load['bending_force_n'])
                else:
                    self.assertIsNone(reference['directional_capacity_mpa'])

    def test_source_endpoint_labels_preserve_the_catalog_conflict(self):
        cases=[case for case in self.fixtures if
               'CATALOG_SOURCE_TENSILE_ENDPOINT_LABEL_CONFLICT' in case['labels']]
        self.assertTrue(cases, 'Fresh source/catalog endpoint evidence is required')
        for case in cases:
            with self.subTest(case=case['id']):
                metrics=case['input']['reference_metrics']
                self.assertEqual(metrics['source_metric_labels']['XY'], 'Tensile Break Strength XY')
                self.assertEqual(metrics['source_metric_labels']['Z'], 'Tensile Strength Z')
                self.assertIn('breaking strength', metrics['catalog_metric_labels']['Z'])
                self.assertEqual(metrics['metric_comparability'],
                                 'SOURCE_LABEL_CONFLICT_ENDPOINT_COMPARABILITY_UNVERIFIED')
                self.assertIsNone(case['numeric_fracture_ground_truth'])

    def test_anonymized_contact_roundoff_is_bounded_without_source_geometry(self):
        from print_strength_engine.deposition_section import UnsupportedGeometry
        from print_strength_engine.interlayer_contact import _bounded_overlap_area
        cases=self.bundle.get('contact_roundoff_regressions', [])
        self.assertTrue(cases, 'Current corrected scalar contact evidence is required')
        for case in cases:
            with self.subTest(case=case['id']):
                data=case['input'];bound=data['upper_bound_mm2']
                self.assertFalse(case['geometry_retained'])
                self.assertFalse(case['strength_training_eligible'])
                self.assertIsNone(case['numeric_fracture_ground_truth'])
                self.assertEqual(set(data), {'area_mm2', 'upper_bound_mm2', 'expected_area_mm2'})
                self.assertEqual(_bounded_overlap_area(data['area_mm2'], bound), data['expected_area_mm2'])
                with self.assertRaises(UnsupportedGeometry):
                    _bounded_overlap_area(bound+65*ulp(bound), bound)

    def test_current_role_semantics_use_explicit_synthetic_probes_and_no_weld_force(self):
        from print_strength_engine.local_process import StreamingLocalProcess, VERSION, valid_process_descriptor
        from test_automatic_sections import candidate
        cases=self.bundle.get('process_semantic_regressions', [])
        self.assertTrue(cases, 'Current V2 role/status evidence is required')
        for case in cases:
            with self.subTest(case=case['id']):
                data=case['input'];state=data['observed_current_source_semantics']
                self.assertFalse(case['geometry_retained'])
                self.assertFalse(case['strength_training_eligible'])
                self.assertIsNone(case['numeric_fracture_ground_truth'])
                self.assertEqual(data['probe_basis'],
                                 'UNIT_SCHEMA_PROBE_DERIVED_FROM_ROLE_ENUM_NOT_SOURCE_FEATURE_TOKEN_OR_GEOMETRY')
                self.assertEqual(state['process_version'], VERSION)
                self.assertFalse(state['is_measured'])
                self.assertIsNone(state['measured_substrate_temperature_c'])
                self.assertIn(state['actual_bond_measured'], (False, None))
                self.assertIn(state['weld_strength_status'], ('UNMEASURED', None))
                self.assertIsNone(state['interlayer_failure_load_n'])
                writer=StreamingLocalProcess([candidate(station=5, bounds=[[2,8],[-2,2],[0,2]])])
                context={'commanded_volume_mm3':10, 'commanded_speed_mm_s':20,
                         'nozzle_setpoint_c':240, 'bed_setpoint_c':100,
                         'chamber_setpoint_c':60, 'part_cooling_fan_pwm':128,
                         'flow_override_percent':100, 'assessment_gaps':()}
                writer.motion([0,0,1], [10,0,1], 1, 1, 0,
                              data['canonical_schema_feature'], context)
                probe=writer.finish()['a']
                self.assertEqual(probe['version'], VERSION)
                self.assertTrue(valid_process_descriptor(probe))
                self.assertGreater(probe['roles'][data['expected_role']]['path_length_mm'], 0)
                self.assertFalse(probe['is_measured'])
                self.assertIsNone(probe['measured_substrate_temperature_c'])


if __name__ == '__main__':
    unittest.main()
