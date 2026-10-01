import unittest

from print_strength_engine.fusrock import (
    catalog,
    exact_directional_reference,
    match_profiles,
    product_summary,
)


class FusRockOfficialCatalog(unittest.TestCase):
    def test_snapshot_contains_every_comparison_product_and_parameter(self):
        data = catalog()
        self.assertEqual(data['source']['url'], 'https://www.fusrock.com/fusrock/tools/comparison.html')
        self.assertEqual(data['source']['checked_date'], '2026-10-01')
        self.assertEqual(len(data['products']), 46)
        self.assertEqual(len(data['parameters']), 96)
        self.assertGreaterEqual(data['source']['product_pages_linked'], 40)
        self.assertEqual(len({row['id'] for row in data['products']}), 46)
        self.assertEqual(len({row['material_name'] for row in data['products']}), 46)

    def test_profile_match_is_exact_and_rejects_mixed_or_unknown_grades(self):
        self.assertEqual(match_profiles(['FusRock_ABS_0.2 @BBL H2C'])['material_name'], 'ABS')
        self.assertEqual(match_profiles(['FusRock ABS-GF @QIDI Q2'])['material_name'], 'ABS-GF')
        self.assertEqual(match_profiles(['FusRock_PC-ABS_X1C_0.4mm'])['material_name'], 'PC-ABS')
        self.assertIsNone(match_profiles(['FusRock ABS', 'FusRock ASA']))
        self.assertIsNone(match_profiles(['FusRock ABS Plus']))
        self.assertIsNone(match_profiles(['UnknownBrand ABS']))

    def test_abs_directional_reference_uses_comparable_break_metrics_only(self):
        product = match_profiles(['FusRock_ABS_0.2 @BBL H2C'])
        ref = exact_directional_reference(product)
        self.assertEqual(ref['raw_reference_mpa'], {'XY': '33.36', 'Z': '55'})
        self.assertEqual(ref['metric_keys'], {'XY': 'tbs_xy_unannealed', 'Z': 'ts_z_unannealed'})
        self.assertEqual(ref['test_conditions']['nozzle_c'], 250)
        self.assertEqual(ref['test_conditions']['bed_c'], 100)
        self.assertEqual(ref['test_conditions']['speed_mm_s'], 50)
        self.assertEqual(ref['test_conditions']['infill_percent'], 100)
        self.assertNotEqual(ref['raw_reference_mpa']['XY'], str(product['metrics']['tensile_unannealed']))

    def test_summary_exposes_official_print_physical_thermal_and_mechanical_data(self):
        product = match_profiles(['FusRock ABS'])
        summary = product_summary(product)
        self.assertEqual(summary['product'], 'FusRock ABS')
        self.assertEqual(summary['printing']['nozzle_temp_c'], [240, 260])
        self.assertEqual(summary['printing']['bed_temp_c'], [100, 110])
        self.assertEqual(summary['printing']['print_speed_mm_s'], [30, 120])
        self.assertEqual(summary['physical']['density_g_cm3'], 1.05)
        self.assertEqual(summary['thermal']['hdt_a_c'], 86)
        self.assertEqual(summary['mechanical']['tensile_break_xy_mpa'], 33.36)
        self.assertEqual(summary['mechanical']['tensile_break_z_mpa'], 55)
        self.assertTrue(summary['source_url'].endswith('/material/performance/id/106/lang/en'))
        page = product['product_page_recommendations']
        self.assertEqual(page['nozzle_temperature'], '240-260°C')
        self.assertEqual(page['chamber_temp'], 'Sealing or 60-80°C')
        self.assertEqual(page['cooling_fan_speed'], 'Off-30 %')
        self.assertEqual(page['retraction_distance'], '1-5 mm')
        self.assertEqual(page['drying_setting'], '70℃ for 5-6h')
        self.assertEqual(summary['printing']['official_product_page']['chamber_temp'], 'Sealing or 60-80°C')
        self.assertEqual(summary['catalog']['product_count'], 46)
        self.assertEqual(summary['catalog']['parameter_count'], 96)
        self.assertEqual(summary['all_official_facts']['metrics']['physical_density'], 1.05)
        self.assertEqual(summary['all_official_facts']['recommendations']['nozzle_temp_c'], [240, 260])


if __name__ == '__main__':
    unittest.main()
