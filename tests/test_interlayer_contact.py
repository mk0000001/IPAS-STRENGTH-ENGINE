"""Declared-road overlaps remain geometric observations, not weld validation."""
import unittest
from copy import deepcopy
from math import inf,nextafter,ulp
from unittest.mock import patch
import print_strength_engine.interlayer_contact as contact_module
from print_strength_engine.interlayer_contact import StreamingInterlayerContact,valid_contact_descriptor


def candidate():
    return {'region_id':'region','section_window_bounds_mm':[[-10,20],[-10,20],[-1,20]]}


def add_square(collector,z,*,shift=0,width=1,side=4,layer=None):
    for y in range(side):
        collector.segment((shift,y+.5,z),(shift+side,y+.5,z),width,1,0,layer_number=layer or int(z))


def square_contact_with_intersection_excess(excess_width):
    """Emulate GEOS area roundoff using unit test squares, never user geometry."""
    from shapely.geometry import box
    from shapely.geometry.base import BaseGeometry
    original=BaseGeometry.intersection
    def intersect(left,right,*args,**kwargs):
        shape=original(left,right,*args,**kwargs)
        if left.area==right.area==shape.area==16.:
            return box(0,0,excess_width,4)
        return shape
    collector=StreamingInterlayerContact([candidate()])
    for z in range(1,7):add_square(collector,z)
    with patch.object(BaseGeometry,'intersection',intersect):
        return collector.finish()['region']


class InterlayerContactTests(unittest.TestCase):
    def test_fresh_equal_footprint_area_roundoff_is_normalized_to_geometric_bound(self):
        # Exact scalar values from a fresh anonymous source assessment.
        lower=15.743535805252982;upper=15.743535800771948;overlap=15.743535800771951
        normalize=getattr(contact_module,'_bounded_overlap_area',None)
        self.assertTrue(callable(normalize),'Source overlap roundoff requires a bounded normalization')
        self.assertEqual(normalize(overlap,min(lower,upper)),upper)
        self.assertEqual(normalize(6.,16.),6.)
        for bound in (2.**-40,16.,2.**40):
            with self.subTest(bound=bound):
                self.assertEqual(normalize(bound+64*ulp(bound),bound),bound)
                with self.assertRaises(contact_module.UnsupportedGeometry):
                    normalize(bound+65*ulp(bound),bound)
        for invalid in (16.001,-.001,float('nan'),float('inf'),True):
            with self.subTest(invalid=invalid):
                with self.assertRaises(contact_module.UnsupportedGeometry):normalize(invalid,16.)

    def test_generated_roundoff_contact_stays_valid_through_descriptor_and_weakness_readers(self):
        from print_strength_engine.weakness import assess_candidates
        value=square_contact_with_intersection_excess(nextafter(4.,inf))
        self.assertEqual(value['status'],'COMPLETE')
        for row in value['interfaces']:
            self.assertEqual(row['overlap_area_mm2'],16.)
            for field in ('upper_overlap_ratio','lower_overlap_ratio','smaller_footprint_overlap_ratio',
                          'interior_smaller_overlap_ratio'):
                self.assertEqual(row[field],1.)
        self.assertTrue(valid_contact_descriptor(value,candidate()['section_window_bounds_mm']))
        row={**candidate(),'kind':'LOCAL_THIN_SECTION','rank':1,'interlayer_contact':value}
        assessment=assess_candidates([row])['candidates'][0]['weakness_assessment']
        self.assertEqual(assessment['contact_geometry_status'],'COMPLETE')
        self.assertEqual(assessment['minimum_smaller_footprint_overlap_ratio'],1.)
        self.assertEqual(assessment['weld_strength_status'],'UNMEASURED')
        self.assertIsNone(assessment['interlayer_failure_load_n'])
        self.assertFalse(assessment['is_failure_prediction'])

    def test_materially_excessive_intersection_withholds_instead_of_clamping(self):
        value=square_contact_with_intersection_excess(4.001)
        self.assertEqual(value['status'],'WITHHELD')
        self.assertIn('INVALID_INTERLAYER_OVERLAP_AREA',value['assessment_gaps'])
        self.assertTrue(valid_contact_descriptor(value,candidate()['section_window_bounds_mm']))

    def test_cached_noncanonical_excess_cannot_bypass_reader_bounds(self):
        collector=StreamingInterlayerContact([candidate()])
        for z in range(1,7):add_square(collector,z)
        valid=collector.finish()['region']
        for field in ('upper_overlap_ratio','lower_overlap_ratio','smaller_footprint_overlap_ratio',
                      'interior_smaller_overlap_ratio'):
            value=deepcopy(valid);value['interfaces'][0][field]=nextafter(1.,inf)
            with self.subTest(field=field):
                self.assertFalse(valid_contact_descriptor(value,candidate()['section_window_bounds_mm']))

    def test_full_overlap_does_not_claim_bond_strength_is_verified(self):
        collector=StreamingInterlayerContact([candidate()])
        for z in range(1,7):add_square(collector,z)
        value=collector.finish()['region']
        self.assertEqual(value['status'],'COMPLETE')
        self.assertEqual(value['layer_count'],6)
        self.assertAlmostEqual(value['minimum_smaller_footprint_overlap_ratio'],1)
        self.assertEqual(value['observations'],[])
        self.assertFalse(value['actual_bond_measured'])
        self.assertFalse(value['molecular_weld_quality_verified'])
        self.assertFalse(value['is_failure_prediction'])
        self.assertTrue(valid_contact_descriptor(value,candidate()['section_window_bounds_mm']))

    def test_repeated_large_contact_loss_is_a_geometric_observation(self):
        collector=StreamingInterlayerContact([candidate()])
        for z in range(1,9):add_square(collector,z,shift=0 if z%2 else 2.5)
        value=collector.finish()['region']
        self.assertGreater(value['qualifying_interface_count'],0)
        self.assertTrue(any(item['kind']=='LOW_DECLARED_LAYER_OVERLAP' for item in value['observations']))
        worst=value['worst_qualifying_interface']
        self.assertAlmostEqual(worst['smaller_footprint_overlap_ratio'],.375)
        self.assertAlmostEqual(worst['overlap_area_mm2'],6)

    def test_expansion_and_shrinkage_are_not_bad_bonds(self):
        collector=StreamingInterlayerContact([candidate()])
        for z,side in enumerate((3,3,4,4,3,3),1):add_square(collector,z,side=side)
        value=collector.finish()['region']
        self.assertEqual(value['observations'],[])
        self.assertAlmostEqual(value['minimum_smaller_footprint_overlap_ratio'],1)
        self.assertTrue(any(row['upper_overlap_ratio']<1 for row in value['interfaces']))

    def test_tiny_terminal_caps_do_not_become_contact_failure_candidates(self):
        collector=StreamingInterlayerContact([candidate()])
        for z in range(1,7):
            collector.segment((0,0,z),(.1,0,z),.1,1,0,layer_number=z)
        value=collector.finish()['region']
        self.assertEqual(value['qualifying_interface_count'],0)
        self.assertIsNone(value['worst_qualifying_interface'])
        self.assertEqual(value['observations'],[])

    def test_first_or_last_interface_is_not_a_low_bond_warning(self):
        collector=StreamingInterlayerContact([candidate()])
        for z in range(1,7):add_square(collector,z,shift=10 if z==1 else 0)
        value=collector.finish()['region']
        self.assertEqual(value['interfaces'][0]['overlap_area_mm2'],0)
        self.assertFalse(value['interfaces'][0]['qualifies_for_diagnostic'])
        self.assertEqual(value['observations'],[])

    def test_nonoverlap_and_vertical_gap_are_separate_geometry_evidence(self):
        collector=StreamingInterlayerContact([candidate()])
        for z in range(1,9):add_square(collector,z if z<5 else z+.25,shift=0 if z%2 else 6,layer=z)
        value=collector.finish()['region']
        kinds={row['kind'] for row in value['observations']}
        self.assertIn('NO_DECLARED_LAYER_OVERLAP',kinds)
        self.assertIn('DECLARED_VERTICAL_GAP',kinds)
        gap=next(row for row in value['interfaces'] if row['geometric_vertical_gap_mm']>.1)
        self.assertFalse(gap['adjacent_plane_verified'])

    def test_clipping_growth_does_not_invent_bad_overlap(self):
        region=candidate();region['section_window_bounds_mm'][0]=[2,10]
        collector=StreamingInterlayerContact([region])
        for z,shift in enumerate((6,5,4,3,2,1),1):add_square(collector,z,shift=shift)
        value=collector.finish()['region']
        self.assertEqual(value['observations'],[])

    def test_incomplete_or_missing_dimensions_withholds_geometry(self):
        collector=StreamingInterlayerContact([candidate()])
        add_square(collector,1)
        value=collector.finish(complete=False)['region']
        self.assertEqual(value['status'],'WITHHELD')
        self.assertIn('INCOMPLETE_SOURCE_SCAN',value['assessment_gaps'])
        collector=StreamingInterlayerContact([candidate()])
        collector.segment((0,0,1),(4,0,1),None,1,0,layer_number=1)
        self.assertIn('DECLARED_ROAD_DIMENSIONS_REQUIRED',collector.finish()['region']['assessment_gaps'])

    def test_budgets_and_cancellation_are_enforced(self):
        collector=StreamingInterlayerContact([candidate()],max_records=1,max_total_records=1)
        add_square(collector,1)
        value=collector.finish()['region']
        self.assertEqual(value['status'],'WITHHELD')
        self.assertIn('INTERLAYER_GEOMETRY_BUDGET_EXCEEDED',value['assessment_gaps'])
        collector=StreamingInterlayerContact([candidate()],cancelled=lambda:True)
        with self.assertRaisesRegex(RuntimeError,'ANALYSIS_CANCELLED'):collector.finish()

    def test_mixed_height_same_plane_does_not_claim_a_single_interface(self):
        collector=StreamingInterlayerContact([candidate()])
        add_square(collector,1)
        collector.segment((0,5,2),(4,5,2),1,.5,0,layer_number=2)
        add_square(collector,2)
        value=collector.finish()['region']
        self.assertEqual(value['status'],'WITHHELD')
        self.assertIn('INCONSISTENT_DECLARED_LAYER_INTERVAL',value['assessment_gaps'])

    def test_cached_metrics_cannot_be_nonfinite_mismatched_or_invented(self):
        collector=StreamingInterlayerContact([candidate()])
        for z in range(1,7):add_square(collector,z)
        valid=collector.finish()['region'];bounds=candidate()['section_window_bounds_mm']
        self.assertTrue(valid_contact_descriptor(valid,bounds))
        corruptions=[
            lambda value:value.update(version='old'),
            lambda value:value.update(actual_bond_measured=True),
            lambda value:value.update(layers=[]),
            lambda value:value.update(interfaces={}),
            lambda value:value['interfaces'][1].update(smaller_footprint_overlap_ratio=float('nan')),
            lambda value:value['interfaces'][1].update(overlap_area_mm2=-1),
            lambda value:value['interfaces'][0].update(qualifies_for_diagnostic=True),
            lambda value:value['layers'][2].update(top_z_mm=100),
            lambda value:value['layers'][2].update(tools=[-1]),
            lambda value:value.update(observations=[{'kind':'LOW_DECLARED_LAYER_OVERLAP','interface_index':1}]),
            lambda value:value['interfaces'][1].update(upper_overlap_ratio=.2),
            lambda value:value['interfaces'][1].update(geometric_vertical_gap_mm=1),
            lambda value:value.update(qualifying_interface_count=100),
            lambda value:value.update(retained_records=10**9),
            lambda value:value.update(worst_qualifying_interface=None)]
        for mutate in corruptions:
            value=deepcopy(valid);mutate(value)
            with self.subTest(value=value):self.assertFalse(valid_contact_descriptor(value,bounds))
        for malformed in (None,[],{},'complete'):
            self.assertFalse(valid_contact_descriptor(malformed,bounds))


if __name__=='__main__':unittest.main()
