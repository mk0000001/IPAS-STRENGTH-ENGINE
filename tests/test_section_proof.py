"""Reject inconsistent cached mechanics without inventing material corrections."""
from copy import deepcopy
import json
import math
import unittest

import test_automatic_sections as sections_fixture
from test_automatic_sections import candidate
from print_strength_engine.capacity import _automatic_details_valid, capacity_for_candidate


class SectionProofTests(unittest.TestCase):
    def section(self):
        return json.loads(json.dumps(sections_fixture.AutomaticSectionTests().extract()))

    def test_inconsistent_finite_moduli_cannot_raise_reference_force(self):
        source = self.section()
        point = candidate()
        point['deposited_section'] = deepcopy(source)
        baseline = capacity_for_candidate(point, {'X': 20})
        self.assertIsNotNone(baseline['bending_force_n'])
        for nested in ('axial', 'bending'):
            source[nested]['principal_section_moduli_mm3'] = [v * 1.5 for v in source[nested]['principal_section_moduli_mm3']]
            source[nested]['minimum_all_direction_section_modulus_mm3'] *= 1.5
        source['min_principal_section_modulus_mm3'] *= 1.5
        source['minimum_all_direction_section_modulus_mm3'] *= 1.5
        self.assertFalse(_automatic_details_valid(source, 'X', point))
        point['deposited_section'] = source
        self.assertIsNone(capacity_for_candidate(point, {'X': 20})['bending_force_n'])

    def test_fresh_section_retains_bounded_geometry_support_proof(self):
        source = self.section()
        for key in ('axial', 'bending'):
            support = source[key].get('boundary_support_vertices_relative_uv_mm')
            self.assertIsInstance(support, list)
            self.assertEqual(len(support), 4)
            self.assertTrue(all(len(v) == 2 and all(math.isfinite(x) for x in v) for v in support))
        self.assertTrue(_automatic_details_valid(source, 'X', candidate()))

    def test_missing_or_incomplete_support_never_supplies_force(self):
        for damage in ('missing', 'empty', 'nan', 'bool', 'interior_only'):
            source = self.section()
            for key in ('axial', 'bending'):
                support = source[key].get('boundary_support_vertices_relative_uv_mm') or [[-5, -1], [5, -1], [5, 1], [-5, 1]]
                if damage == 'missing':
                    source[key].pop('boundary_support_vertices_relative_uv_mm', None)
                elif damage == 'empty':
                    source[key]['boundary_support_vertices_relative_uv_mm'] = []
                elif damage == 'interior_only':
                    source[key]['boundary_support_vertices_relative_uv_mm'] = [[x / 2, y / 2] for x, y in support]
                else:
                    support[0][0] = float('nan') if damage == 'nan' else True
                    source[key]['boundary_support_vertices_relative_uv_mm'] = support
            with self.subTest(damage=damage):
                self.assertFalse(_automatic_details_valid(source, 'X', candidate()))

    def test_top_direction_cannot_disagree_with_checked_bending_geometry(self):
        source = self.section()
        source['weakest_local_bending_stress_gradient_xyz'] = [0, 1, 0]
        self.assertFalse(_automatic_details_valid(source, 'X', candidate()))

    def test_rotated_and_hollow_sections_keep_their_actual_support(self):
        from test_load_case import beam
        from print_strength_engine.automatic_sections import valid_plane_mechanics
        for geometry, point in ((beam(10, 10, hollow=True), candidate()),
                ({'segments': [{'start': [0, 0, 1], 'end': [10, 10, 1], 'width_mm': 2, 'height_mm': 1, 'tool': 0}]},
                 candidate('Z', .5, [[-5, 15], [-5, 15], [-1, 2]]))):
            source = sections_fixture.AutomaticSectionTests().extract(geometry, point)
            plane = [("XYZ".index(point['section_normal_axis']) + n) % 3 for n in (1, 2)]
            bounds = [point['section_window_bounds_mm'][n] for n in plane]
            for key in ('axial', 'bending'):
                self.assertTrue(valid_plane_mechanics(source[key], bounds))
            self.assertTrue(_automatic_details_valid(source, point['section_normal_axis'], point))

    def test_proof_tolerances_do_not_accept_inflation_at_small_scales(self):
        from shapely.geometry import box
        from print_strength_engine.automatic_sections import _plane_properties, valid_plane_mechanics
        for scale in (1e-3, 1, 1e3):
            bounds = [[0, scale], [0, scale]]
            source = _plane_properties(box(0, 0, scale, scale))
            with self.subTest(scale=scale):
                self.assertTrue(valid_plane_mechanics(source, bounds))
                source['principal_section_moduli_mm3'] = [v * 1.5 for v in source['principal_section_moduli_mm3']]
                source['minimum_all_direction_section_modulus_mm3'] *= 1.5
                self.assertFalse(valid_plane_mechanics(source, bounds))

    def test_small_section_top_level_modulus_must_match_geometry(self):
        from test_load_case import beam
        geometry = beam()
        scale = .001
        for road in geometry['segments']:
            for key in ('start', 'end'):
                road[key] = [v * scale for v in road[key]]
            for key in ('width_mm', 'height_mm'):
                road[key] *= scale
        point = candidate(station=.05, bounds=[[.04, .06], [-.006, .006], [-.001, .011]])
        source = sections_fixture.AutomaticSectionTests().extract(geometry, point)
        self.assertTrue(_automatic_details_valid(source, 'X', point))
        point['deposited_section'] = deepcopy(source)
        self.assertIsNotNone(capacity_for_candidate(point, {'X': 20})['bending_force_n'])
        source['minimum_all_direction_section_modulus_mm3'] *= 1.5
        self.assertFalse(_automatic_details_valid(source, 'X', point))


if __name__ == '__main__':
    unittest.main()
