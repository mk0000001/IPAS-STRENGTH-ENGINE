import copy
import unittest

from print_strength_engine.weakness import assess_candidates, VERSION
from print_strength_engine.capacity import VERSION as CAPACITY_VERSION
from print_strength_engine.automatic_sections import VERSION as SECTION_VERSION


def candidate(key, force, *, terminal=False):
    return {'kind':'LOCAL_THIN_SECTION','region_id':key,'rank':int(key),
            'section_normal_axis':'X','section_window_bounds_mm':[[0,10],[0,4],[0,2]],
            'selection_reason':'THIN_TERMINAL_ROOT' if terminal else 'LOCAL_SECTION_REDUCTION',
            'terminal_kind':'OBJECT_FREE_END' if terminal else None,
            'terminal_root_station_mm':5 if terminal else None,
            'thickness_proxy_mm':.8,'section_modulus_mm3':1,
            'estimated_capacity':{'calculation_status':'AUTOMATIC_REFERENCE_LOAD_ESTIMATE',
                'model_version':CAPACITY_VERSION,'bending_basis':'MINIMUM_OVER_ALL_LOCAL_MOMENT_DIRECTIONS',
                'is_failure_prediction':False,'bending_force_n':force,'bending_lever_mm':25,
                'reference_stress_area_basis':'UNKNOWN',
                'reference_transfer_assumption':{'source_area_basis':'UNKNOWN',
                  'target_area_basis':'DECLARED_NET_ROAD_ENVELOPE','verified':False,
                  'basis':'COUPON_REFERENCE_AS_HOMOGENEOUS_NET_SECTION_STRESS'}},
            'deposited_section':{'version':SECTION_VERSION,'status':'COMPLETE','complete':True,
                'sampled':False,'normal_axis':'X','provenance':'GCODE_WIDTH_HEIGHT_ASSUMPTION',
                'scope':'LOCAL_DECLARED_ROAD_REGION','tools':[0]}}


class WeaknessTest(unittest.TestCase):
    def test_reference_order_reverses_old_geometry_order_and_preserves_identity(self):
        source=[candidate('1',7),candidate('2',2),candidate('3',5)]
        original=copy.deepcopy(source)
        result=assess_candidates(source)
        self.assertEqual([r['region_id'] for r in result['candidates']],['2','3','1'])
        self.assertEqual([r['rank'] for r in result['candidates']],[1,2,3])
        self.assertEqual(source,original)
        self.assertFalse(result['is_failure_prediction'])
        self.assertEqual(result['version'],VERSION)
        self.assertEqual(result['rank_basis'],'COMPARABLE_LOCAL_25MM_REFERENCE_LOADS')

    def test_incomplete_candidate_does_not_mix_with_reference_ranking(self):
        rows=[candidate('1',7),candidate('2',2)]
        rows[1]['estimated_capacity']=None
        result=assess_candidates(rows)
        self.assertEqual([r['region_id'] for r in result['candidates']],['1','2'])
        self.assertEqual(result['rank_basis'],'GEOMETRIC_SECTION_COMPARISON')

    def test_removed_reference_restores_original_geometry_order(self):
        ranked=assess_candidates([candidate('1',7),candidate('2',2)])['candidates']
        self.assertEqual([row['region_id'] for row in ranked],['2','1'])
        for row in ranked:row['estimated_capacity']=None
        restored=assess_candidates(ranked)
        self.assertEqual([row['region_id'] for row in restored['candidates']],['1','2'])
        self.assertEqual(restored['rank_basis'],'GEOMETRIC_SECTION_COMPARISON')

    def test_multiple_material_tools_and_area_bases_are_not_silently_compared(self):
        rows=[candidate('1',7),candidate('2',2)]
        rows[1]['deposited_section']['tools']=[1]
        self.assertEqual(assess_candidates(rows)['rank_basis'],'GEOMETRIC_SECTION_COMPARISON')
        rows[1]['deposited_section']['tools']=[0]
        rows[1]['estimated_capacity']['reference_stress_area_basis']='INTERLAYER_CONTACT'
        self.assertEqual(assess_candidates(rows)['rank_basis'],'GEOMETRIC_SECTION_COMPARISON')

    def test_terminal_exposes_layer_separation_without_fabricating_weld_strength(self):
        row=assess_candidates([candidate('1',2,terminal=True)])['candidates'][0]
        assessment=row['weakness_assessment']
        self.assertIn('TERMINAL_ROOT_BENDING',assessment['mechanisms'])
        self.assertIn('FREE_EDGE_LAYER_SEPARATION_EXPOSURE',assessment['mechanisms'])
        self.assertEqual(assessment['weld_strength_status'],'UNMEASURED')
        self.assertIsNone(assessment['interlayer_failure_load_n'])
        self.assertEqual(row['estimated_capacity']['bending_force_n'],2)

    def test_perfect_declared_overlap_is_not_a_sound_weld_certification(self):
        from print_strength_engine.interlayer_contact import VERSION as CONTACT_VERSION
        row=candidate('1',2)
        row['interlayer_contact']={'version':CONTACT_VERSION,'status':'COMPLETE','complete':True,
            'sampled':False,'provenance':'GCODE_WIDTH_HEIGHT_ASSUMPTION',
            'scope':'LOCAL_DECLARED_ROAD_INTERLAYER_WINDOW',
            'section_window_bounds_mm':row['section_window_bounds_mm'],
            'interfaces_checked':4,'qualifying_interface_count':3,
            'minimum_smaller_footprint_overlap_ratio':1.,'observations':[],
            'actual_bond_measured':False,'molecular_weld_quality_verified':False}
        assessment=assess_candidates([row])['candidates'][0]['weakness_assessment']
        self.assertEqual(assessment['contact_geometry_status'],'COMPLETE')
        self.assertEqual(assessment['weld_strength_status'],'UNMEASURED')
        self.assertFalse(assessment['is_failure_prediction'])
        self.assertIsNone(assessment['interlayer_failure_load_n'])

    def test_nonfinite_or_wrong_window_contact_is_not_accepted(self):
        row=candidate('1',2)
        row['interlayer_contact']={'status':'COMPLETE','complete':True,
            'minimum_smaller_footprint_overlap_ratio':float('nan')}
        assessment=assess_candidates([row])['candidates'][0]['weakness_assessment']
        self.assertEqual(assessment['contact_geometry_status'],'UNAVAILABLE')

    def test_mismatched_reference_transfer_or_old_model_are_not_comparable(self):
        for field,value in [('model_version','OLD'),('bending_basis','PRINCIPAL_ONLY')]:
            rows=[candidate('1',7),candidate('2',2)]
            rows[1]['estimated_capacity'][field]=value
            self.assertEqual(assess_candidates(rows)['rank_basis'],'GEOMETRIC_SECTION_COMPARISON')
        rows=[candidate('1',7),candidate('2',2)]
        rows[1]['estimated_capacity']['reference_transfer_assumption']['verified']=True
        self.assertEqual(assess_candidates(rows)['rank_basis'],'GEOMETRIC_SECTION_COMPARISON')
        rows=[candidate('1',7),candidate('2',2)]
        rows[0]['material_reference_id']='GRADE_A';rows[1]['material_reference_id']='GRADE_B'
        self.assertEqual(assess_candidates(rows)['rank_basis'],'GEOMETRIC_SECTION_COMPARISON')

    def test_resolution_limited_or_incomplete_road_region_cannot_set_load_rank(self):
        rows=[candidate('1',7),candidate('2',2)]
        rows[1]['screening_quality']='RESOLUTION_LIMITED_FEATURE'
        self.assertEqual(assess_candidates(rows)['rank_basis'],'GEOMETRIC_SECTION_COMPARISON')
        rows[1].pop('screening_quality');rows[1]['deposited_section']['complete']=False
        self.assertEqual(assess_candidates(rows)['rank_basis'],'GEOMETRIC_SECTION_COMPARISON')


if __name__=='__main__':unittest.main()
