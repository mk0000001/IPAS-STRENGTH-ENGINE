"""Geometry invariants and preservation of uncertain process inputs."""
import unittest

from print_strength_engine.load_case import evaluate_load_case
from print_strength_engine.process import settings


def beam():
    return {'complete': True, 'sampled': False,
            'provenance': 'GCODE_WIDTH_HEIGHT_ASSUMPTION',
            'segments': [{'start': [0, y, 1], 'end': [100, y, 1],
                          'width_mm': 1, 'height_mm': 1, 'tool': 0}
                         for y in (-.5, .5)]}


def load():
    return {'fixed_region_mm': [[-1, 10], [-2, 2], [-1, 2]],
            'load_point_mm': [100, 0, .5], 'direction': [0, 0, -1],
            'force_n': 1}


class CorePhysicsAuditTests(unittest.TestCase):
    def test_fixture_extent_outside_material_cannot_change_beam_axis(self):
        # Both fixtures clamp exactly x=0..10 of the same 2x1 mm beam.
        # M=90 Nmm, I=2/12 mm4, c=.5 mm gives 270 MPa per N.
        for transverse_fixture in ((-2, 2), (-2000, 2), (-2, 2000)):
            case = load()
            case['fixed_region_mm'][1] = list(transverse_fixture)
            result = evaluate_load_case(case, beam())
            with self.subTest(fixture=transverse_fixture):
                self.assertEqual(result['status'], 'CONDITIONAL_NORMAL_STRESS')
                self.assertEqual(result['beam_axis'], 'X')
                self.assertAlmostEqual(result['normal_stress_per_n_mpa'], 270)
                self.assertIsNone(result['failure_load_n'])

    def test_mixed_process_slots_do_not_become_first_tool_scalars(self):
        for slots in ((.4, .8), (.4, 'unknown')):
            read = settings({'configuration': {
                'nozzle_diameter': list(slots), 'outer_wall_line_width': list(slots),
                'sparse_infill_density': [100, 20]}})
            with self.subTest(slots=slots):
                self.assertIsNone(read['nozzle_diameter_mm'])
                self.assertIsNone(read['line_width_mm'])
                self.assertIsNone(read['infill_percent'])
                self.assertEqual(read['line_width_source'], 'UNKNOWN')

    def test_uncertain_nozzle_list_cannot_fall_back_to_first_tool_summary(self):
        read = settings({'nozzle_diameter_mm': .4,
                         'configuration': {'nozzle_diameter': [.4, .8]}})
        self.assertIsNone(read['line_width_mm'])
        self.assertEqual(read['line_width_source'], 'UNKNOWN')
        self.assertEqual(read['nozzle_diameters_mm'], [.4, .8])

    def test_uniform_slots_keep_known_value_and_per_tool_provenance(self):
        read = settings({'configuration': {'nozzle_diameter': '.4;.4',
                         'outer_wall_line_width': [.42, .42],
                         'sparse_infill_density': '20%,20%'}})
        self.assertEqual(read['nozzle_diameter_mm'], .4)
        self.assertEqual(read['line_width_mm'], .42)
        self.assertEqual(read['infill_percent'], 20)
        self.assertEqual(read['nozzle_diameters_mm'], [.4, .4])
        self.assertEqual(read['line_widths_mm'], [.42, .42])


if __name__ == '__main__':
    unittest.main()
