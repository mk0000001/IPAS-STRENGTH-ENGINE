import unittest

from print_strength_engine.capacity import capacity_for_candidate


class CapacityPatterns(unittest.TestCase):
    def capacity(self, pattern):
        return capacity_for_candidate(
            {'min_section_area_mm2': 100., 'thickness_proxy_mm': 10.,
             'section_normal_axis': 'Z'},
            {'Z': 10.},
            {'configuration': {'sparse_infill_density': '25%',
                               'sparse_infill_pattern': pattern,
                               'wall_loops': 2, 'nozzle_diameter': .4}},
        )

    def test_slicer_spellings_produce_the_same_capacity(self):
        for canonical, aliases in (
            ('zigzag', ('zig-zag', 'Zig Zag', 'zig_zag')),
            ('adaptive', ('adaptivecubic', 'adaptive-cubic', 'Adaptive Cubic')),
            ('tri-hexagon', ('trihexagon', 'tri_hexagon', 'Tri Hexagon')),
            ('line', ('lines',)),
        ):
            for alias in aliases:
                with self.subTest(pattern=alias):
                    self.assertIsNone(self.capacity(alias)['axial_capacity_n'])
                    self.assertIsNone(self.capacity(canonical)['axial_capacity_n'])

    def test_unknown_patterns_do_not_receive_an_invented_fallback(self):
        for pattern in ('tpmsd', 'crosshatch', 'future-grid-pattern', None):
            with self.subTest(pattern=pattern):
                value = self.capacity(pattern)
                self.assertEqual(value['section_knockdown_reasons'],[])
                self.assertIsNone(value['section_knockdown'])
                self.assertIsNone(value['axial_capacity_n'])

    def test_known_pattern_name_is_metadata_not_a_strength_coefficient(self):
        result=self.capacity('adaptivecubic')
        self.assertEqual(result['structure_settings']['pattern'],'adaptivecubic')
        self.assertEqual(result['section_knockdown_reasons'],[])
        self.assertIsNone(result['axial_capacity_n'])

    def test_aligned_rectilinear_does_not_inherit_unvalidated_family_strength(self):
        for pattern in ('alignedrectilinear', 'aligned rectilinear', 'aligned-rectilinear'):
            with self.subTest(pattern=pattern):
                result = self.capacity(pattern)
                self.assertIsNone(result['axial_capacity_n'])
                self.assertEqual(result['section_knockdown_reasons'],[])


if __name__ == '__main__':
    unittest.main()
