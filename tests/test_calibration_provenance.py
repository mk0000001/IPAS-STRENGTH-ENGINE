"""Synthetic provenance fixtures test boundaries, never physical accuracy."""
from copy import deepcopy
import unittest
from unittest.mock import patch

from print_strength_engine.calibration import validate_linear_candidate
from print_strength_engine import evidence
from print_strength_engine.public_validation import public_data_report
from tests.test_calibration_gate import records


def mapped_records():
    rows = records()
    entries = []
    for row in rows:
        label = row['lineage_id']
        row.update(source_id='SYNTHETIC-' + label,
                   source_doi='10.9999/synthetic.' + label.lower(),
                   observation_kind='RAW_SPECIMEN')
        entries.append(dict(source_id=row['source_id'], source_doi=row['source_doi'],
                            source_locator=row['source_locator'],
                            review_status='CURATED_IDENTITY', observation_kind='RAW_SPECIMEN',
                            canonical_campaign_id='campaign-' + label,
                            original_outcome_id='original-' + row['sample_id'],
                            review_locator='TEST_ONLY identity fixture'))
    return rows, dict(schema='PROVENANCE_OBSERVATION_MAP_V1',
                      map_id='TEST_ONLY_MAP', observations=entries)


class ProvenanceBoundaryTests(unittest.TestCase):
    def audit(self, rows, source_map):
        try:
            return validate_linear_candidate(rows, variable='layer_height_mm',
                                             provenance_map=source_map)
        except TypeError as error:
            self.fail('Provenance-aware audit is unavailable: ' + str(error))

    def test_legacy_statistical_pass_is_declared_unverified_diagnostic(self):
        rows = records()
        rows[0]['source_note'] = {'unknown_n': None, 'locator_note': 'retained'}
        rows[0]['canonical_campaign_id'] = 'caller-asserted-not-authenticated'
        report = validate_linear_candidate(rows, variable='layer_height_mm')
        self.assertEqual(report['status'], 'CANDIDATE_PASSED_REQUIRES_SOURCE_AND_SCOPE_REVIEW')
        self.assertEqual(report.get('independence_status'), 'CALLER_DECLARED_UNVERIFIED')
        self.assertEqual(report.get('declared_lineages'), ['A', 'B', 'C'])
        self.assertEqual(report.get('canonical_campaigns'), [])
        self.assertFalse(report.get('independent_validation_established', True))
        self.assertEqual(report.get('input_provenance', [])[0]['provided']['source_note'],
                         {'unknown_n': None, 'locator_note': 'retained'})
        self.assertFalse(report['accepted_for_runtime'])

    def test_cross_doi_aliases_canonicalize_to_two_campaigns_before_folds(self):
        rows, source_map = mapped_records()
        for entry in source_map['observations'][:6]:
            entry['canonical_campaign_id'] = 'campaign-AB'
        report = self.audit(rows, source_map)
        self.assertEqual(report['status'], 'INSUFFICIENT_EVIDENCE')
        self.assertEqual(report['canonical_campaigns'], ['campaign-AB', 'campaign-C'])
        self.assertEqual(report['publication_count'], 3)
        self.assertEqual(report['folds'], [])

    def test_independent_campaigns_may_have_identical_rounded_curves(self):
        rows, source_map = mapped_records()
        rows[0]['source_doi'] = 'https://doi.org/10.9999/SYNTHETIC.A'
        report = self.audit(rows, source_map)
        self.assertEqual(report['status'], 'CANDIDATE_PASSED_REQUIRES_SOURCE_AND_SCOPE_REVIEW')
        self.assertEqual(report['canonical_campaigns'], ['campaign-A', 'campaign-B', 'campaign-C'])
        self.assertEqual(len(report['folds']), 3)
        self.assertEqual(report['provenance_map']['status'], 'INTERNALLY_VALIDATED_METADATA')
        self.assertFalse(report['provenance_map']['source_authenticity_verified'])
        self.assertFalse(report['independent_validation_established'])
        self.assertFalse(report['accepted_for_runtime'])

    def test_original_outcome_alias_reuse_is_detected_even_with_different_values(self):
        rows, source_map = mapped_records()
        source_map['observations'][3].update(canonical_campaign_id='campaign-A',
                                            original_outcome_id='original-A-0')
        rows[3]['value_mpa'] = 46.01
        report = self.audit(rows, source_map)
        self.assertEqual(report['status'], 'REJECTED_INPUT')
        self.assertTrue(any('ORIGINAL_OUTCOME_REUSED' in r['reasons'] for r in report['exclusions']))
        self.assertEqual(report['folds'], [])

    def test_legacy_local_outcome_labels_are_preserved_without_global_identity(self):
        rows = records()
        rows[0].update(source_id='LAB-A', original_outcome_id='S1')
        rows[3].update(source_id='LAB-B', original_outcome_id='S1')
        report = validate_linear_candidate(rows, variable='layer_height_mm')
        self.assertEqual(report['status'], 'CANDIDATE_PASSED_REQUIRES_SOURCE_AND_SCOPE_REVIEW')
        self.assertEqual(report['input_provenance'][0]['provided']['original_outcome_id'], 'S1')
        self.assertEqual(report['input_provenance'][3]['provided']['original_outcome_id'], 'S1')
        self.assertIsNone(report['input_provenance'][0]['original_outcome_id'])
        self.assertIsNone(report['input_provenance'][3]['original_outcome_id'])
        self.assertEqual(report['independence_status'], 'CALLER_DECLARED_UNVERIFIED')

    def test_one_publication_can_contain_multiple_curated_campaigns(self):
        rows, source_map = mapped_records()
        for row, entry in zip(rows, source_map['observations']):
            row.update(study_id='one-paper', source_doi='10.9999/one-paper')
            entry['source_doi'] = '10.9999/one-paper'
        report = self.audit(rows, source_map)
        self.assertEqual(report['status'], 'CANDIDATE_PASSED_REQUIRES_SOURCE_AND_SCOPE_REVIEW')
        self.assertEqual(report['publication_count'], 1)
        self.assertEqual(len(report['canonical_campaigns']), 3)

    def test_aggregates_with_unknown_or_known_n_never_expand_into_specimens(self):
        for n in (None, 15):
            with self.subTest(n=n):
                rows, source_map = mapped_records()
                for row, entry in zip(rows, source_map['observations']):
                    row.update(observation_kind='PUBLISHED_AGGREGATE', n=n)
                    entry.update(observation_kind='PUBLISHED_AGGREGATE', n=n)
                report = self.audit(rows, source_map)
                self.assertEqual(report['status'], 'REJECTED_INPUT')
                self.assertEqual(report['input_rows'], 9)
                self.assertEqual(report['eligible_rows'], 0)
                self.assertEqual(report['folds'], [])
                self.assertTrue(all('AGGREGATE_NOT_SPECIMEN' in r['reasons'] for r in report['exclusions']))
                self.assertEqual(report['input_provenance'][0]['provided']['n'], n)

    def test_declared_aggregate_is_blocked_in_legacy_mode(self):
        rows = records()
        rows[0].update(observation_kind='PUBLISHED_AGGREGATE', n=None)
        report = validate_linear_candidate(rows, variable='layer_height_mm')
        self.assertEqual(report['status'], 'REJECTED_INPUT')
        self.assertIn('AGGREGATE_NOT_SPECIMEN', report['exclusions'][0]['reasons'])

    def test_unresolved_abs_overlap_never_receives_invented_campaign_or_specimen(self):
        for source_id, doi in (('M05', '10.3390/polym15092011'),
                               ('M06', '10.3390/polym16081106'),
                               ('M07', '10.1016/j.prostr.2024.06.029')):
            with self.subTest(source_id=source_id):
                rows = records()
                rows[0].update(source_id=source_id, source_doi=doi)
                report = validate_linear_candidate(rows, variable='layer_height_mm')
                self.assertEqual(report['status'], 'REJECTED_INPUT')
                self.assertIn('UNRESOLVED_EXPERIMENTAL_OVERLAP', report['exclusions'][0]['reasons'])
                self.assertIsNone(report['input_provenance'][0]['canonical_campaign_id'])
                self.assertIsNone(report['input_provenance'][0]['original_outcome_id'])

    def test_curated_map_cannot_override_unresolved_abs_publication(self):
        rows, source_map = mapped_records()
        rows[0].update(source_id='M05', source_doi='10.3390/polym15092011')
        source_map['observations'][0].update(source_id='M05', source_doi='10.3390/polym15092011')
        report = self.audit(rows, source_map)
        self.assertEqual(report['status'], 'REJECTED_INPUT')
        self.assertIn('UNRESOLVED_EXPERIMENTAL_OVERLAP', report['exclusions'][0]['reasons'])

    def test_generic_m05_label_does_not_quarantine_an_unrelated_publication(self):
        rows, source_map = mapped_records()
        rows[0]['source_id'] = 'M05'
        source_map['observations'][0]['source_id'] = 'M05'
        report = self.audit(rows, source_map)
        self.assertEqual(report['status'], 'CANDIDATE_PASSED_REQUIRES_SOURCE_AND_SCOPE_REVIEW')
        self.assertEqual(report['canonical_campaigns'], ['campaign-A', 'campaign-B', 'campaign-C'])

    def test_known_abs_doi_is_quarantined_under_a_different_source_label(self):
        rows = records()
        rows[0].update(source_id='ANOTHER-REGISTRY-LABEL',
                       source_doi='https://doi.org/10.3390/POLYM15092011')
        report = validate_linear_candidate(rows, variable='layer_height_mm')
        self.assertEqual(report['status'], 'REJECTED_INPUT')
        self.assertIn('UNRESOLVED_EXPERIMENTAL_OVERLAP', report['exclusions'][0]['reasons'])

    def test_malformed_maps_fail_closed_instead_of_legacy_fallback(self):
        _, good = mapped_records()
        malformed = [False, [], {}, dict(good, observations=True), dict(good, map_id=True)]
        for field in ('source_id', 'source_doi', 'source_locator', 'canonical_campaign_id',
                      'original_outcome_id', 'review_locator', 'observation_kind', 'review_status'):
            bad = deepcopy(good); bad['observations'][0][field] = True; malformed.append(bad)
        bad = deepcopy(good); bad['observations'][0]['n'] = True; malformed.append(bad)
        bad = deepcopy(good); bad['observations'].append(deepcopy(bad['observations'][0])); malformed.append(bad)
        bad = deepcopy(good); bad['observations'][3]['original_outcome_id'] = 'original-A-0'; malformed.append(bad)
        for index, source_map in enumerate(malformed):
            with self.subTest(malformed_case=index):
                report = self.audit(mapped_records()[0], source_map)
                self.assertEqual(report['status'], 'REJECTED_INPUT')
                self.assertEqual(report['provenance_map']['status'], 'INVALID_PROVENANCE_MAP')
                self.assertEqual(report['folds'], [])

    def test_missing_or_mismatched_source_mapping_cannot_fall_back_to_declared_ids(self):
        rows, source_map = mapped_records()
        source_map['observations'].pop()
        report = self.audit(rows, source_map)
        self.assertEqual(report['status'], 'REJECTED_INPUT')
        self.assertIn('SOURCE_OBSERVATION_NOT_MAPPED', report['exclusions'][-1]['reasons'])
        rows, source_map = mapped_records(); rows[0]['source_doi'] = '10.9999/wrong'
        report = self.audit(rows, source_map)
        self.assertIn('SOURCE_PUBLICATION_MISMATCH', report['exclusions'][0]['reasons'])

    def test_unresolved_map_entry_blocks_without_synthesizing_identity(self):
        rows, source_map = mapped_records()
        entry = source_map['observations'][0]
        entry.update(review_status='UNRESOLVED_OVERLAP', overlap_group_id='TEST_ONLY_OVERLAP')
        entry.pop('canonical_campaign_id'); entry.pop('original_outcome_id')
        report = self.audit(rows, source_map)
        self.assertEqual(report['status'], 'REJECTED_INPUT')
        self.assertIn('UNRESOLVED_EXPERIMENTAL_OVERLAP', report['exclusions'][0]['reasons'])
        self.assertIsNone(report['input_provenance'][0]['canonical_campaign_id'])

    def test_inputs_and_source_map_are_not_mutated_and_metadata_is_hashed(self):
        rows, source_map = mapped_records()
        before_rows, before_map = deepcopy(rows), deepcopy(source_map)
        report = self.audit(rows, source_map)
        self.assertEqual(rows, before_rows); self.assertEqual(source_map, before_map)
        report['input_provenance'][0]['provided']['source_id'] = 'changed'
        self.assertEqual(rows[0]['source_id'], 'SYNTHETIC-A')
        changed = deepcopy(source_map); changed['observations'][0]['review_locator'] = 'another note'
        self.assertNotEqual(self.audit(rows, changed)['provenance_map']['sha256'],
                            report['provenance_map']['sha256'])

    def test_boolean_observation_claims_are_invalid_not_raw_specimens(self):
        for field in ('source_id', 'source_doi', 'observation_kind', 'original_outcome_id', 'n'):
            rows, source_map = mapped_records(); rows[0][field] = True
            report = self.audit(rows, source_map)
            self.assertEqual(report['status'], 'REJECTED_INPUT')
            self.assertEqual(report['folds'], [])

    def test_invalid_map_is_never_reported_as_curated_identity(self):
        report = self.audit(mapped_records()[0], False)
        self.assertEqual(report['independence_status'], 'INVALID_PROVENANCE_MAP')
        self.assertEqual(report['canonical_campaigns'], [])


class EvidenceProvenanceTests(unittest.TestCase):
    def test_catalog_preserves_declared_campaign_and_separates_publications(self):
        a = deepcopy(evidence._CATALOG[0]); a['experimental_lineage_id'] = 'DECLARED-CAMPAIGN'
        b = deepcopy(a); b.update(source_id='SYNTHETIC-ALIAS', doi='10.9999/alias')
        with patch.object(evidence, '_CATALOG', [a, b]):
            rows = evidence.literature_comparisons({'material_family': 'PLA'})
            coverage = evidence.evidence_coverage({'material_family': 'PLA'})
        self.assertEqual([r['experimental_lineage_id'] for r in rows], ['DECLARED-CAMPAIGN'] * 2)
        self.assertEqual(coverage['experimental_lineages'], ['DECLARED-CAMPAIGN'])
        self.assertEqual(coverage['publication_count'], 2)
        self.assertEqual(coverage['canonical_campaigns'], [])
        self.assertFalse(coverage['independent_validation_established'])

    def test_observation_map_groups_aggregate_aliases_without_changing_values(self):
        a = deepcopy(evidence._CATALOG[0])
        a.update(source_id='SYN-A', doi='10.9999/a', locator='aggregate cell')
        a['observations'] = [dict(layer_height_mm=.1, value_mpa=46., n=None,
                                  source_locator='aggregate cell')]
        b = deepcopy(a); b.update(source_id='SYN-B', doi='10.9999/b')
        b['observations'][0]['value_mpa'] = 46.01
        source_map = dict(schema='PROVENANCE_OBSERVATION_MAP_V1', map_id='TEST_ONLY_AGGREGATE',
                          observations=[dict(source_id='SYN-' + label, source_doi='10.9999/' + label.lower(),
                                             source_locator='aggregate cell', review_status='CURATED_IDENTITY',
                                             observation_kind='PUBLISHED_AGGREGATE', n=None,
                                             canonical_campaign_id='campaign-AB', original_outcome_id='aggregate-origin',
                                             review_locator='TEST_ONLY alias note') for label in ('A', 'B')])
        with patch.object(evidence, '_CATALOG', [a, b]):
            try:
                rows = evidence.literature_comparisons({'material_family': 'PLA'}, provenance_map=source_map)
                coverage = evidence.evidence_coverage({'material_family': 'PLA'}, provenance_map=source_map)
            except TypeError as error:
                self.fail('Provenance-aware comparison is unavailable: ' + str(error))
        self.assertEqual([r['experimental_lineage_id'] for r in rows], ['campaign-AB'] * 2)
        self.assertEqual([r['observations'][0]['value_mpa'] for r in rows], [46., 46.01])
        self.assertEqual([r['observations'][0]['n'] for r in rows], [None, None])
        self.assertEqual(coverage['canonical_campaigns'], ['campaign-AB'])
        self.assertEqual(coverage['publication_count'], 2)
        self.assertFalse(any(r['runtime_calibration_eligible'] for r in rows))

    def test_public_report_counts_declared_campaigns_not_catalog_length_as_verified(self):
        report = public_data_report()
        self.assertEqual(report.get('publication_count'), 2)
        self.assertEqual(report.get('declared_campaigns'), ['W027_W028', 'W029_W030'])
        self.assertEqual(report.get('canonical_campaigns'), [])
        self.assertEqual(report['experimental_lineages'], 2)
        self.assertFalse(report.get('independent_validation_established', True))
        rows = [r for entry in report['materials'] for r in entry['calibration_audit'].get('input_provenance', [])]
        self.assertEqual(len(rows), 18)
        self.assertTrue(all(r['provided']['observation_kind'] == 'RAW_SPECIMEN' for r in rows))

    def test_map_cannot_relabel_published_catalog_aggregate_as_raw_specimen(self):
        entry = deepcopy(evidence._CATALOG[0])
        entry.update(source_id='SYN-A', doi='10.9999/a', locator='aggregate cell')
        entry['observations'] = [dict(layer_height_mm=.1, value_mpa=46., n=None,
                                     source_locator='aggregate cell')]
        source_map = dict(schema='PROVENANCE_OBSERVATION_MAP_V1', map_id='TEST_ONLY_KIND_CONFLICT',
                          observations=[dict(source_id='SYN-A', source_doi='10.9999/a',
                                             source_locator='aggregate cell', review_status='CURATED_IDENTITY',
                                             observation_kind='RAW_SPECIMEN', canonical_campaign_id='campaign-A',
                                             original_outcome_id='claimed-raw-id', review_locator='TEST_ONLY')])
        with patch.object(evidence, '_CATALOG', [entry]):
            rows = evidence.literature_comparisons({'material_family': 'PLA'}, provenance_map=source_map)
        identity = rows[0]['observation_provenance'][0]
        self.assertIn('OBSERVATION_KIND_CONFLICT', identity['errors'])
        self.assertEqual(identity['observation_kind'], 'PUBLISHED_AGGREGATE')
        self.assertEqual(rows[0]['canonical_campaigns'], [])

    def test_invalid_map_keeps_comparisons_but_no_curated_campaign_claim(self):
        coverage = evidence.evidence_coverage({'material_family': 'ASA'}, provenance_map=False)
        report = public_data_report(provenance_map=False)
        self.assertEqual(coverage['provenance_map']['status'], 'INVALID_PROVENANCE_MAP')
        self.assertEqual(coverage['experimental_lineages'], [])
        self.assertEqual(coverage['comparison_count'], 1)
        self.assertEqual(report['campaign_identity_status'], 'INVALID_PROVENANCE_MAP')
        self.assertEqual(report['canonical_campaigns'], [])
        self.assertTrue(report['saved_extraction_arithmetic_passed'])


if __name__ == '__main__':
    unittest.main()
