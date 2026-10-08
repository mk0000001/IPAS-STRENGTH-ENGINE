"""Exact local road-section geometry, independently checked analytically."""
import math
import unittest
from unittest.mock import patch

try:
    from print_strength_engine.automatic_sections import StreamingSections
except ImportError:
    StreamingSections=None

from test_load_case import beam


def candidate(axis='X',station=50,bounds=None):
    return {'kind':'LOCAL_THIN_SECTION','region_id':'a','section_normal_axis':axis,'section_station_mm':station,
            'bending_section_station_mm':station,
            'section_window_bounds_mm':bounds or [[40,60],[-6,6],[-1,11]],
            'min_section_area_mm2':99999,'section_modulus_mm3':99999}


def raw_component_properties(piece_tools):
    """Exercise real raw geometry with controlled proof order and GEOS counters."""
    from shapely.geometry.base import BaseGeometry
    point=candidate('Z',.5,[[-30,30],[-30,30],[0,2]])
    point['kind']='COMPONENT_REFERENCE_SECTION'
    writer=StreamingSections([point]);cut=next(iter(writer.cuts.values()))
    # Only the test orders the raw iterable; production keeps its original set.
    cut['pieces']=[piece for piece,tools in piece_tools]
    cut['piece_tools']={piece:set(tools) for piece,tools in piece_tools}
    cut['tools']=set().union(*(tools for piece,tools in piece_tools))
    calls={'intersects':0,'intersection':0}
    intersects=BaseGeometry.intersects;intersection=BaseGeometry.intersection
    def counted_intersects(shape,other):
        calls['intersects']+=1
        return intersects(shape,other)
    def counted_intersection(shape,other,*args,**kwargs):
        calls['intersection']+=1
        return intersection(shape,other,*args,**kwargs)
    with patch.object(BaseGeometry,'intersects',counted_intersects),patch.object(BaseGeometry,'intersection',counted_intersection):
        result=writer._cut_properties(cut)
    return result,calls


def rectangle(x0,y0,x1,y1):
    return ((x0,y0),(x1,y0),(x1,y1),(x0,y1))


class AutomaticSectionTests(unittest.TestCase):
    def extract(self,geometry=None,point=None,complete=True):
        self.assertIsNotNone(StreamingSections,'streamed local section extraction is missing')
        writer=StreamingSections([point or candidate()])
        for row in (geometry or beam())['segments']:
            writer.segment(row['start'],row['end'],row.get('width_mm'),row.get('height_mm'),row.get('tool'))
        return writer.finish(complete=complete)['a']

    def test_rectangle_net_area_and_finite_inertia(self):
        result=self.extract()
        self.assertEqual(result['status'],'COMPLETE')
        self.assertEqual(result['scope'],'LOCAL_DECLARED_ROAD_REGION')
        self.assertAlmostEqual(result['area_mm2'],20)
        self.assertAlmostEqual(result['axial']['coordinate_second_moment_mm4'][1][1],20/3)
        self.assertAlmostEqual(result['min_principal_section_modulus_mm3'],20/3)
        self.assertEqual(result['axial']['component_count'],1)

    def test_hollow_section_preserves_hole(self):
        result=self.extract(beam(10,10,hollow=True))
        self.assertAlmostEqual(result['area_mm2'],36)
        self.assertAlmostEqual(result['axial']['coordinate_second_moment_mm4'][1][1],492)
        self.assertAlmostEqual(result['min_principal_section_modulus_mm3'],98.4)
        self.assertEqual(result['axial']['hole_count'],1)

    def test_angled_road_plane_is_not_its_xy_bounding_box(self):
        geometry={'segments':[{'start':[0,0,1],'end':[10,10,1],
                              'width_mm':2,'height_mm':1,'tool':0}]}
        point=candidate(station=5,bounds=[[0,10],[-5,15],[-1,2]])
        result=self.extract(geometry,point)
        self.assertAlmostEqual(result['area_mm2'],2*math.sqrt(2))
        self.assertAlmostEqual(result['axial']['centroid_uv_mm'][0],5)
        self.assertAlmostEqual(result['min_principal_section_modulus_mm3'],math.sqrt(2)/3)

    def test_z_cut_rotated_road_retains_product_of_inertia(self):
        geometry={'segments':[{'start':[0,0,1],'end':[10,10,1],
                              'width_mm':2,'height_mm':1,'tool':0}]}
        point=candidate('Z',.5,[[-5,15],[-5,15],[-1,2]])
        result=self.extract(geometry,point)
        self.assertAlmostEqual(result['area_mm2'],20*math.sqrt(2))
        tensor=result['axial']['coordinate_second_moment_mm4']
        self.assertAlmostEqual(tensor[0][1],490*math.sqrt(2)/3)
        self.assertAlmostEqual(result['min_principal_section_modulus_mm3'],20*math.sqrt(2)/3)

    def test_cropped_neighbor_cannot_add_area(self):
        geometry=beam()
        for row in beam()['segments']:
            row['start'][1]+=50;row['end'][1]+=50
            geometry['segments'].append(row)
        self.assertAlmostEqual(self.extract(geometry)['area_mm2'],20)

    def test_crop_is_local_and_does_not_fill_infill_gaps(self):
        geometry=beam();geometry['segments']=[row for row in geometry['segments'] if abs(row['start'][1])>4]
        result=self.extract(geometry)
        self.assertAlmostEqual(result['area_mm2'],4)
        self.assertEqual(result['axial']['component_count'],2)
        cropped=self.extract(point=candidate(bounds=[[40,60],[-1,1],[-1,11]]))
        self.assertAlmostEqual(cropped['area_mm2'],4)

    def test_duplicate_and_overlapping_roads_are_union_geometry(self):
        geometry=beam();geometry['segments']*=2
        self.assertAlmostEqual(self.extract(geometry)['area_mm2'],20)

    def test_separate_axial_and_bending_stations_are_extracted(self):
        geometry=beam()
        for row in geometry['segments']:
            if abs(row['start'][1])>.5:row['end'][0]=50
        point=candidate(station=45,bounds=[[40,60],[-6,6],[-1,11]])
        point['bending_section_station_mm']=55
        result=self.extract(geometry,point)
        self.assertAlmostEqual(result['axial']['area_mm2'],20)
        self.assertAlmostEqual(result['bending']['area_mm2'],4)
        self.assertAlmostEqual(result['min_principal_section_modulus_mm3'],4/3)

    def test_late_record_after_old_sidecar_limit_is_retained(self):
        self.assertIsNotNone(StreamingSections)
        writer=StreamingSections([candidate()])
        for _ in range(200001):writer.segment([0,100,1],[100,100,1],1,1,0)
        writer.segment([0,0,1],[100,0,1],1,1,0)
        result=writer.finish()['a']
        self.assertEqual(result['source_records_scanned'],200002)
        self.assertAlmostEqual(result['area_mm2'],1)

    def test_incomplete_or_invalid_dimensions_never_return_partial_area(self):
        result=self.extract(complete=False)
        self.assertEqual(result['status'],'WITHHELD');self.assertIsNone(result['area_mm2'])
        for key,value in (('width_mm',None),('height_mm',-1),('width_mm',float('nan'))):
            geometry=beam();geometry['segments'][-1][key]=value
            result=self.extract(geometry)
            self.assertEqual(result['status'],'WITHHELD');self.assertIsNone(result['area_mm2'])

    def test_source_layer_boundary_uses_positive_axis_limit(self):
        geometry={'segments':[{'start':[0,0,1],'end':[100,0,1],'width_mm':2,'height_mm':1,'tool':0},
                              {'start':[0,0,2],'end':[100,0,2],'width_mm':4,'height_mm':1,'tool':0}]}
        result=self.extract(geometry,candidate('Z',1,[[-1,101],[-5,5],[0,3]]))
        self.assertAlmostEqual(result['area_mm2'],400)

    def test_translation_preserves_central_inertia(self):
        geometry=beam();point=candidate();delta=[20000,-30000,40000]
        for row in geometry['segments']:
            for key in ('start','end'):row[key]=[a+b for a,b in zip(row[key],delta)]
        point['section_station_mm']+=delta[0];point['bending_section_station_mm']+=delta[0]
        point['section_window_bounds_mm']=[[a+d,b+d] for (a,b),d in zip(point['section_window_bounds_mm'],delta)]
        self.assertAlmostEqual(self.extract(geometry,point)['min_principal_section_modulus_mm3'],20/3)

    def test_all_moment_directions_include_square_diagonal_stress(self):
        geometry={'segments':[{'start':[-1,0,1],'end':[1,0,1],'width_mm':2,'height_mm':1,'tool':0}]}
        result=self.extract(geometry,candidate('Z',.5,[[-2,2],[-2,2],[0,2]]))
        self.assertAlmostEqual(result['min_principal_section_modulus_mm3'],4/3)
        self.assertIsNotNone(result.get('minimum_all_direction_section_modulus_mm3'))
        self.assertAlmostEqual(result['minimum_all_direction_section_modulus_mm3'],4/(3*math.sqrt(2)))

    def test_all_direction_bending_modulus_is_rotation_invariant(self):
        q=1/math.sqrt(2)
        geometry={'segments':[{'start':[-q,-q,1],'end':[q,q,1],'width_mm':2,'height_mm':1,'tool':0}]}
        result=self.extract(geometry,candidate('Z',.5,[[-2,2],[-2,2],[0,2]]))
        self.assertIsNotNone(result.get('minimum_all_direction_section_modulus_mm3'))
        self.assertAlmostEqual(result['minimum_all_direction_section_modulus_mm3'],4/(3*math.sqrt(2)))

    def test_reported_nonsquare_moment_and_stress_gradient_match_extreme(self):
        result=self.extract();section=result['bending'];tensor=section['coordinate_second_moment_mm4']
        mu,mv=section['critical_bending_moment_direction_uv']
        det=tensor[0][0]*tensor[1][1]-tensor[0][1]**2
        gu=(-mv*tensor[1][1]-mu*tensor[0][1])/det
        gv=(mu*tensor[0][0]+mv*tensor[0][1])/det
        norm=math.hypot(gu,gv)
        self.assertAlmostEqual(math.hypot(mu,mv),1)
        self.assertAlmostEqual(section['critical_stress_gradient_uv'][0],gu/norm)
        self.assertAlmostEqual(section['critical_stress_gradient_uv'][1],gv/norm)
        maximum=max(abs(gu*y+gv*z) for y in (-5,5) for z in (-1,1))
        self.assertAlmostEqual(maximum,1/result['minimum_all_direction_section_modulus_mm3'])

    def test_raw_geometry_budget_uses_compact_fallback_without_retaining_prefix(self):
        with patch('print_strength_engine.automatic_sections.MAX_SECTION_PIECES',1):
            result=self.extract()
        self.assertEqual(result['status'],'COMPLETE')
        self.assertAlmostEqual(result['area_mm2'],20)
        self.assertTrue(result['resource_compaction']['attempted'])
        self.assertTrue(result['resource_compaction']['applied'])

    def test_missing_crop_does_not_aggregate_whole_plate(self):
        point=candidate();del point['section_window_bounds_mm']
        result=self.extract(point=point)
        self.assertEqual(result['status'],'WITHHELD')
        self.assertIn('LOCAL_SECTION_WINDOW_REQUIRED',result['assessment_gaps'])

    def test_partial_overlap_is_union_not_sum(self):
        geometry={'segments':[{'start':[0,.5,1],'end':[100,.5,1],'width_mm':1,'height_mm':1,'tool':0},
                              {'start':[0,1,1],'end':[100,1,1],'width_mm':1,'height_mm':1,'tool':0}]}
        self.assertAlmostEqual(self.extract(geometry)['area_mm2'],1.5)

    def test_raw_component_tool_proof_stops_after_one_positive_same_tool_road(self):
        pieces=[(rectangle(0,0,4,2),{0})]
        pieces += [(rectangle(.25+i/1024,.25,3.5,1.75),{0}) for i in range(256)]
        result,calls=raw_component_properties(pieces)
        self.assertEqual(result['tools'],[0])
        self.assertEqual(result['area_mm2'],8)
        self.assertEqual(result['centroid_uv_mm'],[2,1])
        self.assertAlmostEqual(result['minimum_all_direction_section_modulus_mm3'],16/(3*math.sqrt(5)))
        self.assertEqual(calls,{'intersects':1,'intersection':1})

    def test_raw_component_tool_proof_keeps_zero_area_boundary_tool_unproven(self):
        pieces=[(rectangle(0,0,1,1),{0})]
        pieces += [(rectangle(.1+i/1024,.1,.9,.9),{0}) for i in range(64)]
        pieces.append((rectangle(1,1,4,4),{1}))
        result,calls=raw_component_properties(pieces)
        self.assertEqual(result['tools'],[0])
        self.assertEqual(result['reference_component_count'],2)
        self.assertEqual(result['area_mm2'],1)
        self.assertAlmostEqual(result['minimum_all_direction_section_modulus_mm3'],1/(6*math.sqrt(2)))
        self.assertEqual(calls,{'intersects':2,'intersection':2})

    def test_raw_component_tool_proof_finds_late_selected_tool_without_unselected_tool(self):
        pieces=[(rectangle(0,0,4,2),{0})]
        pieces += [(rectangle(.25+i/1024,.25,3.5,1.75),{0}) for i in range(64)]
        pieces += [(rectangle(10,0,18,8),{2}),(rectangle(4,2,12,10),{3}),
                   (rectangle(.5,.5,3,1.5),{0,1})]
        result,calls=raw_component_properties(pieces)
        self.assertEqual(result['tools'],[0,1])
        self.assertEqual(result['reference_component_count'],2)
        self.assertEqual(result['area_mm2'],8)
        self.assertEqual(result['selected_component_bounds_uv_mm'],[[0,4],[0,2]])
        self.assertAlmostEqual(result['minimum_all_direction_section_modulus_mm3'],16/(3*math.sqrt(5)))
        self.assertEqual(calls,{'intersects':4,'intersection':3})


if __name__=='__main__':unittest.main()
