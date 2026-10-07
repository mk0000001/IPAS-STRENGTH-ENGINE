"""Reference sections cover normal and constricted files without plate-wide forces."""
import math
import unittest
from copy import deepcopy
from unittest.mock import patch

try:
    from print_strength_engine.component_sections import reference_section_candidates
except ImportError:
    reference_section_candidates = None

from print_strength_engine.automatic_sections import StreamingSections, valid_plane_mechanics
from print_strength_engine.capacity import capacity_for_candidate


BOUNDS = [[-2, 32], [-4, 4], [0, 4]]


class ReferenceCandidateTests(unittest.TestCase):
    def candidates(self, heights, volumes=None, explicit=None, max_candidates=6):
        self.assertIsNotNone(reference_section_candidates, 'reference candidate construction is missing')
        manifest = {'layers': [{'id': i + 1, 'z_mm': z, 'model': 1} for i, z in enumerate(heights)]}
        profile = {'layers': [{'layer_number': i + 1, 'z_mm': z,
                              'volume_mm3': (volumes or [10] * len(heights))[i],
                              **({'height_mm': explicit} if explicit is not None else {})}
                             for i, z in enumerate(heights)]}
        return reference_section_candidates(manifest, profile, BOUNDS, max_candidates)

    def test_uniform_model_selects_interior_real_layers_without_thin_or_neck(self):
        rows = self.candidates([.2, .4, .6, .8, 1, 1.2, 1.4])
        self.assertTrue(rows)
        self.assertTrue(all(row['kind'] == 'COMPONENT_REFERENCE_SECTION' for row in rows))
        self.assertTrue(all(1 < row['layer_number'] < 7 for row in rows))
        self.assertAlmostEqual(rows[0]['section_station_mm'], rows[0]['z_mm'] - .1)
        self.assertEqual(rows[0]['section_normal_axis'], 'Z')
        self.assertEqual(rows[0]['region_id'], 'ref-layer-2')

    def test_neck_layer_keeps_screening_identity_but_uses_interior_station(self):
        rows = self.candidates([i * .2 for i in range(1, 42)], [1 if i == 20 else 10 for i in range(41)])
        self.assertEqual(rows[0]['kind'], 'COMPONENT_NECK_SECTION')
        self.assertEqual(rows[0]['layer_number'], 21)
        self.assertEqual(rows[0]['region_id'], 'ref-neck-21')
        self.assertAlmostEqual(rows[0]['section_station_mm'], 4.1)
        self.assertLessEqual(len(rows), 6)

    def test_single_layer_with_explicit_height_is_evaluable(self):
        rows = self.candidates([.3], explicit=.15)
        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(rows[0]['section_station_mm'], .225)
        self.assertEqual(rows[0]['section_window_bounds_mm'][2], [.15, .3])

    def test_single_layer_without_height_retains_explicit_gap_and_no_station(self):
        rows = self.candidates([.3])
        self.assertEqual(len(rows), 1)
        self.assertIsNone(rows[0]['section_station_mm'])
        self.assertIn('REFERENCE_LAYER_HEIGHT_REQUIRED', rows[0]['assessment_gaps'])

    def test_two_layers_infer_height_from_actual_spacing(self):
        rows = self.candidates([.35, .65])
        self.assertEqual(len(rows), 2)
        self.assertAlmostEqual(rows[0]['section_station_mm'], .2)
        self.assertAlmostEqual(rows[1]['section_station_mm'], .5)

    def test_support_only_and_invalid_profile_values_cannot_be_selected(self):
        self.assertIsNotNone(reference_section_candidates)
        manifest = {'layers': [{'id': 1, 'z_mm': .2, 'model': 0}, {'id': 2, 'z_mm': .4, 'model': 1}]}
        profile = {'layers': [{'layer_number': 1, 'z_mm': .2, 'volume_mm3': 1},
                              {'layer_number': 2, 'z_mm': .4, 'volume_mm3': math.inf}]}
        rows = reference_section_candidates(manifest, profile, BOUNDS)
        self.assertEqual([row['layer_number'] for row in rows], [2])
        self.assertIn('REFERENCE_LAYER_HEIGHT_REQUIRED', rows[0]['assessment_gaps'])
        self.assertIsNone(rows[0]['material_area_proxy_mm2'])

    def test_invalid_bounds_and_boolean_model_marker_do_not_create_geometry(self):
        self.assertIsNotNone(reference_section_candidates)
        manifest = {'layers': [{'id': 1, 'z_mm': .2, 'model': 1}]}
        self.assertEqual(reference_section_candidates(manifest, {}, [[0, 1], [0, math.nan], [0, 1]]), [])
        self.assertEqual(reference_section_candidates({'layers': [{'id': 1, 'z_mm': .2, 'model': True}]}, {}, BOUNDS), [])
        self.assertLessEqual(len(self.candidates([i * .2 for i in range(1, 21)], max_candidates=100)), 6)

    def test_explicit_invalid_height_is_not_hidden_by_neighbor_spacing(self):
        rows = self.candidates([.2, .4], explicit=float('nan'))
        self.assertTrue(all(row['section_station_mm'] is None for row in rows))

    def test_unrepresentable_integer_bounds_are_rejected_without_crashing(self):
        self.assertIsNotNone(reference_section_candidates)
        manifest = {'layers': [{'id': 1, 'z_mm': .2, 'model': 1}]}
        self.assertEqual(reference_section_candidates(manifest, {}, [[0, 10**1000], [0, 1], [0, 1]]), [])


def component_candidate(kind='COMPONENT_REFERENCE_SECTION'):
    return {'kind': kind, 'region_id': 'a', 'section_normal_axis': 'Z',
            'section_station_mm': .5, 'axial_section_station_mm': .5,
            'bending_section_station_mm': .5, 'section_window_bounds_mm': [[-2, 32], [-4, 4], [0, 2]]}


def extracted_component(kind='COMPONENT_REFERENCE_SECTION', complete=True):
    point = component_candidate(kind)
    writer = StreamingSections([point])
    writer.segment([-1, 0, 1], [1, 0, 1], 2, 1, 0)  # 2 by 2 square, area 4.
    writer.segment([20, 0, 1], [30, 0, 1], 4, 1, 0)  # Separate 10 by 4 rectangle.
    return point, writer.finish(complete=complete)['a']


class ComponentSectionTests(unittest.TestCase):
    def test_separate_objects_do_not_gain_combined_area_or_parallel_axis_stiffness(self):
        for kind in ('COMPONENT_REFERENCE_SECTION', 'COMPONENT_NECK_SECTION'):
            with self.subTest(kind=kind):
                point, section = extracted_component(kind)
                self.assertEqual(section['status'], 'COMPLETE')
                self.assertAlmostEqual(section['area_mm2'], 4)
                self.assertAlmostEqual(section['minimum_all_direction_section_modulus_mm3'], 4 / (3 * math.sqrt(2)))
                self.assertEqual(section['component_count'], 2)
                self.assertEqual(section['selected_component_bounds_uv_mm'], [[-1, 1], [-1, 1]])
                self.assertEqual(section['axial']['centroid_uv_mm'], section['bending']['centroid_uv_mm'])
                self.assertEqual(section['axial']['component_count'], 1)
                self.assertTrue(valid_plane_mechanics(section['axial'], point['section_window_bounds_mm'][:2]))
                point['deposited_section'] = section
                value = capacity_for_candidate(point, {'X': 20, 'Y': 20, 'Z': 8})
                self.assertIsNotNone(value)
                self.assertEqual(value['calculation_status'], 'AUTOMATIC_REFERENCE_LOAD_ESTIMATE')
                self.assertAlmostEqual(value['axial_capacity_n'], 32)
                self.assertAlmostEqual(value['bending_force_n'], 32 / (75 * math.sqrt(2)))

    def test_existing_local_kind_retains_its_crop_union_behavior(self):
        _, section = extracted_component('LOCAL_THIN_SECTION')
        self.assertAlmostEqual(section['area_mm2'], 44)
        self.assertEqual(section['axial']['component_count'], 2)

    def test_reference_component_requires_same_axial_and_bending_plane(self):
        point = component_candidate();point['bending_section_station_mm'] = 1.5
        writer = StreamingSections([point])
        writer.segment([-1, 0, 1], [1, 0, 1], 2, 1, 0)
        section = writer.finish()['a']
        self.assertEqual(section['status'], 'WITHHELD')
        self.assertIn('COMPONENT_REFERENCE_COMMON_Z_PLANE_REQUIRED', section['assessment_gaps'])

    def test_component_force_rejects_incomplete_source_and_plain_layer_proxy(self):
        point, section = extracted_component(complete=False)
        self.assertEqual(section['status'], 'WITHHELD')
        point['deposited_section'] = section
        self.assertIsNone(capacity_for_candidate(point, {'Z': 8}))
        point, section = extracted_component();point['kind'] = 'LAYER_CONSTRICTION'
        point['material_area_proxy_mm2'] = 44;point['deposited_section'] = section
        value = capacity_for_candidate(point, {'Z': 8})
        self.assertIsNone(value['axial_capacity_n']);self.assertIsNone(value['bending_force_n'])

    def test_relabelled_multiobject_local_union_cannot_gain_component_reference_force(self):
        point, section = extracted_component('LOCAL_THIN_SECTION')
        point['kind'] = 'COMPONENT_REFERENCE_SECTION';point['deposited_section'] = section
        value = capacity_for_candidate(point, {'Z': 8})
        self.assertTrue(value is None or value['axial_capacity_n'] is None)

    def test_malformed_component_selection_proof_withholds_force(self):
        point, original = extracted_component()
        for field, invalid in [('component_count', True), ('component_count', 0),
                               ('component_selection_basis', 'PLATE_UNION'),
                               ('selected_component_bounds_uv_mm', [[-1, 30], [-1, 1]]),
                               ('selected_component_centroid_uv_mm', [20, 0])]:
            with self.subTest(field=field, invalid=invalid):
                section = deepcopy(original);section[field] = invalid
                point['deposited_section'] = section
                value = capacity_for_candidate(point, {'Z': 8})
                self.assertTrue(value is None or value['axial_capacity_n'] is None)

    def test_selected_component_tool_does_not_include_unrelated_object_tool(self):
        point = component_candidate();writer = StreamingSections([point])
        writer.segment([-1, 0, 1], [1, 0, 1], 2, 1, 0)
        writer.segment([20, 0, 1], [30, 0, 1], 4, 1, 1)
        section = writer.finish()['a'];point['deposited_section'] = section
        self.assertEqual(section['tools'], [0])
        self.assertAlmostEqual(capacity_for_candidate(point, {'Z': 8})['axial_capacity_n'], 32)

    def test_volume_scenario_cannot_switch_to_a_different_disconnected_component(self):
        from print_strength_engine.local_process import StreamingLocalProcess, valid_process_descriptor
        for kind in ('COMPONENT_REFERENCE_SECTION', 'COMPONENT_NECK_SECTION'):
            with self.subTest(kind=kind):
                point = component_candidate(kind)
                declared = StreamingSections([point]); process = StreamingLocalProcess([point])
                # The declared weak section is at X=0, but the lower commanded
                # volume would independently select the other part at X=25.
                for start, end, width, volume in (
                        ([-1, 0, 1], [1, 0, 1], 2, 4),
                        ([20, 0, 1], [30, 0, 1], 4, 1)):
                    declared.segment(start, end, width, 1, 0)
                    process.motion(start, end, width, 1, 0, 'outer wall',
                                   {'commanded_volume_mm3': volume})
                section = declared.finish()['a']; local = process.finish()['a']
                volume_section = local.pop('volume_section')
                self.assertEqual(section['selected_component_centroid_uv_mm'], [0, 0])
                self.assertEqual(volume_section['selected_component_centroid_uv_mm'], [25, 0])
                self.assertTrue(valid_process_descriptor(local))
                point.update(deposited_section=section, local_process=local,
                             commanded_volume_section=volume_section)
                value = capacity_for_candidate(point, {'Z': 8})
                self.assertEqual(value['calculation_status'], 'AUTOMATIC_REFERENCE_LOAD_ESTIMATE')
                self.assertAlmostEqual(value['axial_capacity_n'], 32)
                self.assertAlmostEqual(value['bending_force_n'], 32 / (75 * math.sqrt(2)))
                self.assertEqual(value['geometry_scenarios']['selected_geometry'], 'DECLARED_ROADS')
                alternative = value['geometry_scenarios']['commanded_volume']
                self.assertEqual(alternative['status'], 'WITHHELD')
                self.assertIn('COMMANDED_VOLUME_COMPONENT_IDENTITY_UNRESOLVED',
                              alternative['assessment_gaps'])

    def test_reference_and_local_sharing_cut_keep_independent_selection_policies(self):
        reference = component_candidate();local = {**reference, 'kind': 'LOCAL_THIN_SECTION', 'region_id': 'local'}
        writer = StreamingSections([reference, local])
        writer.segment([-1, 0, 1], [1, 0, 1], 2, 1, 0)
        writer.segment([20, 0, 1], [30, 0, 1], 4, 1, 0)
        sections = writer.finish()
        self.assertAlmostEqual(sections['a']['area_mm2'], 4)
        self.assertAlmostEqual(sections['local']['area_mm2'], 44)

    def test_component_budget_withholds_instead_of_dropping_extra_objects(self):
        with patch('print_strength_engine.automatic_sections.MAX_SECTION_COMPONENTS', 1):
            _, section = extracted_component()
        self.assertEqual(section['status'], 'WITHHELD')
        self.assertIsNone(section['area_mm2'])

    def test_reference_gap_is_preserved_by_section_collector(self):
        point = component_candidate();point['section_station_mm'] = point['axial_section_station_mm'] = None
        point['assessment_gaps'] = ['REFERENCE_LAYER_HEIGHT_REQUIRED']
        section = StreamingSections([point]).finish()['a']
        self.assertIn('REFERENCE_LAYER_HEIGHT_REQUIRED', section['assessment_gaps'])


class CommonProductToolTests(unittest.TestCase):
    def connected(self):
        point=component_candidate();point['material_area_proxy_mm2']=4;writer=StreamingSections([point])
        writer.segment([-1,0,1],[0,0,1],2,1,0)
        writer.segment([0,0,1],[1,0,1],2,1,3)
        point['deposited_section']=writer.finish()['a']
        return point

    def test_explicit_common_product_assumption_retains_original_tool_geometry(self):
        point=self.connected();before=deepcopy(point)
        value=capacity_for_candidate(point,{'Z':8},homogeneous_reference_tools=[0,3])
        self.assertEqual(value['calculation_status'],'AUTOMATIC_REFERENCE_LOAD_ESTIMATE')
        self.assertAlmostEqual(value['axial_capacity_n'],32)
        self.assertEqual(value['homogeneous_material_assumption']['tool_ids'],[0,3])
        self.assertFalse(value['homogeneous_material_assumption']['verified'])
        self.assertIn('MULTITOOL_COMMON_PRODUCT_HOMOGENEITY_ASSUMED',value['assessment_gaps'])
        self.assertEqual(point,before)

    def test_multi_tool_geometry_remains_blocked_without_matching_explicit_tool_scope(self):
        for tools in (None,[],[0],[0,1],[0,3,3],[False,3],[0,3,4]):
            with self.subTest(tools=tools):
                value=capacity_for_candidate(self.connected(),{'Z':8},homogeneous_reference_tools=tools)
                self.assertIsNone(value['axial_capacity_n'])
                self.assertIn('MULTITOOL_STIFFNESS_UNVERIFIED',value['assessment_gaps'])

    def test_common_product_assumption_never_rescues_incomplete_geometry(self):
        point=self.connected();point['deposited_section']['complete']=False
        value=capacity_for_candidate(point,{'Z':8},homogeneous_reference_tools=[0,3])
        self.assertIsNone(value['axial_capacity_n'])

    def test_common_product_comparison_rejects_malformed_or_inconsistent_proofs(self):
        from print_strength_engine.weakness import _load_key
        point=self.connected()
        point['estimated_capacity']=capacity_for_candidate(point,{'X':8,'Y':8,'Z':8},homogeneous_reference_tools=[0,3])
        reference={'reference_product':'Synthetic common exact product','source_ref':'https://example.invalid/coupon',
            'raw_reference_mpa':{'XY':'8','Z':'8'},'directional_capacity_reference_mpa':{'X':'8','Y':'8','Z':'8'},'stress_area_basis':'UNKNOWN'}
        common={**deepcopy(reference),'basis':'IDENTICAL_EXACT_PRODUCT_COUPON_REFERENCE_PER_TOOL','tool_ids':[0,3],
                'units':'MPa','verified':False,'bending_supported':True}
        point['estimated_capacity']['material_reference_provenance']={**reference,'common_product_tool_reference':common}
        self.assertIsNotNone(_load_key(point))
        for axis in ([1],{'x':1}):
            with self.subTest(axis=axis):
                changed=deepcopy(point);changed['section_normal_axis']=axis;changed['deposited_section']['normal_axis']=axis
                self.assertIsNone(_load_key(changed))
        for target in ('homogeneous_material_assumption','material_reference_provenance','common_product_tool_reference'):
            for invalid in ([1],'invalid',1,True):
                with self.subTest(target=target,invalid=invalid):
                    changed=deepcopy(point);capacity=changed['estimated_capacity']
                    mapping=capacity['material_reference_provenance'] if target=='common_product_tool_reference' else capacity
                    mapping[target]=invalid
                    self.assertIsNone(_load_key(changed))
        for tools in ([[],3],[{},3],[0,0],[False,3],[-1,3],[float('inf'),3]):
            with self.subTest(tools=tools):
                changed=deepcopy(point);changed['deposited_section']['tools']=tools
                self.assertIsNone(_load_key(changed))
        mutations=[('bending_supported',v) for v in (None,[1],{},float('inf'),'False',False)]
        mutations += [('raw_reference_mpa',v) for v in ([1],'8',float('inf'),{'XY':'8','Z':'nan'})]
        mutations += [('directional_capacity_reference_mpa',v) for v in ({'X':'8','Y':'8','Z':'9'},{'X':True,'Y':'8','Z':'8'})]
        mutations += [('reference_product','Another product'),('source_ref','https://example.invalid/other'),('stress_area_basis','NET_MATERIAL')]
        for field,value in mutations:
            with self.subTest(field=field,value=value):
                changed=deepcopy(point)
                changed['estimated_capacity']['material_reference_provenance']['common_product_tool_reference'][field]=value
                self.assertIsNone(_load_key(changed))


if __name__ == '__main__':
    unittest.main()
