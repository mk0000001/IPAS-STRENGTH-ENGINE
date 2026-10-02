import unittest
from print_strength_engine.local_process import StreamingLocalProcess, valid_process_descriptor
from test_automatic_sections import candidate


class LocalProcessTests(unittest.TestCase):
    def context(self, volume=10, **changes):
        return dict(commanded_volume_mm3=volume, commanded_speed_mm_s=20,
                    nozzle_setpoint_c=240, bed_setpoint_c=100, chamber_setpoint_c=60,
                    part_cooling_fan_pwm=128, flow_override_percent=100,
                    assessment_gaps=(), **changes)

    def collect(self, volume=10, feature='inner wall', start=None, end=None, context=None):
        writer=StreamingLocalProcess([candidate(station=5,bounds=[[2,8],[-2,2],[0,2]])])
        writer.motion(start or [0,0,1],end or [10,0,1],1,1,0,feature,context or self.context(volume))
        return writer.finish()

    def test_volume_clipped_by_centerline_not_whole_motion(self):
        result=self.collect()['a']
        role=result['roles']['INNER_WALL']
        self.assertAlmostEqual(role['path_length_mm'],6)
        self.assertAlmostEqual(role['commanded_volume_mm3'],6)
        self.assertEqual(result['individual_wall_passes_resolved'],False)
        self.assertEqual(result['measured_substrate_temperature_c'],None)
        self.assertTrue(valid_process_descriptor(result))

    def test_half_commanded_rectangle_volume_halves_equivalent_section(self):
        result=self.collect(5)['a']
        self.assertEqual(result['volume_section']['status'],'COMPLETE')
        self.assertAlmostEqual(result['volume_section']['area_mm2'],.5)
        self.assertEqual(result['volume_section']['provenance'],'GCODE_COMMANDED_VOLUME_RECTANGULAR_EQUIVALENT')

    def test_overextrusion_does_not_enlarge_declared_section(self):
        result=self.collect(20)['a']
        self.assertAlmostEqual(result['volume_section']['area_mm2'],1)
        self.assertEqual(result['roles']['INNER_WALL']['over_declared_volume_records'],1)

    def test_missing_volume_withholds_added_scenario_only(self):
        result=self.collect(context=self.context(None))['a']
        self.assertEqual(result['volume_section']['status'],'WITHHELD')
        self.assertIn('COMMANDED_VOLUME_REQUIRED',result['volume_section']['assessment_gaps'])
        self.assertEqual(result['roles']['INNER_WALL']['volume_known_length_mm'],0)

    def test_missing_outside_window_does_not_poison_local_scenario(self):
        writer=StreamingLocalProcess([candidate(station=5,bounds=[[2,8],[-2,2],[0,2]])])
        writer.motion([0,100,1],[10,100,1],1,1,0,'inner wall',self.context(None))
        writer.motion([0,0,1],[10,0,1],1,1,0,'outer wall',self.context())
        self.assertEqual(writer.finish()['a']['volume_section']['status'],'COMPLETE')

    def test_unsupported_arc_withholds_volume_not_role_summary(self):
        writer=StreamingLocalProcess([candidate(station=5,bounds=[[2,8],[-2,2],[0,2]])])
        writer.motion([0,0,1],[10,0,1],1,1,0,'outer wall',self.context(),arc=True)
        result=writer.finish()['a']
        self.assertEqual(result['volume_section']['status'],'WITHHELD')
        self.assertIn('ARC_VOLUME_ALLOCATION_UNSUPPORTED',result['assessment_gaps'])

    def test_nonfinite_context_is_unknown_and_not_zero(self):
        result=self.collect(context=self.context(float('nan')))['a']
        self.assertIsNone(result['roles']['INNER_WALL']['commanded_volume_mm3'])
        self.assertEqual(result['volume_section']['status'],'WITHHELD')

    def test_temperature_coverage_not_invented_by_known_record(self):
        writer=StreamingLocalProcess([candidate(station=5,bounds=[[2,8],[-2,2],[0,2]])])
        writer.motion([0,0,1],[10,0,1],1,1,0,'outer wall',self.context())
        ctx=self.context();ctx['nozzle_setpoint_c']=None
        writer.motion([0,.5,1],[10,.5,1],1,1,0,'inner wall',ctx)
        result=writer.finish()['a']
        self.assertAlmostEqual(result['temperature_setpoint_c']['known_length_mm'],6)
        self.assertAlmostEqual(result['path_length_mm'],12)
        self.assertEqual(result['temperature_setpoint_c']['min'],240)

    def test_tampered_and_incomplete_descriptors_are_rejected(self):
        result=self.collect()['a'];result['roles']['INNER_WALL']['volume_known_length_mm']=99
        self.assertFalse(valid_process_descriptor(result))
        writer=StreamingLocalProcess([candidate(station=5,bounds=[[2,8],[-2,2],[0,2]])])
        writer.motion([0,0,1],[10,0,1],1,1,0,'inner wall',self.context())
        self.assertEqual(writer.finish(complete=False)['a']['volume_section']['status'],'WITHHELD')

    def test_off_center_road_footprint_still_enters_cut(self):
        writer=StreamingLocalProcess([candidate(station=5,bounds=[[2,8],[-.1,.1],[0,2]])])
        writer.motion([0,.3,1],[10,.3,1],1,1,0,'inner wall',self.context(10))
        result=writer.finish()['a']
        self.assertAlmostEqual(result['volume_section']['area_mm2'],.2)
        self.assertTrue(valid_process_descriptor(result))

    def prepared_candidate(self, volume=5, tool=0, **context_changes):
        from print_strength_engine.automatic_sections import StreamingSections
        point=candidate(station=5,bounds=[[2,8],[-2,2],[0,2]])
        declared=StreamingSections([point])
        declared.segment([0,0,1],[10,0,1],1,1,tool)
        point['deposited_section']=declared.finish()['a']
        ctx=self.context(volume)
        ctx.update(context_changes)
        writer=StreamingLocalProcess([point])
        writer.motion([0,0,1],[10,0,1],1,1,tool,'inner wall',ctx)
        local=writer.finish()['a']
        point['local_process']=local
        point['commanded_volume_section']=local['volume_section']
        return point

    def test_unknown_volume_stays_unknown_when_other_role_is_known(self):
        writer=StreamingLocalProcess([candidate(station=5,bounds=[[2,8],[-2,2],[0,2]])])
        writer.motion([0,0,1],[10,0,1],1,1,0,'outer wall',self.context(None))
        writer.motion([0,1,1],[10,1,1],1,1,0,'inner wall',self.context(10))
        result=writer.finish()['a']
        self.assertIsNone(result['roles']['OUTER_WALL']['commanded_volume_mm3'])
        self.assertAlmostEqual(result['roles']['INNER_WALL']['commanded_volume_mm3'],6)
        self.assertEqual(result['volume_section']['status'],'WITHHELD')

    def test_unknown_height_cannot_prove_road_outside_crop(self):
        writer=StreamingLocalProcess([candidate(station=5,bounds=[[2,8],[-2,2],[0,2]])])
        writer.motion([0,0,1],[10,0,1],1,1,0,'inner wall',self.context())
        # Its top is outside; an unknown height can still extend into the window.
        writer.motion([0,0,2.1],[10,0,2.1],1,None,0,'outer wall',self.context())
        self.assertEqual(writer.finish()['a']['volume_section']['status'],'WITHHELD')

    def test_unknown_width_cannot_prove_neighboring_road_outside_crop(self):
        writer=StreamingLocalProcess([candidate(station=5,bounds=[[2,8],[-2,2],[0,2]])])
        writer.motion([0,0,1],[10,0,1],1,1,0,'inner wall',self.context())
        writer.motion([0,2.1,1],[10,2.1,1],None,1,0,'outer wall',self.context())
        self.assertEqual(writer.finish()['a']['volume_section']['status'],'WITHHELD')

    def test_partial_height_crop_changes_section_not_declared_height(self):
        writer=StreamingLocalProcess([candidate(station=5,bounds=[[2,8],[-2,2],[.5,1]])])
        writer.motion([0,0,1],[10,0,1],1,1,0,'inner wall',self.context(5))
        result=writer.finish()['a']['volume_section']
        self.assertEqual(result['status'],'COMPLETE')
        self.assertAlmostEqual(result['area_mm2'],.25)

    def test_negative_and_nonfinite_volume_never_become_zero_geometry(self):
        for value in (-1,float('inf'),float('-inf'),True):
            with self.subTest(volume=value):
                result=self.collect(context=self.context(value))['a']
                self.assertIsNone(result['roles']['INNER_WALL']['commanded_volume_mm3'])
                self.assertEqual(result['volume_section']['status'],'WITHHELD')
                self.assertIsNone(result['volume_section']['area_mm2'])

    def test_explicit_zero_volume_is_known_but_has_no_positive_section(self):
        result=self.collect(context=self.context(0))['a']
        role=result['roles']['INNER_WALL']
        self.assertEqual(role['commanded_volume_mm3'],0)
        self.assertAlmostEqual(role['volume_known_length_mm'],6)
        self.assertTrue(valid_process_descriptor(result))
        self.assertEqual(result['volume_section']['status'],'WITHHELD')
        self.assertIsNone(result['volume_section']['area_mm2'])
        self.assertNotIn('COMMANDED_VOLUME_REQUIRED',result['volume_section']['assessment_gaps'])

    def test_invalid_source_coordinate_cannot_leave_volume_section_complete(self):
        for start in ([0,float('nan'),1],[0,0],['invalid',0,1]):
            with self.subTest(start=start):
                writer=StreamingLocalProcess([candidate(station=5,bounds=[[2,8],[-2,2],[0,2]])])
                writer.motion([0,0,1],[10,0,1],1,1,0,'inner wall',self.context())
                writer.motion(start,[10,0,1],1,1,0,'outer wall',self.context())
                self.assertEqual(writer.finish()['a']['volume_section']['status'],'WITHHELD')

    def test_malformed_role_metadata_is_rejected_without_raising(self):
        from copy import deepcopy
        for bad in (None,[],42,'inner wall'):
            with self.subTest(role=bad):
                value=deepcopy(self.collect()['a'])
                value['roles']['INNER_WALL']=bad
                self.assertFalse(valid_process_descriptor(value))

    def test_temperature_context_does_not_change_material_or_reference_force(self):
        from print_strength_engine.capacity import capacity_for_candidate
        low=self.prepared_candidate(nozzle_setpoint_c=180)
        high=self.prepared_candidate(nozzle_setpoint_c=300)
        mpa={'X':20,'Y':20,'Z':10}
        a=capacity_for_candidate(low,mpa)
        b=capacity_for_candidate(high,mpa)
        self.assertEqual(a['material_reference_mpa'],b['material_reference_mpa'])
        self.assertAlmostEqual(a['bending_force_n'],b['bending_force_n'])
        self.assertAlmostEqual(a['axial_capacity_n'],b['axial_capacity_n'])
        self.assertFalse(a['geometry_scenarios']['temperature_strength_multiplier_applied'])

    def test_unknown_thermal_context_preserves_known_volume_scenario(self):
        from print_strength_engine.capacity import capacity_for_candidate
        point=self.prepared_candidate(nozzle_setpoint_c=None,
              assessment_gaps=('NOZZLE_TEMPERATURE_UNAVAILABLE',))
        value=capacity_for_candidate(point,{'X':20,'Y':20,'Z':10})
        self.assertEqual(value['structure_model'],'LOCAL_COMMANDED_VOLUME_UNION')
        self.assertEqual(value['geometry_scenarios']['commanded_volume']['status'],'COMPLETE')

    def test_wrong_process_window_cannot_enable_volume_capacity(self):
        from print_strength_engine.capacity import capacity_for_candidate
        point=self.prepared_candidate()
        point['local_process']['section_window_bounds_mm']=[[20,80],[-2,2],[0,2]]
        value=capacity_for_candidate(point,{'X':20,'Y':20,'Z':10})
        self.assertEqual(value['structure_model'],'LOCAL_DECLARED_ROAD_UNION')

    def test_uncapped_or_measured_volume_section_cannot_enable_capacity(self):
        from print_strength_engine.capacity import capacity_for_candidate
        for field,val in (('width_capped_at_declared',False),('commanded_volume_is_measured',True),
                          ('normal_axis','Z'),('tools',[1]),('complete',False)):
            with self.subTest(field=field):
                point=self.prepared_candidate()
                point['commanded_volume_section'][field]=val
                result=capacity_for_candidate(point,{'X':20,'Y':20,'Z':10})
                self.assertEqual(result['structure_model'],'LOCAL_DECLARED_ROAD_UNION')

    def test_partial_local_scan_cannot_enable_complete_volume_section(self):
        from print_strength_engine.capacity import capacity_for_candidate
        point=self.prepared_candidate()
        point['local_process'].update(complete=False,status='PARTIAL')
        result=capacity_for_candidate(point,{'X':20,'Y':20,'Z':10})
        self.assertEqual(result['structure_model'],'LOCAL_DECLARED_ROAD_UNION')
        self.assertEqual(result['geometry_scenarios']['commanded_volume']['status'],'WITHHELD')

    def test_malformed_commanded_section_is_withheld_without_raising(self):
        from print_strength_engine.capacity import capacity_for_candidate
        for bad in ([],['COMPLETE'],42,'COMPLETE'):
            with self.subTest(section=bad):
                point=self.prepared_candidate()
                point['commanded_volume_section']=bad
                result=capacity_for_candidate(point,{'X':20,'Y':20,'Z':10})
                self.assertEqual(result['structure_model'],'LOCAL_DECLARED_ROAD_UNION')

    def test_volume_geometry_selection_and_material_input_are_immutable(self):
        from copy import deepcopy
        from print_strength_engine.capacity import capacity_for_candidate
        point=self.prepared_candidate()
        original=deepcopy(point)
        mpa={'X':20,'Y':20,'Z':10}
        capacity_for_candidate(point,mpa)
        self.assertEqual(point,original)
        self.assertEqual(mpa,{'X':20,'Y':20,'Z':10})

    def test_known_volume_policy_compares_declared_and_equivalent_selections(self):
        from print_strength_engine.capacity import capacity_for_candidate
        from print_strength_engine.weakness import assess_candidates
        a=self.prepared_candidate(5)
        b=self.prepared_candidate(10)
        b['region_id']='b'
        for rank,point in enumerate((a,b),1):
            point['rank']=rank
            point['estimated_capacity']=capacity_for_candidate(point,{'X':20,'Y':20,'Z':10})
        self.assertEqual(a['estimated_capacity']['structure_model'],'LOCAL_COMMANDED_VOLUME_UNION')
        self.assertEqual(b['estimated_capacity']['structure_model'],'LOCAL_DECLARED_ROAD_UNION')
        self.assertEqual(assess_candidates([a,b])['rank_basis'],'COMPARABLE_LOCAL_25MM_REFERENCE_LOADS')

    def test_unknown_volume_policy_does_not_mix_into_known_volume_rank(self):
        from print_strength_engine.capacity import capacity_for_candidate
        from print_strength_engine.weakness import assess_candidates
        a=self.prepared_candidate(5)
        b=self.prepared_candidate(None)
        b['region_id']='b'
        for rank,point in enumerate((a,b),1):
            point['rank']=rank
            point['estimated_capacity']=capacity_for_candidate(point,{'X':20,'Y':20,'Z':10})
        self.assertEqual(assess_candidates([a,b])['rank_basis'],'GEOMETRIC_SECTION_COMPARISON')

    def test_full_circle_arc_is_not_mistaken_for_zero_length_prime(self):
        writer=StreamingLocalProcess([candidate(station=5,bounds=[[2,8],[-2,2],[0,2]])])
        writer.motion([0,0,1],[10,0,1],1,1,0,'inner wall',self.context())
        writer.motion([0,0,1],[0,0,1],1,1,0,'outer wall',self.context(10),arc=True)
        result=writer.finish()['a']
        self.assertEqual(result['volume_section']['status'],'WITHHELD')
        self.assertIn('ARC_VOLUME_ALLOCATION_UNSUPPORTED',result['assessment_gaps'])

    def test_vertical_deposition_is_not_mistaken_for_zero_length_prime(self):
        writer=StreamingLocalProcess([candidate(station=5,bounds=[[2,8],[-2,2],[0,2]])])
        writer.motion([0,0,1],[10,0,1],1,1,0,'inner wall',self.context())
        writer.motion([5,0,0],[5,0,1],1,1,0,'outer wall',self.context(1))
        result=writer.finish()['a']
        self.assertEqual(result['volume_section']['status'],'WITHHELD')
        self.assertIn('NONPLANAR_DEPOSITION_UNSUPPORTED',result['volume_section']['assessment_gaps'])

    def test_repeated_passes_accumulate_commanded_volume_but_union_once(self):
        writer=StreamingLocalProcess([candidate(station=5,bounds=[[2,8],[-2,2],[0,2]])])
        for _ in range(2):
            writer.motion([0,0,1],[10,0,1],1,1,0,'inner wall',self.context(10))
        result=writer.finish()['a']
        self.assertAlmostEqual(result['roles']['INNER_WALL']['commanded_volume_mm3'],12)
        self.assertAlmostEqual(result['roles']['INNER_WALL']['path_length_mm'],12)
        self.assertAlmostEqual(result['volume_section']['area_mm2'],1)

    def test_oblique_path_uses_length_and_reverse_clipping_consistently(self):
        from math import sqrt
        results=[]
        for start,end in (([0,0,1],[10,10,1]),([10,10,1],[0,0,1])):
            writer=StreamingLocalProcess([candidate(station=5,bounds=[[2,8],[0,10],[0,2]])])
            writer.motion(start,end,1,1,0,'inner wall',self.context(5*sqrt(2)))
            results.append(writer.finish()['a'])
        for result in results:
            self.assertAlmostEqual(result['roles']['INNER_WALL']['path_length_mm'],6*sqrt(2))
            self.assertAlmostEqual(result['roles']['INNER_WALL']['commanded_volume_mm3'],3*sqrt(2))
            self.assertAlmostEqual(result['volume_section']['area_mm2'],.5*sqrt(2))

    def test_multitool_volume_never_becomes_single_material_capacity(self):
        from print_strength_engine.automatic_sections import StreamingSections
        from print_strength_engine.capacity import capacity_for_candidate
        point=candidate(station=5,bounds=[[2,8],[-2,2],[0,2]])
        declared=StreamingSections([point]);writer=StreamingLocalProcess([point])
        for tool,y in ((0,-.5),(1,.5)):
            start,end=[0,y,1],[10,y,1]
            declared.segment(start,end,1,1,tool)
            writer.motion(start,end,1,1,tool,'inner wall',self.context(5))
        point['deposited_section']=declared.finish()['a']
        point['local_process']=writer.finish()['a']
        point['commanded_volume_section']=point['local_process']['volume_section']
        self.assertEqual(point['local_process']['roles']['INNER_WALL']['tools'],[0,1])
        result=capacity_for_candidate(point,{'X':20,'Y':20,'Z':10})
        self.assertNotEqual(result['calculation_status'],'AUTOMATIC_REFERENCE_LOAD_ESTIMATE')
        self.assertIsNone(result['bending_force_n'])

    def test_lower_axial_volume_reference_is_retained_when_bending_is_unchanged(self):
        from math import sqrt
        from print_strength_engine.automatic_sections import StreamingSections
        from print_strength_engine.capacity import capacity_for_candidate
        point=candidate(station=5,bounds=[[2,10],[-2,2],[0,2]])
        point['bending_section_station_mm']=8
        declared=StreamingSections([point]);writer=StreamingLocalProcess([point])
        # The two cuts encounter different roads. Only the axial road changes.
        roads=[([4,0,1],[6,0,1],.01,1,.002),([7,0,1],[9,0,1],1,1,2)]
        for start,end,width,height,volume in roads:
            declared.segment(start,end,width,height,0)
            writer.motion(start,end,width,height,0,'inner wall',self.context(volume))
        point['deposited_section']=declared.finish()['a']
        point['local_process']=writer.finish()['a']
        point['commanded_volume_section']=point['local_process']['volume_section']
        result=capacity_for_candidate(point,{'X':20,'Y':20,'Z':10})
        self.assertAlmostEqual(result['axial_capacity_n'],.02)
        self.assertAlmostEqual(result['effective_load_bearing_area_mm2'],.001)
        self.assertAlmostEqual(result['bending_force_n'],20/(6*sqrt(2)*25))
        self.assertAlmostEqual(result['governing_capacity_n'],.02)
        self.assertEqual(result['geometry_scenarios']['selected_geometry'],'DECLARED_ROADS')
        self.assertEqual(result['geometry_scenarios']['selected_axial_geometry'],'COMMANDED_VOLUME_EQUIVALENT')
        transfer=result['reference_transfer_assumption']
        self.assertEqual(transfer['axial_target_area_basis'],'COMMAND_VOLUME_EQUIVALENT_NET_SECTION')
        self.assertEqual(transfer['bending_target_area_basis'],'DECLARED_NET_ROAD_ENVELOPE')

    def test_volume_changes_reference_load_without_modifying_material_mpa(self):
        from print_strength_engine.capacity import capacity_for_candidate
        from print_strength_engine.automatic_sections import StreamingSections
        point=candidate(station=5,bounds=[[2,8],[-2,2],[0,2]])
        declared=StreamingSections([point]);declared.segment([0,0,1],[10,0,1],1,1,0)
        point['deposited_section']=declared.finish()['a']
        local=self.collect(5)['a'];point['local_process']=local;point['commanded_volume_section']=local['volume_section']
        mpa={'X':20,'Y':20,'Z':10};result=capacity_for_candidate(point,mpa)
        self.assertEqual(mpa,{'X':20,'Y':20,'Z':10})
        self.assertEqual(result['structure_model'],'LOCAL_COMMANDED_VOLUME_UNION')
        self.assertLess(result['bending_force_n'],result['geometry_scenarios']['declared']['bending_force_n'])
        self.assertFalse(result['is_failure_prediction'])
        self.assertFalse(result['geometry_scenarios']['temperature_strength_multiplier_applied'])
