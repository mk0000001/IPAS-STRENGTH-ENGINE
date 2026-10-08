"""Synthetic behavior contracts for a separately bounded exact-union fallback."""
from copy import deepcopy
import json
from unittest.mock import patch

import pytest
from print_strength_engine import automatic_sections as sections
from print_strength_engine.local_process import StreamingLocalProcess


def point(axis='Z',component=False):
    return {'kind':'COMPONENT_REFERENCE_SECTION' if component else 'LOCAL_THIN_SECTION',
            'region_id':'synthetic-plane','section_normal_axis':axis,
            'section_station_mm':.5,'axial_section_station_mm':.5,'bending_section_station_mm':.5,
            'section_window_bounds_mm':[[-20,20],[-20,20],[0,2]]}


def roads():
    return [([-4,y,1],[4,y,1],1.,1.,tool) for y,tool in ((0,0),(.5,1),(1.,0))]


def extract(rows=None,candidate=None,**kwargs):
    collector=sections.StreamingSections([candidate or point()],**kwargs)
    for row in rows or roads():collector.segment(*row)
    return collector.finish()['synthetic-plane']


def budget(**kwargs):
    from print_strength_engine.compact_sections import CompactGeometryBudget
    return CompactGeometryBudget(**kwargs)


def numeric_payload(value):
    return {key:deepcopy(item) for key,item in value.items() if key!='resource_compaction'}


def direction_invariant_payload(value):
    """Opposite extreme fibers are an equally governing direction on symmetry."""
    result=numeric_payload(value)
    for descriptor in [result,result.get('axial') or {},result.get('bending') or {}]:
        for key in ('critical_stress_gradient_uv','critical_bending_moment_direction_uv',
                    'weakest_local_bending_stress_gradient_xyz','critical_bending_moment_direction_xyz'):
            if key in descriptor:
                sign=next((1 if number>0 else -1 for number in descriptor[key] if abs(number)>1e-15),1)
                descriptor[key]=[sign*number for number in descriptor[key]]
        if 'boundary_support_vertices_relative_uv_mm' in descriptor:
            descriptor['boundary_support_vertices_relative_uv_mm']=sorted(descriptor['boundary_support_vertices_relative_uv_mm'])
    return result


def test_normal_raw_result_bytes_do_not_change_when_shared_policy_is_available():
    before=extract()
    after=extract(compact_budget=budget())
    assert json.dumps(after,sort_keys=True,allow_nan=False)==json.dumps(before,sort_keys=True,allow_nan=False)
    assert 'resource_compaction' not in after


def test_raw_piece_cap_triggers_fallback_instead_of_publishing_prefix_or_withholding_valid_geometry():
    expected=extract()
    with patch.object(sections,'MAX_SECTION_PIECES',1):
        actual=extract(compact_budget=budget())
    assert actual['status']=='COMPLETE'
    assert numeric_payload(actual)==expected
    assert actual['resource_compaction']['attempted'] is True
    assert actual['resource_compaction']['applied'] is True


def test_compact_byte_exhaustion_is_separate_and_never_publishes_a_partial_area():
    with patch.object(sections,'MAX_SECTION_PIECES',1):
        actual=extract(compact_budget=budget(max_packed_bytes=1))
    assert actual['status']=='WITHHELD'
    assert actual['area_mm2'] is None
    assert 'LOCAL_SECTION_COMPACT_RESOURCE_BUDGET_EXCEEDED' in actual['assessment_gaps']
    assert actual['resource_compaction']['attempted'] is True
    assert actual['resource_compaction']['applied'] is False


def test_per_cut_union_vertex_limit_still_withholds_compacted_geometry():
    with patch.object(sections,'MAX_SECTION_PIECES',1),patch.object(sections,'MAX_UNION_VERTICES',3):
        actual=extract(compact_budget=budget())
    assert actual['status']=='WITHHELD'
    assert actual['area_mm2'] is None


def test_raw_final_vertex_budget_failure_gets_one_real_fallback_attempt_and_terminal_marker():
    with patch.object(sections,'MAX_UNION_VERTICES',3):actual=extract(compact_budget=budget())
    assert actual['status']=='WITHHELD'
    assert actual['area_mm2'] is None
    assert actual['resource_compaction']['attempted'] is True
    assert actual['resource_compaction']['applied'] is False


def test_overlapping_different_tools_are_all_retained_after_compaction():
    with patch.object(sections,'MAX_SECTION_PIECES',1):
        actual=extract(compact_budget=budget())
    assert actual['tools']==[0,1]
    assert actual['axial']['tools']==[0,1]
    assert actual['bending']['tools']==[0,1]
    assert actual['area_mm2']==16


@pytest.mark.parametrize('axis',['X','Y','Z'])
def test_fallback_uses_same_clipped_plane_for_all_normal_axes(axis):
    candidate=point(axis)
    rows=[([-4+i*.5,y,1],[4-i*.5,y,1],1,1,tool) for i,(y,tool) in enumerate(((0,0),(.5,1),(1,0)))]
    expected=extract(rows,candidate)
    with patch.object(sections,'MAX_SECTION_PIECES',1):
        actual=extract(rows,candidate,compact_budget=budget())
    assert actual['status']=='COMPLETE'
    assert direction_invariant_payload(actual)==direction_invariant_payload(expected)


def test_holes_are_preserved_without_solid_filling():
    frame=[([-5,-4.5,1],[5,-4.5,1],1,1,0),([-5,4.5,1],[5,4.5,1],1,1,0),
           ([-4.5,-5,1],[-4.5,5,1],1,1,0),([4.5,-5,1],[4.5,5,1],1,1,0)]
    expected=extract(frame)
    with patch.object(sections,'MAX_SECTION_PIECES',1):
        actual=extract(frame,compact_budget=budget())
    assert numeric_payload(actual)==expected
    assert actual['area_mm2']==36
    assert actual['axial']['hole_count']==1


def test_reference_component_selection_does_not_sum_disconnected_bodies():
    separate=[([-4,0,1],[4,0,1],1,1,0),([10,0,1],[11,0,1],.5,1,1)]
    expected=extract(separate,point(component=True))
    with patch.object(sections,'MAX_SECTION_PIECES',1):
        actual=extract(separate,point(component=True),compact_budget=budget())
    assert numeric_payload(actual)==expected
    assert actual['component_count']==2
    assert actual['area_mm2']==.5
    assert actual['tools']==[1]
    assert sections.valid_component_selection(actual)


def test_duplicate_road_with_new_tool_keeps_tool_proof_even_after_geometry_deduplication():
    rows=roads()+[(*roads()[0][:-1],3)]
    with patch.object(sections,'MAX_SECTION_PIECES',1):
        actual=extract(rows,compact_budget=budget())
    assert actual['area_mm2']==16
    assert actual['tools']==[0,1,3]


def test_local_commanded_volume_collector_receives_same_resource_budget_instance():
    shared=budget()
    declared=sections.StreamingSections([point()],compact_budget=shared)
    volume=StreamingLocalProcess([point()],compact_budget=shared)
    assert declared.compact_budget is shared
    assert volume.sections.compact_budget is shared


def test_incomplete_source_still_withholds_after_successful_compaction():
    with patch.object(sections,'MAX_SECTION_PIECES',1):
        collector=sections.StreamingSections([point()],compact_budget=budget())
        for row in roads():collector.segment(*row)
        actual=collector.finish(complete=False)['synthetic-plane']
    assert actual['status']=='WITHHELD'
    assert actual['area_mm2'] is None
    assert 'INCOMPLETE_SOURCE_SCAN' in actual['assessment_gaps']


def test_shared_aggregate_exhaustion_releases_failed_cut_and_does_not_regrow_it():
    rows=roads()[:2]
    for _ in range(2):
        with patch.object(sections,'MAX_SECTION_PIECES',1):
            assert extract(rows,compact_budget=budget(max_packed_bytes=600))['status']=='COMPLETE'
    shared=budget(max_packed_bytes=600)
    with patch.object(sections,'MAX_SECTION_PIECES',1):
        first=sections.StreamingSections([point()],compact_budget=shared)
        second=sections.StreamingSections([point()],compact_budget=shared)
        for row in rows:first.segment(*row);second.segment(*row)
        assert first.finish()['synthetic-plane']['status']=='WITHHELD'
        cut=next(iter(first.cuts.values()))
        assert not cut['pieces'] and not cut['compact'].tools
        retained=dict(shared.usage)
        for _ in range(10):first.segment(*rows[0])
        assert shared.usage==retained
        assert second.finish()['synthetic-plane']['status']=='COMPLETE'


def test_final_union_vertex_cap_does_not_count_duplicate_tool_storage_as_final_vertices():
    rows=[([-4,0,1],[4,0,1],1,1,0),([-4,0,1],[4,0,1],1,1,1),
          ([-3,0,1],[3,0,1],.5,1,0)]
    with patch.object(sections,'MAX_SECTION_PIECES',1),patch.object(sections,'MAX_UNION_VERTICES',5):
        actual=extract(rows,point(component=True),compact_budget=budget())
    assert actual['status']=='COMPLETE'
    assert actual['area_mm2']==8
    assert actual['tools']==[0,1]


def test_streaming_geos_failure_withholds_only_affected_cut_and_releases_storage():
    from shapely.errors import GEOSException
    from print_strength_engine import compact_sections
    first=point();second=point();second.update(region_id='second-plane',section_station_mm=1.5,
        axial_section_station_mm=1.5,bending_section_station_mm=1.5)
    shared=budget()
    with patch.object(sections,'MAX_SECTION_PIECES',1),patch.object(compact_sections,'UNION_CHUNK_PIECES',2):
        writer=sections.StreamingSections([first,second],compact_budget=shared)
        with patch.object(compact_sections,'union_all',side_effect=GEOSException('synthetic topology failure')):
            for row in roads():writer.segment(*row)
        writer.segment([-4,0,2],[4,0,2],1,1,0)
        result=writer.finish()
    assert result['synthetic-plane']['status']=='WITHHELD'
    assert 'INVALID_LOCAL_SECTION_UNION' in result['synthetic-plane']['assessment_gaps']
    assert result['second-plane']['status']=='COMPLETE'


def test_point_only_contact_does_not_attribute_another_tool_to_selected_component():
    rows=[([0,0,1],[8,0,1],1,1,0),([10,0,1],[11,0,1],.5,1,1),
          ([11,.75,1],[12,.75,1],1,1,2)]
    with patch.object(sections,'MAX_SECTION_PIECES',1):actual=extract(rows,point(component=True),compact_budget=budget())
    assert actual['status']=='COMPLETE'
    assert actual['area_mm2']==.5
    assert actual['tools']==[1]


def test_compacted_z_station_keeps_positive_axis_one_sided_layer_boundary():
    candidate=point();candidate.update(section_station_mm=1,axial_section_station_mm=1,
                                       bending_section_station_mm=1,section_window_bounds_mm=[[-20,20],[-20,20],[0,3]])
    rows=[([-4,0,1],[4,0,1],10,1,0),([-4,0,2],[4,0,2],1,1,1),([-4,.5,2],[4,.5,2],1,1,1)]
    with patch.object(sections,'MAX_SECTION_PIECES',1):actual=extract(rows,candidate,compact_budget=budget())
    assert actual['status']=='COMPLETE'
    assert actual['area_mm2']==12
    assert actual['tools']==[1]


@pytest.mark.parametrize('chunk',[1,2,2048])
@pytest.mark.parametrize('reverse',[False,True])
def test_small_union_oracle_preserves_holes_components_point_touch_and_narrow_gap(chunk,reverse):
    from shapely import union_all
    from shapely.geometry import box
    from print_strength_engine import compact_sections
    pieces=[box(-5,-5,5,-4),box(-5,4,5,5),box(-5,-4,-4,4),box(4,-4,5,4),
            box(7,0,8,1),box(8,1,9,2),box(10,0,11,1),box(11.0001,0,12,1)]
    expected=union_all(pieces,grid_size=0)
    with patch.object(compact_sections,'UNION_CHUNK_PIECES',chunk):
        compact=compact_sections.CompactCutUnion(2,True,budget(),max_vertices=1000000)
        for shape in reversed(pieces) if reverse else pieces:
            compact.add(tuple(shape.exterior.coords[:-1]),{0})
        actual,tools=compact.finish()
    assert actual.equals(expected)
    assert len(actual.geoms)==len(expected.geoms)
    assert sum(len(p.interiors) for p in actual.geoms)==1
    assert set(tools)=={0}
