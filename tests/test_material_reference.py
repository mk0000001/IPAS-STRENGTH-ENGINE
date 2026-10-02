"""Manufacturer MPa stays raw; only the separate load input receives a margin."""
from copy import deepcopy
from decimal import Decimal
import unittest

from print_strength_engine.material_reference import reference_inputs
from print_strength_engine.process import process_adjustment


class MaterialReferenceInputs(unittest.TestCase):
    def test_fusrock_raw_reference_is_not_the_margin_adjusted_capacity_input(self):
        raw={'XY':'33.36','Z':'55'}
        result=reference_inputs(raw,'.85')
        self.assertEqual(result['directional_material_mpa'],{'X':'33.36','Y':'33.36','Z':'55'})
        self.assertEqual(result['directional_capacity_mpa'],{'X':'28.356','Y':'28.356','Z':'46.75'})
        self.assertEqual(result['internal_margin_factor'],'0.85')
        self.assertEqual(result['status'],'READY')
        self.assertEqual(result['margin_basis'],'UNCALIBRATED_LOAD_SCENARIO_MARGIN')

    def test_separate_directional_grade_values_are_preserved(self):
        raw={'X':'45.8','Y':'40.5','Z':'21.2'}
        result=reference_inputs(raw,Decimal('.8'))
        self.assertEqual(result['directional_material_mpa'],raw)
        self.assertEqual(result['directional_capacity_mpa'],{'X':'36.64','Y':'32.4','Z':'16.96'})

    def test_none_or_omitted_margin_keeps_only_raw_material_values(self):
        for call in (lambda:reference_inputs({'XY':'33.36','Z':'55'}),
                     lambda:reference_inputs({'XY':'33.36','Z':'55'},None)):
            with self.subTest(call=call):
                result=call()
                self.assertEqual(result['directional_material_mpa']['X'],'33.36')
                self.assertIsNone(result['directional_capacity_mpa'])
                self.assertIsNone(result['internal_margin_factor'])
                self.assertEqual(result['status'],'MATERIAL_REFERENCE_ONLY')

    def test_invalid_or_partial_material_never_publishes_directional_values(self):
        invalid=(None,True,[],{}, {'XY':'33.36'}, {'Z':'55'}, {'X':'33.36','Z':'55'},
                 {'XY':True,'Z':'55'}, {'XY':'0','Z':'55'}, {'XY':'-1','Z':'55'},
                 {'XY':'NaN','Z':'55'}, {'XY':'Infinity','Z':'55'},
                 {'XY':'33.36','Z':float('nan')}, {'XY':'33.36','Z':float('inf')},
                 {'XY':'33.36','Z':False}, {'XY':'bogus','Z':'55'})
        for raw in invalid:
            with self.subTest(raw=raw):
                result=reference_inputs(raw,'.85')
                self.assertIsNone(result['directional_material_mpa'])
                self.assertIsNone(result['directional_capacity_mpa'])
                self.assertEqual(result['status'],'WITHHELD_INVALID_REFERENCE')

    def test_invalid_margin_never_changes_raw_manufacturer_mpa(self):
        for margin in (False,True,0,-.1,1.01,'NaN','Infinity',float('nan'),float('inf'),'',{},[]):
            with self.subTest(margin=margin):
                result=reference_inputs({'XY':'33.36','Z':'55'},margin)
                self.assertEqual(result['directional_material_mpa'],{'X':'33.36','Y':'33.36','Z':'55'})
                self.assertIsNone(result['directional_capacity_mpa'])
                self.assertIsNone(result['internal_margin_factor'])
                self.assertEqual(result['status'],'WITHHELD_INVALID_MARGIN')

    def test_unit_margin_does_not_introduce_a_material_penalty(self):
        result=reference_inputs({'XY':'33.36','Z':'55'},1)
        self.assertEqual(result['directional_capacity_mpa'],result['directional_material_mpa'])

    def test_repeated_calls_do_not_accumulate_or_mutate_the_margin(self):
        raw={'XY':'33.36','Z':'55','source':{'manufacturer':'FusRock'}}
        saved=deepcopy(raw)
        first=reference_inputs(raw,'.85');second=reference_inputs(raw,'.85')
        self.assertEqual(raw,saved)
        self.assertEqual(first,second)
        self.assertEqual(second['directional_capacity_mpa']['X'],'28.356')
        first['directional_material_mpa']['X']='1'
        self.assertEqual(raw,saved)
        self.assertEqual(second['directional_material_mpa']['X'],'33.36')

    def test_decimal_inputs_keep_precision_beyond_the_default_decimal_context(self):
        value='1.23456789012345678901234567890123456789'
        result=reference_inputs({'XY':value,'Z':'55'},'.85')
        # Independent integer coefficient product establishes all output digits.
        expected='1.0493827066049382706604938270660493827065'
        self.assertEqual(result['directional_material_mpa']['X'],value)
        self.assertEqual(result['directional_capacity_mpa']['X'],expected)

    def test_conflicting_xy_and_explicit_direction_is_withheld(self):
        result=reference_inputs({'XY':'33.36','X':'22','Y':'33.36','Z':'55'},'.85')
        self.assertIsNone(result['directional_material_mpa'])
        self.assertIsNone(result['directional_capacity_mpa'])

    def test_raw_process_reference_is_not_marked_as_margin_adjusted(self):
        raw=reference_inputs({'XY':'33.36','Z':'55'},'.85')['directional_material_mpa']
        result=process_adjustment({'detected_materials':['ABS']},raw,
            reference_context={'internal_conservative_factor':'.85','reference_margin_applied':False})
        self.assertEqual(result['reference_mpa'],{'X':'33.36','Y':'33.36','Z':'55'})
        self.assertEqual(result['reference_strength_kind'],'REFERENCE_ONLY_NOT_MEASURED_TARGET_ALLOWABLE')
        self.assertNotIn('REFERENCE_CONTAINS_UNVALIDATED_INTERNAL_MARGIN',
                         result['calibration']['blocking_reasons'])
        self.assertFalse(result['adjusted'])
        self.assertIsNone(result['effective_mpa'])

    def test_legacy_adjusted_process_reference_retains_its_margin_warning(self):
        old=reference_inputs({'XY':'33.36','Z':'55'},'.85')['directional_capacity_mpa']
        result=process_adjustment({'detected_materials':['ABS']},old,
            reference_context={'internal_conservative_factor':'.85'})
        self.assertEqual(result['reference_mpa'],{'X':'28.356','Y':'28.356','Z':'46.75'})
        self.assertEqual(result['reference_strength_kind'],'MARGIN_ADJUSTED_REFERENCE_NOT_MEASURED_ALLOWABLE')
        self.assertIn('REFERENCE_CONTAINS_UNVALIDATED_INTERNAL_MARGIN',
                      result['calibration']['blocking_reasons'])
        self.assertFalse(result['adjusted'])
        self.assertIsNone(result['effective_mpa'])

    def test_reference_mpa_uses_the_existing_physical_input_upper_bound(self):
        for value in ('100000.0001','1e999999999',Decimal('100001')):
            with self.subTest(value=value):
                result=reference_inputs({'XY':value,'Z':'55'},'.85')
                self.assertIsNone(result['directional_material_mpa'])
                self.assertIsNone(result['directional_capacity_mpa'])
                self.assertEqual(result['status'],'WITHHELD_INVALID_REFERENCE')
        result=reference_inputs({'XY':'100000','Z':'55'},'.85')
        self.assertEqual(Decimal(result['directional_capacity_mpa']['X']),Decimal('85000'))

    def test_decimal_underflow_does_not_publish_a_zero_capacity_reference(self):
        result=reference_inputs({'XY':'1e-1000000000000000000','Z':'55'},'1e-20')
        self.assertIsNotNone(result['directional_material_mpa'])
        self.assertIsNone(result['directional_capacity_mpa'])
        self.assertIsNone(result['internal_margin_factor'])
        self.assertEqual(result['status'],'WITHHELD_CAPACITY_ARITHMETIC')


if __name__=='__main__':unittest.main()
