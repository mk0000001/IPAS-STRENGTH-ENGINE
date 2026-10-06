"""End-zone selection compares root sections, never the vanishing free cap."""
import unittest
import numpy as np

from print_strength_engine.local_thickness import screen_solid


def strip(narrow_end=False, rounded_cap=False):
    solid=np.zeros((12,45,300),bool)
    solid[4:6,5:40,4:296]=True
    if narrow_end:
        solid[4:6,:,270:296]=False
        solid[4:6,21:25,270:296]=True
    if rounded_cap:
        solid[4:6,:,285:296]=False
        solid[4:6,21:25,285:296]=True
    return solid


class TerminalScreening(unittest.TestCase):
    def test_narrow_same_thickness_terminal_is_retained_before_body(self):
        result=screen_solid(strip(narrow_end=True),[0,0,0],.4)
        ends=[c for c in result['candidates'] if c.get('end_role')=='HIGH_END'
              and c.get('terminal_kind')=='OBJECT_FREE_END']
        self.assertTrue(ends,'A short narrow end must survive the six-candidate limit')
        end=ends[0]
        self.assertEqual(end['rank'],1)
        self.assertLess(end['min_section_area_mm2'],2)
        self.assertLess(end['section_station_mm'],end['terminal_end_station_mm']-5)

    def test_uniform_strip_keeps_representative_body_without_voxel_count_order(self):
        result=screen_solid(strip(),[0,0,0],.4)
        candidates=result['candidates']
        self.assertLessEqual(len(candidates),3)
        self.assertEqual({c.get('end_role') for c in candidates},
                         {'LOW_END','INTERIOR','HIGH_END'})
        body=next(c for c in candidates if c['end_role']=='INTERIOR')
        self.assertTrue(40<body['position_mm'][0]<80)
        self.assertEqual(body['selection_reason'],'UNIFORM_THIN_REGION')
        self.assertFalse(result['is_failure_prediction'])
        self.assertEqual(result['rank_basis'],'GEOMETRIC_COMPARISON_NOT_FAILURE_ORDER')

    def test_small_rounded_free_cap_does_not_make_root_section_weaker(self):
        result=screen_solid(strip(rounded_cap=True),[0,0,0],.4)
        ends=[c for c in result['candidates'] if c.get('end_role')=='HIGH_END']
        self.assertTrue(ends)
        end=ends[0]
        body=next(c for c in result['candidates'] if c.get('end_role')=='INTERIOR')
        self.assertAlmostEqual(end['section_modulus_mm3'],body['section_modulus_mm3'])
        self.assertAlmostEqual(end['min_section_area_mm2'],body['min_section_area_mm2'])
        self.assertNotEqual(end['rank'],1,'A tiny rounded cap cannot win by its disappearing tip section')
        self.assertEqual(end['cap_exclusion_policy'],'TERMINAL_INTERIOR_QUARTER')
        self.assertLess(end['section_evaluation_interval_mm'][1],285*.4)

    def test_thin_transition_is_not_labeled_an_object_free_end(self):
        solid=np.zeros((30,45,300),bool)
        solid[3:25,5:40,4:100]=True
        solid[13:15,21:25,98:296]=True
        result=screen_solid(solid,[0,0,0],.4)
        transitions=[c for c in result['candidates']
                     if c.get('terminal_kind')=='THIN_REGION_TRANSITION']
        self.assertTrue(transitions)
        self.assertTrue(all(c['cap_exclusion_policy']=='NONE' for c in transitions))

    def test_nearby_disconnected_objects_are_not_spatially_deduplicated(self):
        solid=np.zeros((12,25,120),bool)
        solid[4:6,5:9,4:116]=True
        solid[4:6,11:15,4:116]=True
        result=screen_solid(solid,[0,0,0],.4)
        candidates=result['candidates']
        self.assertEqual(len({c.get('object_component_id') for c in candidates}),2)
        for object_id in {c['object_component_id'] for c in candidates}:
            roles={c['end_role'] for c in candidates if c['object_component_id']==object_id}
            self.assertIn('LOW_END',roles)
            self.assertIn('HIGH_END',roles)
        self.assertLessEqual(len(candidates),6)

    def test_terminal_marker_cuts_interval_and_world_coordinates_agree(self):
        delta=[100,200,300]
        first=screen_solid(strip(narrow_end=True),[0,0,0],.4)['candidates']
        shifted=screen_solid(strip(narrow_end=True),delta,.4)['candidates']
        self.assertTrue(any(c.get('terminal_kind')=='OBJECT_FREE_END' for c in first))
        self.assertEqual(len(first),len(shifted))
        for a,b in zip(first,shifted):
            axis='XYZ'.index(a['section_normal_axis'])
            self.assertAlmostEqual(b['section_station_mm']-a['section_station_mm'],delta[axis])
            self.assertEqual(a['position_mm'][axis],a['section_station_mm'])
            if a.get('terminal_kind')=='OBJECT_FREE_END':
                lo,hi=a['section_evaluation_interval_mm']
                for field in ('section_station_mm','axial_section_station_mm','bending_section_station_mm'):
                    self.assertLessEqual(lo,a[field]);self.assertLessEqual(a[field],hi)
                self.assertEqual(a['terminal_root_position_mm'],a['position_mm'])
                self.assertEqual(a['terminal_root_station_mm'],a['section_station_mm'])
                for key in ('terminal_end_position_mm','terminal_root_position_mm'):
                    self.assertTrue(np.allclose(np.asarray(b[key])-a[key],delta))
                self.assertTrue(np.allclose(np.asarray(b['section_evaluation_interval_mm'])-
                                            a['section_evaluation_interval_mm'],delta[axis]))

    def test_geometric_score_has_declared_same_moment_arm_and_units(self):
        result=screen_solid(strip(narrow_end=True),[0,0,0],.4)
        for candidate in result['candidates']:
            comparison=candidate.get('screening_comparison')
            self.assertIsNotNone(comparison)
            self.assertEqual(comparison['basis'],'EQUAL_25MM_PRINCIPAL_BENDING_GEOMETRY')
            self.assertEqual(comparison['lever_mm'],25)
            self.assertAlmostEqual(comparison['stress_per_unit_force_mpa_per_n'],
                                   25/candidate['section_modulus_mm3'])

    def test_single_voxel_island_is_marked_uncertain_not_prioritized_as_weakest(self):
        solid=strip()
        solid[4:6,42:43,20:40]=True
        result=screen_solid(solid,[0,0,0],.4)
        candidates=result['candidates']
        self.assertEqual(candidates[0].get('screening_quality'),'RESOLVED_GEOMETRIC_REGION')
        islands=[c for c in candidates if c.get('screening_quality')=='RESOLUTION_LIMITED_FEATURE']
        self.assertTrue(islands,'Keep small possibly-real features, with their quality warning')
        self.assertEqual(islands[0]['object_component_voxel_count'],40)
        self.assertEqual(min(islands[0]['object_component_voxel_span_xyz']),1)
        self.assertEqual(islands[0]['object_component_basis'],
                         'VOXEL_FACE_CONNECTED_REGION_NOT_SOURCE_OBJECT_ID')

    def test_short_connected_appendage_still_has_a_free_end_root(self):
        solid=np.zeros((30,45,90),bool)
        solid[3:25,5:40,4:65]=True
        solid[13:15,21:25,63:85]=True
        result=screen_solid(solid,[0,0,0],.4)
        ends=[c for c in result['candidates'] if c.get('terminal_kind')=='OBJECT_FREE_END']
        self.assertTrue(ends)
        end=ends[0]
        self.assertEqual(end['end_role'],'HIGH_END')
        self.assertLess(end['section_evaluation_interval_mm'][1],33)

    def test_short_independent_strip_records_both_ends_without_free_cap_cuts(self):
        solid=np.zeros((12,25,35),bool);solid[4:6,5:20,4:25]=True
        result=screen_solid(solid,[0,0,0],.4)
        candidate=result['candidates'][0]
        self.assertEqual(candidate.get('end_role'),'BOTH_ENDS')
        self.assertEqual(candidate['terminal_kind'],'OBJECT_FREE_END')
        self.assertEqual(len(candidate['terminal_end_positions_mm']),2)
        self.assertEqual(candidate['cap_exclusion_policy'],'TERMINAL_CENTRAL_HALF')
        self.assertTrue(candidate['section_evaluation_interval_mm'][0]>1.6)
        self.assertTrue(candidate['section_evaluation_interval_mm'][1]<10)

    def test_taper_reason_reports_geometry_change_without_layer_adhesion_claim(self):
        result=screen_solid(strip(rounded_cap=True),[0,0,0],.4)
        end=next(c for c in result['candidates'] if c.get('end_role')=='HIGH_END')
        self.assertEqual(end.get('selection_reason'),'TAPERED_TERMINAL_ROOT')
        self.assertLess(end['terminal_geometry']['outer_to_interior_area_ratio'],1)
        self.assertFalse(end['terminal_geometry']['is_layer_adhesion_assessment'])

    def test_axis_permutation_preserves_analytic_geometry_and_root_policy(self):
        reference=screen_solid(strip(narrow_end=True),[0,0,0],.4)['candidates'][0]
        for permutation,axis in (((0,1,2),'X'),((0,2,1),'Y'),((2,1,0),'Z')):
            with self.subTest(axis=axis):
                solid=np.transpose(strip(narrow_end=True),permutation)
                end=screen_solid(solid,[0,0,0],.4)['candidates'][0]
                self.assertEqual(end['section_normal_axis'],axis)
                self.assertEqual(end['terminal_axis'],axis)
                self.assertAlmostEqual(end['min_section_area_mm2'],1.28)
                self.assertAlmostEqual(end['section_modulus_mm3'],1.6*.8**2/6,places=4)
                self.assertAlmostEqual(end['screening_score'],reference['screening_score'])
                self.assertLess(end['terminal_root_station_mm'],end['terminal_end_station_mm']-5)

    def test_reflection_moves_terminal_root_without_changing_geometry_score(self):
        solid=strip(narrow_end=True)
        high=screen_solid(solid,[0,0,0],.4)['candidates'][0]
        low=screen_solid(solid[:,:,::-1],[0,0,0],.4)['candidates'][0]
        self.assertEqual(high['end_role'],'HIGH_END')
        self.assertEqual(low['end_role'],'LOW_END')
        self.assertAlmostEqual(high['min_section_area_mm2'],low['min_section_area_mm2'])
        self.assertAlmostEqual(high['screening_score'],low['screening_score'])
        self.assertAlmostEqual(high['terminal_root_station_mm']+low['terminal_root_station_mm'],120)

    def test_reflection_preserves_abrupt_selected_root_description(self):
        solid=strip(narrow_end=True)
        high=screen_solid(solid,[0,0,0],.4)['candidates'][0]
        low=screen_solid(solid[:,:,::-1],[0,0,0],.4)['candidates'][0]
        for end in (high,low):
            self.assertEqual(end['terminal_root_selection_basis'],'ABRUPT_NARROWING_IN_INTERIOR_HALF')
            # The selected root has four 0.4 mm cells across and two in height:
            # its 1.6 x 0.8 mm section is the same under reflection.
            self.assertAlmostEqual(end['terminal_geometry']['interior_median_area_mm2'],1.28)
            self.assertAlmostEqual(end['terminal_geometry']['outer_to_interior_area_ratio'],1.)
            self.assertEqual(end['selection_reason'],'THIN_TERMINAL_ROOT')
        self.assertEqual(high['terminal_geometry'],low['terminal_geometry'])

    def test_short_both_end_metadata_translates_with_world_origin(self):
        solid=np.zeros((12,25,35),bool);solid[4:6,5:20,4:25]=True
        first=screen_solid(solid,[0,0,0],.4)['candidates'][0]
        shifted=screen_solid(solid,[100,200,300],.4)['candidates'][0]
        for a,b in zip(first['terminal_end_positions_mm'],shifted['terminal_end_positions_mm']):
            self.assertTrue(np.allclose(np.asarray(b)-a,[100,200,300]))


if __name__=='__main__':unittest.main()
