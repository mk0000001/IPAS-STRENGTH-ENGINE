"""Unvalidated material-reference load comparisons require streamed net sections."""
import unittest
import math
from copy import deepcopy
from print_strength_engine.capacity import capacity_for_candidate
import test_automatic_sections as section_tests


class AutomaticCapacityTests(unittest.TestCase):
    def estimate(self,basis='UNKNOWN',section=None):
        point=section_tests.candidate();point['deposited_section']=section or section_tests.AutomaticSectionTests().extract()
        return capacity_for_candidate(point,{'X':20,'Y':30,'Z':8},
            {'configuration':{'sparse_infill_density':20}},reference_area_basis=basis)

    def test_no_applied_force_needed_for_reference_loads(self):
        result=self.estimate()
        self.assertEqual(result['calculation_status'],'AUTOMATIC_REFERENCE_LOAD_ESTIMATE')
        self.assertAlmostEqual(result['axial_capacity_n'],400)
        orientation=math.sqrt(1.04)
        self.assertAlmostEqual(result['bending_capacity_nmm'],400/3/orientation)
        self.assertAlmostEqual(result['bending_force_n'],16/3/orientation)
        self.assertEqual(result['bending_lever_mm'],25)
        self.assertEqual([item['lever_mm'] for item in result['bending_scenarios']],[10,25,50])
        self.assertAlmostEqual(result['bending_scenarios'][0]['force_n'],40/3/orientation)
        self.assertAlmostEqual(result['bending_scenarios'][2]['force_n'],8/3/orientation)
        self.assertFalse(result['is_failure_prediction']);self.assertFalse(result['empirically_validated'])
        self.assertIsNone(result['allowable_mpa'])

    def test_reference_area_basis_is_preserved_as_an_unverified_assumption(self):
        for basis in ('UNKNOWN','GROSS_ENVELOPE','NET_MATERIAL'):
            result=self.estimate(basis)
            self.assertEqual(result['reference_stress_area_basis'],basis)
            self.assertAlmostEqual(result['axial_capacity_n'],400)
            self.assertFalse(result['reference_transfer_assumption']['verified'])
            self.assertEqual(result['reference_transfer_assumption']['target_area_basis'],'DECLARED_NET_ROAD_ENVELOPE')

    def test_incomplete_section_cannot_use_outer_area_or_full_infill_metadata(self):
        point=section_tests.candidate();point['deposited_section']={'status':'WITHHELD','area_mm2':20}
        result=capacity_for_candidate(point,{'X':20},{'configuration':{'sparse_infill_density':100}})
        self.assertIsNone(result['axial_capacity_n']);self.assertIsNone(result['bending_force_n'])

    def test_multitool_section_does_not_assume_material_bond_stiffness(self):
        section=section_tests.AutomaticSectionTests().extract();section['tools']=[0,1]
        result=self.estimate(section=section)
        self.assertIsNone(result['axial_capacity_n']);self.assertIsNone(result['bending_force_n'])
        self.assertIn('MULTITOOL_STIFFNESS_UNVERIFIED',result['assessment_gaps'])

    def test_verified_local_roads_need_no_outer_envelope_area(self):
        point=section_tests.candidate();point['deposited_section']=section_tests.AutomaticSectionTests().extract()
        del point['min_section_area_mm2'];del point['section_modulus_mm3']
        result=capacity_for_candidate(point,{'X':20})
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result['axial_capacity_n'],400)

    def test_layer_proxy_does_not_gain_force_from_a_deposited_section_field(self):
        point=section_tests.candidate();point['kind']='LAYER_CONSTRICTION'
        point['deposited_section']=section_tests.AutomaticSectionTests().extract()
        result=capacity_for_candidate(point,{'X':20})
        self.assertIsNone(result['axial_capacity_n'])

    def test_boolean_material_reference_is_not_a_number(self):
        point=section_tests.candidate();point['deposited_section']=section_tests.AutomaticSectionTests().extract()
        self.assertIsNone(capacity_for_candidate(point,{'X':True}))

    def test_missing_required_complete_section_details_withhold_instead_of_crashing(self):
        original=section_tests.AutomaticSectionTests().extract()
        for missing in ('bending','principal_section_moduli_mm3','weakest_local_bending_stress_gradient_xyz'):
            with self.subTest(missing=missing):
                damaged=deepcopy(original)
                if missing=='principal_section_moduli_mm3':del damaged['bending'][missing]
                else:del damaged[missing]
                try:result=self.estimate(section=damaged)
                except (KeyError,TypeError) as error:self.fail(f'Malformed section raised {error!r}')
                self.assertIsNone(result['axial_capacity_n']);self.assertIsNone(result['bending_force_n'])

    def test_malformed_principal_moduli_withhold_reference_loads(self):
        original=section_tests.AutomaticSectionTests().extract()
        for value in (None,[],[1],[1,float('inf')],[True,1],[1,-1],'1,2'):
            with self.subTest(value=value):
                damaged=deepcopy(original);damaged['bending']['principal_section_moduli_mm3']=value
                result=self.estimate(section=damaged)
                self.assertIsNone(result['axial_capacity_n']);self.assertIsNone(result['bending_force_n'])

    def test_malformed_stress_direction_withholds_reference_loads(self):
        original=section_tests.AutomaticSectionTests().extract()
        for value in (None,[],[0,1],[0,float('nan'),1],[True,0,1],[0,0,0],[0,2,0],[1,0,0],'0,1,0'):
            with self.subTest(value=value):
                damaged=deepcopy(original);damaged['weakest_local_bending_stress_gradient_xyz']=value
                result=self.estimate(section=damaged)
                self.assertIsNone(result['axial_capacity_n']);self.assertIsNone(result['bending_force_n'])

    def test_old_or_missing_deposited_section_version_withholds_loads(self):
        original=section_tests.AutomaticSectionTests().extract()
        for version in ('OLD',None):
            with self.subTest(version=version):
                damaged=deepcopy(original)
                if version is None:del damaged['version']
                else:damaged['version']=version
                result=self.estimate(section=damaged)
                self.assertIsNone(result['axial_capacity_n']);self.assertIsNone(result['bending_force_n'])


if __name__=='__main__':unittest.main()
