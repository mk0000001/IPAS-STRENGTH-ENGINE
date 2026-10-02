import unittest
from print_strength_engine.evidence import literature_comparisons
from print_strength_engine.process import process_adjustment,settings


class ProcessInteractionTests(unittest.TestCase):
    def test_temperature_effect_changes_sign_and_is_never_a_factor(self):
        rows=[r for r in literature_comparisons({'material_family':'PAHT-CF','nozzle_c':280}) if r['doi']=='10.3390/polym14071292']
        self.assertEqual(len(rows),2)
        self.assertLess(rows[0]['observed_ratio'],1)
        self.assertGreater(rows[1]['observed_ratio'],1)
        self.assertTrue(all(r['transfer_factor'] is None and not r['applied'] for r in rows))

    def test_open_specimens_preserve_n_sd_and_unknown_area(self):
        row=next(r for r in literature_comparisons({'material_family':'PA6-CF'}) if r['source_id']=='P20261003_NESHEIM_40')
        self.assertEqual(sorted(o['n'] for o in row['observations']),[5,6,6])
        self.assertIsNone(row['source_context']['stress_area_basis'])
        self.assertFalse(row['runtime_calibration_eligible'])

    def test_new_observations_never_change_manufacturer_reference(self):
        result=process_adjustment({'configuration':{'filament_type':'ABS','filament_flow_ratio':'1.5'}},{'X':33.36,'Y':33.36,'Z':55})
        self.assertEqual(result['reference_mpa']['X'],'33.36')
        self.assertIsNone(result['effective_mpa'])
        self.assertFalse(result['adjusted'])

    def test_commanded_and_configured_temperature_never_overwrite_each_other(self):
        result=settings({'configuration':{'nozzle_temperature':240},'process_metrics':{'deposition_nozzle_setpoint_c':{'min':280,'max':280,'last':None}}})
        self.assertEqual(result['nozzle_c'],240)
        self.assertEqual(result['nozzle_command_range_c']['max'],280)
        self.assertIsNone(result['measured_substrate_temperature_c'])
