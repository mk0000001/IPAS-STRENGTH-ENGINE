"""Independent beam calculations and rejection of unsupported material geometry."""
import math
import struct
import unittest

try:
    from print_strength_engine.load_case import evaluate_load_case,validate_load_case
except ImportError:
    evaluate_load_case=validate_load_case=None
from print_strength_engine.capacity import capacity_for_candidate


def beam(width=10,height=2,hollow=False):
    segments=[]
    for y in range(width):
        for z in range(height):
            if hollow and 0<y<width-1 and 0<z<height-1:continue
            segments.append({'start':[0,y+.5-width/2,z+1],
                'end':[100,y+.5-width/2,z+1],'width_mm':1,'height_mm':1,'tool':0})
    return {'segments':segments,'complete':True,'sampled':False,
            'provenance':'GCODE_WIDTH_HEIGHT_ASSUMPTION'}


def load(height=2,force=2):
    return {'fixed_region_mm':[[-1,10],[-6,6],[-1,height+1]],
            'load_point_mm':[100,0,height/2],'direction':[0,0,-1],'force_n':force}


def stepped_beam():
    """10 x 2 mm to 2 x 2 mm at x=50; overlapping material at the step."""
    geometry=beam()
    for segment in geometry['segments']:
        if abs(segment['start'][1])>.5:segment['end'][0]=50
    return geometry


class LoadCaseTests(unittest.TestCase):
    def evaluate(self,case=None,geometry=None,**kwargs):
        self.assertIsNotNone(evaluate_load_case,'explicit load-case engine is missing')
        return evaluate_load_case(case or load(),geometry or beam(),{'X':27,'Y':27,'Z':9},**kwargs)

    def test_rectangular_cantilever_uses_net_section_moment_units(self):
        result=self.evaluate(reference_area_basis='NET_MATERIAL')
        self.assertEqual(result['status'],'CONDITIONAL_NORMAL_STRESS')
        self.assertAlmostEqual(result['section']['area_mm2'],20)
        self.assertAlmostEqual(result['section']['coordinate_second_moment_mm4'][1][1],20/3)
        self.assertAlmostEqual(result['normal_stress_per_n_mpa'],13.5)
        self.assertAlmostEqual(result['normal_stress_mpa'],27)
        self.assertAlmostEqual(result['reference_comparison']['load_at_tensile_reference_n'],2)
        self.assertFalse(result['is_failure_prediction'])
        self.assertIsNone(result['failure_load_n'])

    def test_axial_force_is_n_over_deposited_area(self):
        case=load(force=100);case['direction']=[1,0,0]
        value=self.evaluate(case)
        self.assertAlmostEqual(value['normal_stress_mpa'],5)

    def test_eccentric_axial_and_transverse_force_check_both_beam_ends(self):
        case=load(force=1);case['load_point_mm'][2]=2
        case['direction']=[90,0,1]
        result=self.evaluate(case)
        # At the fixture, bending from the eccentric axial force cancels the
        # transverse moment. At the free end its moment remains F_x * 1 mm.
        expected=(.05+.15)*90/math.sqrt(90**2+1)
        self.assertAlmostEqual(result['normal_stress_per_n_mpa'],expected)
        self.assertAlmostEqual(result['critical_section']['station_mm'],100)

    def test_float32_layer_coordinates_do_not_introduce_false_microgaps(self):
        f32=lambda value:struct.unpack('<f',struct.pack('<f',value))[0]
        geometry=beam(2,1)
        geometry['segments']=[{'start':[0,y,f32(z)],'end':[100,y,f32(z)],
                              'width_mm':1,'height_mm':f32(.2),'tool':0}
                             for y in (-.5,.5) for z in (.2,.4,.6)]
        case=load(height=.6,force=1)
        result=self.evaluate(case,geometry)
        self.assertEqual(result['status'],'CONDITIONAL_NORMAL_STRESS')
        self.assertAlmostEqual(result['section']['area_mm2'],1.2,places=6)

    def test_real_gap_larger_than_numerical_tolerance_is_not_filled(self):
        geometry=beam(2,2)
        for segment in geometry['segments']:
            if segment['start'][2]==2:
                segment['start'][2]+=.000001;segment['end'][2]+=.000001
        self.assertIn('DISCONNECTED_SECTION',self.evaluate(geometry=geometry)['assessment_gaps'])

    def test_sparse_shell_uses_hole_in_area_and_inertia(self):
        case=load(height=10,force=1)
        case['load_point_mm'][2]=9.5  # A real point on the shell, not its central void.
        value=self.evaluate(case,beam(10,10,hollow=True))
        self.assertAlmostEqual(value['section']['area_mm2'],36)
        self.assertAlmostEqual(value['section']['coordinate_second_moment_mm4'][1][1],492)
        self.assertAlmostEqual(value['normal_stress_mpa'],450/492)
        self.assertGreater(value['normal_stress_mpa'],self.evaluate(case,beam(10,10))['normal_stress_mpa'])

    def test_point_load_cannot_be_attached_to_empty_infill(self):
        result=self.evaluate(load(height=10,force=1),beam(10,10,hollow=True))
        self.assertIn('LOAD_POINT_NOT_ON_DEPOSITED_SECTION',result['assessment_gaps'])

    def test_product_of_inertia_is_used_for_unsymmetric_section(self):
        geometry=beam(2,2)
        geometry['segments']=[s for s in geometry['segments'] if not(s['start'][1]>.1 and s['start'][2]==2)]
        for segment in geometry['segments']:
            segment['start'][1]+=1;segment['end'][1]+=1
        case=load(force=1);case['load_point_mm']=[100,5/6,5/6]
        result=self.evaluate(case,geometry)
        self.assertAlmostEqual(result['section']['area_mm2'],3)
        tensor=result['section']['coordinate_second_moment_mm4']
        self.assertAlmostEqual(tensor[0][0],11/12)
        self.assertAlmostEqual(tensor[0][1],-1/3)
        self.assertAlmostEqual(result['normal_stress_per_n_mpa'],972/7)

    def test_duplicate_overlapping_roads_do_not_double_section_area(self):
        geometry=beam();geometry['segments']*=2
        result=self.evaluate(geometry=geometry)
        self.assertAlmostEqual(result['section']['area_mm2'],20)
        self.assertAlmostEqual(result['normal_stress_mpa'],27)

    def test_lazy_broken_input_is_withheld(self):
        def broken():
            yield beam()['segments'][0]
            raise OSError('sidecar truncated')
        geometry=beam();geometry['segments']=broken()
        self.assertIn('INVALID_DEPOSITION_RECORD',self.evaluate(geometry=geometry)['assessment_gaps'])

    def test_isolated_material_inside_fixture_is_not_connected_to_beam(self):
        geometry=beam()
        for segment in geometry['segments']:segment['start'][0]=10
        geometry['segments'].append({'start':[0,0,1],'end':[5,0,1],
                                     'width_mm':1,'height_mm':1,'tool':0})
        self.assertEqual(self.evaluate(geometry=geometry)['status'],'WITHHELD')

    def test_declared_count_prevents_silently_truncated_iterator(self):
        geometry=beam();geometry['count']=len(geometry['segments'])+1
        self.assertIn('DEPOSITION_RECORD_COUNT_MISMATCH',self.evaluate(geometry=geometry)['assessment_gaps'])

    def test_subnormal_road_dimensions_do_not_crash_arithmetic(self):
        geometry=beam();geometry['segments'][0]['height_mm']=1e-250
        self.assertEqual(self.evaluate(geometry=geometry)['status'],'WITHHELD')

    def test_rotation_and_direction_scaling_preserve_response(self):
        geometry=beam();case=load()
        for segment in geometry['segments']:
            for key in ('start','end'):
                x,y,z=segment[key];segment[key]=[-y,x,z]
        case['fixed_region_mm']=[[-6,6],[-1,10],[-1,3]]
        case['load_point_mm']=[0,100,1];case['direction']=[0,0,-8]
        result=self.evaluate(case,geometry)
        self.assertAlmostEqual(result['normal_stress_mpa'],27)
        self.assertEqual(result['beam_axis'],'Y')

    def test_translation_does_not_change_second_moment(self):
        geometry=beam();case=load();delta=[20000,-30000,40000]
        for segment in geometry['segments']:
            for key in ('start','end'):segment[key]=[a+b for a,b in zip(segment[key],delta)]
        case['load_point_mm']=[a+b for a,b in zip(case['load_point_mm'],delta)]
        case['fixed_region_mm']=[[a+d,b+d] for (a,b),d in zip(case['fixed_region_mm'],delta)]
        self.assertAlmostEqual(self.evaluate(case,geometry)['normal_stress_mpa'],27)

    def test_disconnected_roads_cannot_be_aggregated_as_one_section(self):
        geometry=beam();geometry['segments']=[s for s in geometry['segments'] if abs(s['start'][1])>1]
        self.assertEqual(self.evaluate(geometry=geometry)['status'],'WITHHELD')
        self.assertIn('DISCONNECTED_SECTION',self.evaluate(geometry=geometry)['assessment_gaps'])

    def test_missing_dimensions_and_sampled_cache_withhold(self):
        for key in ('width_mm','height_mm'):
            geometry=beam();del geometry['segments'][0][key]
            self.assertEqual(self.evaluate(geometry=geometry)['status'],'WITHHELD')
        geometry=beam();geometry['sampled']=True
        self.assertIn('COMPLETE_DEPOSITION_GEOMETRY_REQUIRED',self.evaluate(geometry=geometry)['assessment_gaps'])

    def test_unknown_force_reports_unit_load_only(self):
        value=self.evaluate(load(force=None))
        self.assertIsNone(value['normal_stress_mpa'])
        self.assertAlmostEqual(value['normal_stress_per_n_mpa'],13.5)

    def test_nominal_coupon_stress_is_not_net_deposited_stress(self):
        for basis in ('GROSS_ENVELOPE','UNKNOWN','INTERLAYER_CONTACT'):
            result=self.evaluate(reference_area_basis=basis)
            self.assertIsNone(result['reference_comparison']['load_at_tensile_reference_n'])
            self.assertEqual(result['reference_comparison']['status'],'INCOMPATIBLE_STRESS_AREA_BASIS')

    def test_partial_fixture_and_torsion_are_not_supported(self):
        case=load();case['fixed_region_mm'][1]=[-1,1]
        self.assertIn('FULL_SECTION_FIXTURE_REQUIRED',self.evaluate(case)['assessment_gaps'])
        case=load();case['load_point_mm'][1]=1
        self.assertIn('TORSION_NOT_SUPPORTED',self.evaluate(case)['assessment_gaps'])

    def test_stepped_section_checks_both_sides_of_every_boundary(self):
        result=self.evaluate(load(force=1),stepped_beam())
        self.assertEqual(result['status'],'CONDITIONAL_NORMAL_STRESS')
        # Wide fixture section: 90/(10*2**3/12)=13.5 MPa/N.
        # Narrow side of x=50: 50/(2*2**3/12)=37.5 MPa/N.
        self.assertAlmostEqual(result['normal_stress_per_n_mpa'],37.5)
        self.assertAlmostEqual(result['critical_section']['station_mm'],50)
        self.assertAlmostEqual(result['section']['area_mm2'],4)
        self.assertEqual(result['section']['section_geometry_status'],'CONNECTED_PIECEWISE_PRISMATIC_ROAD_ENVELOPE')
        self.assertEqual(len(result['section_profile']),2)
        self.assertFalse(result['is_failure_prediction'])
        self.assertIsNone(result['failure_load_n'])

    def test_stepped_axial_stress_uses_each_local_area(self):
        case=load(force=100);case['direction']=[1,0,0]
        result=self.evaluate(case,stepped_beam())
        self.assertEqual(result['status'],'CONDITIONAL_NORMAL_STRESS')
        self.assertAlmostEqual(result['normal_stress_mpa'],25)

    def test_reverse_stepped_cantilever_preserves_critical_response(self):
        geometry=stepped_beam()
        for segment in geometry['segments']:
            for key in ('start','end'):segment[key][0]=100-segment[key][0]
        case=load(force=1);case['fixed_region_mm'][0]=[90,101];case['load_point_mm'][0]=0
        result=self.evaluate(case,geometry)
        self.assertEqual(result['status'],'CONDITIONAL_NORMAL_STRESS')
        self.assertAlmostEqual(result['normal_stress_per_n_mpa'],37.5)
        self.assertAlmostEqual(result['critical_section']['station_mm'],50)

    def test_neighboring_intervals_need_positive_area_contact(self):
        geometry=beam(2,2)
        for segment in geometry['segments']:segment['end'][0]=50
        for segment in beam(2,2)['segments']:
            segment['start'][0]=50
            segment['start'][1]+=2;segment['end'][1]+=2
            geometry['segments'].append(segment)
        case=load(force=1);case['load_point_mm'][1]=2
        result=self.evaluate(case,geometry)
        self.assertEqual(result['status'],'WITHHELD')
        self.assertIn('DISCONNECTED_BEAM_INTERVALS',result['assessment_gaps'])

    def test_varying_section_with_unsolved_torsion_is_withheld(self):
        geometry=beam();geometry['segments'][0]['end'][0]=50
        self.assertIn('TORSION_NOT_SUPPORTED',self.evaluate(geometry=geometry)['assessment_gaps'])

    def test_invalid_nonfinite_load_is_rejected_before_geometry(self):
        self.assertIsNotNone(validate_load_case)
        for field,value in (('force_n',math.nan),('force_n',-1),('direction',[0,0,0]),
                            ('load_point_mm',[0,0,math.inf]),('fixed_region_mm',[[2,1],[0,1],[0,1]])):
            case=load();case[field]=value
            with self.subTest(field=field,value=value),self.assertRaises(ValueError):validate_load_case(case)

    def test_full_infill_metadata_cannot_turn_envelope_into_capacity(self):
        candidate={'min_section_area_mm2':20,'section_modulus_mm3':20/3,'section_normal_axis':'X'}
        result=capacity_for_candidate(candidate,{'X':27},{'configuration':{'sparse_infill_density':100}},90)
        self.assertIsNone(result['axial_capacity_n'])
        self.assertIsNone(result['bending_force_n'])
        self.assertFalse(result['assumes_solid_section'])


if __name__=='__main__':unittest.main()
