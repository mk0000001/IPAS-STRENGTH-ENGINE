"""Exact Cura role aliases preserve model process accounting."""
import unittest
import test_local_process as fixtures


class CuraFeatureRoleTests(unittest.TestCase):
    def test_exact_primary_feature_aliases_keep_distinct_process_roles(self):
        for feature,role in (('WALL-OUTER','OUTER_WALL'),('WALL-INNER','INNER_WALL'),('FILL','INFILL'),('SKIN','SOLID')):
            with self.subTest(feature=feature):
                result=fixtures.LocalProcessTests().collect(feature=feature)['a']
                self.assertEqual(set(result['roles']),{role})
                self.assertAlmostEqual(result['roles'][role]['path_length_mm'],6)
                self.assertFalse(result['is_measured'])
                self.assertIsNone(result['measured_substrate_temperature_c'])

    def test_similar_or_auxiliary_names_are_not_promoted_to_primary_role_aliases(self):
        for feature in ('WALL-OUTER custom','support wall-outer','SUPPORT-INTERFACE','PRIME-TOWER','SKINNY'):
            with self.subTest(feature=feature):
                result=fixtures.LocalProcessTests().collect(feature=feature)['a']
                self.assertEqual(set(result['roles']),{'OTHER_MODEL'})


if __name__ == '__main__': unittest.main()
