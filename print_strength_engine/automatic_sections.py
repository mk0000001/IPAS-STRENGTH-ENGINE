"""Stream exact selected cuts of declared road prisms without storing whole G-code.

Only local cropped section geometry is reconstructed. Geometric continuity,
printed bead shape, weld strength and a whole-part load path are not certified.
"""
from math import fsum,hypot,isfinite
from .deposition_section import finite_number,vector,UnsupportedGeometry

MAX_CANDIDATES=6
MAX_CUTS=12
MAX_SECTION_PIECES=100_000
MAX_TOTAL_SECTION_PIECES=250_000
MAX_UNION_VERTICES=1_000_000
PROVENANCE='GCODE_WIDTH_HEIGHT_ASSUMPTION'
SCOPE='LOCAL_DECLARED_ROAD_REGION'
VERSION='LOCAL_DECLARED_ROAD_SECTIONS_V2'


def _plane_properties(shape):
    """Integrate polygon rings about their centroid, including holes and Iuv."""
    import numpy as np
    polygons=list(shape.geoms) if shape.geom_type=='MultiPolygon' else [shape]
    if not polygons or any(p.geom_type!='Polygon' for p in polygons) or shape.area<=0:
        raise UnsupportedGeometry('NO_LOCAL_DEPOSITED_SECTION')
    cu,cv=shape.centroid.coords[0];terms=[[],[],[]];vertices=[];holes=0
    for polygon in polygons:
        holes+=len(polygon.interiors)
        for index,ring in enumerate((polygon.exterior,*polygon.interiors)):
            points=[(x-cu,y-cv) for x,y in ring.coords]
            vertices.extend(points[:-1])
            if len(vertices)>MAX_UNION_VERTICES:raise UnsupportedGeometry('LOCAL_SECTION_GEOMETRY_BUDGET_EXCEEDED')
            cross=[a*d-c*b for (a,b),(c,d) in zip(points,points[1:])]
            orientation=1 if fsum(cross)>0 else -1
            sign=orientation*(1 if index==0 else -1)
            terms[0].append(sign*fsum((a*a+a*c+c*c)*q/12 for (a,b),(c,d),q in zip(points,points[1:],cross)))
            terms[1].append(sign*fsum((b*b+b*d+d*d)*q/12 for (a,b),(c,d),q in zip(points,points[1:],cross)))
            terms[2].append(sign*fsum((2*a*b+a*d+c*b+2*c*d)*q/24 for (a,b),(c,d),q in zip(points,points[1:],cross)))
    c00,c11,c01=[fsum(values) for values in terms]
    tensor=np.array([[c00,c01],[c01,c11]],dtype=float)
    moments,directions=np.linalg.eigh(tensor)
    if not np.isfinite(moments).all() or (moments<=0).any():
        raise UnsupportedGeometry('DEGENERATE_SECTION_INERTIA')
    distances=np.max(np.abs(np.asarray(vertices)@directions),axis=0)
    moduli=moments/distances
    if not np.isfinite(moduli).all() or (moduli<=0).any():
        raise UnsupportedGeometry('DEGENERATE_SECTION_INERTIA')
    # For any unit bending-moment vector, the largest stress at a fiber r
    # equals ||C^-1 r||. A linear stress field reaches its extrema on polygon
    # vertices, so this covers every moment orientation within this local
    # homogeneous-section model, including directions between principal axes.
    responses=np.asarray(vertices)@np.linalg.inv(tensor)
    magnitudes=np.linalg.norm(responses,axis=1)
    index=int(np.argmax(magnitudes));response=magnitudes[index]
    if not isfinite(response) or response<=0:raise UnsupportedGeometry('DEGENERATE_SECTION_INERTIA')
    resultant=responses[index]/response
    gradient=np.linalg.solve(tensor,resultant)
    gradient/=np.linalg.norm(gradient)
    return {'area_mm2':float(shape.area),'centroid_uv_mm':[cu,cv],
            'coordinate_second_moment_mm4':tensor.tolist(),
            'principal_second_moments_mm4':moments.tolist(),
            'principal_section_moduli_mm3':moduli.tolist(),
            'principal_stress_gradient_directions_uv':directions.T.tolist(),
            'minimum_all_direction_section_modulus_mm3':float(1/response),
            'critical_stress_gradient_uv':gradient.tolist(),
            'critical_bending_moment_direction_uv':[float(resultant[1]),float(-resultant[0])],
            'component_count':len(polygons),'hole_count':holes,'boundary_vertex_count':len(vertices)}


def _xy_interval(footprint,axis,station):
    values=[];other=1-axis
    for start,end in zip(footprint,footprint[1:]+footprint[:1]):
        left,right=start[axis],end[axis]
        if left==right:
            if station==left:values.extend((start[other],end[other]))
        elif min(left,right)<=station<=max(left,right):
            ratio=(station-left)/(right-left)
            values.append(start[other]+ratio*(end[other]-start[other]))
    return (min(values),max(values)) if len(values)>1 else None


class StreamingSections:
    """Consume every model road; retain only bounded intersections of <=12 cuts."""
    def __init__(self,candidates):
        candidates=list(candidates)
        if len(candidates)>MAX_CANDIDATES:raise ValueError('LOCAL_SECTION_CANDIDATE_LIMIT')
        self.entries={};self.cuts={};self.source_records_scanned=0;self.total_pieces=0;self.gaps=set()
        for candidate in candidates:
            key=str(candidate.get('region_id') or '')
            if not key or key in self.entries:raise ValueError('UNIQUE_LOCAL_REGION_ID_REQUIRED')
            entry={'cuts':{},'gaps':[],'intersecting_records':0,'candidate':candidate};self.entries[key]=entry
            try:
                axis='XYZ'.index(str(candidate.get('section_normal_axis') or '').upper())
                bounds=candidate.get('section_window_bounds_mm')
                if not isinstance(bounds,(list,tuple)) or len(bounds)!=3:raise ValueError()
                normalized=[]
                for pair in bounds:
                    if not isinstance(pair,(list,tuple)) or len(pair)!=2:raise ValueError()
                    lo,hi=[finite_number(value) for value in pair]
                    if lo>=hi:raise ValueError()
                    normalized.append([lo,hi])
                axial=finite_number(candidate.get('axial_section_station_mm',candidate.get('section_station_mm')))
                bending=finite_number(candidate.get('bending_section_station_mm',axial))
                if any(not normalized[axis][0]<=station<=normalized[axis][1] for station in (axial,bending)):
                    raise ValueError()
            except (ValueError,TypeError):
                entry['gaps'].append('LOCAL_SECTION_WINDOW_REQUIRED');continue
            u=(axis+1)%3;v=(axis+2)%3
            entry.update(axis=axis,u=u,v=v,bounds=normalized)
            for name,station in (('axial',axial),('bending',bending)):
                cut_key=(axis,station,tuple(normalized[u]),tuple(normalized[v]))
                if cut_key not in self.cuts:
                    self.cuts[cut_key]={'axis':axis,'u':u,'v':v,'station':station,'bounds':normalized,
                                        'pieces':set(),'tools':set(),'members':set(),'gaps':set()}
                self.cuts[cut_key]['members'].add(key);entry['cuts'][name]=cut_key
        if len(self.cuts)>MAX_CUTS:raise ValueError('LOCAL_SECTION_CUT_LIMIT')

    def segment(self,start,end,width,height,tool):
        self.source_records_scanned+=1
        if self.gaps:return
        try:
            start=vector(start);end=vector(end)
            if width is None or height is None:raise UnsupportedGeometry('DECLARED_ROAD_DIMENSIONS_REQUIRED')
            width=finite_number(width);height=finite_number(height)
            if not .001<=width<=10 or not .001<=height<=10:raise UnsupportedGeometry('INVALID_ROAD_DIMENSIONS')
            if start[2]!=end[2]:raise UnsupportedGeometry('NONPLANAR_DEPOSITION_UNSUPPORTED')
            if isinstance(tool,bool) or not isinstance(tool,int) or tool<0:raise UnsupportedGeometry('DEPOSITION_TOOL_REQUIRED')
        except ValueError:
            self.gaps.add('INVALID_DEPOSITION_RECORD');return
        except UnsupportedGeometry as error:
            self.gaps.add(str(error));return
        dx=end[0]-start[0];dy=end[1]-start[1];length=hypot(dx,dy)
        if not length:return
        broad=[[min(start[i],end[i])-width/2,max(start[i],end[i])+width/2] for i in (0,1)]
        broad.append([start[2]-height,start[2]])
        possible=[]
        for cut in self.cuts.values():
            if cut['gaps']:continue
            axis=cut['axis'];station=cut['station'];bounds=cut['bounds'];u=cut['u'];v=cut['v']
            if not broad[axis][0]<=station<broad[axis][1]:continue
            if any(broad[i][1]<=bounds[i][0] or broad[i][0]>=bounds[i][1] for i in (u,v)):continue
            possible.append(cut)
        if not possible:return
        nx=-dy/length*width/2;ny=dx/length*width/2
        footprint=((start[0]+nx,start[1]+ny),(end[0]+nx,end[1]+ny),
                   (end[0]-nx,end[1]-ny),(start[0]-nx,start[1]-ny))
        from shapely.geometry import Polygon,box
        matched=set()
        for cut in possible:
            axis=cut['axis'];station=cut['station'];bounds=cut['bounds'];u=cut['u'];v=cut['v']
            if axis==2:
                clipped=Polygon(footprint).intersection(box(*[bounds[0][0],bounds[1][0],bounds[0][1],bounds[1][1]]))
                if clipped.is_empty or clipped.area<=0:continue
                piece=tuple(clipped.exterior.coords[:-1])
            else:
                extent=[p[axis] for p in footprint]
                # Positive-axis one-sided limit avoids merging both sides of
                # a layer/road cap into a fictitious boundary section.
                if not min(extent)<=station<max(extent):continue
                interval=_xy_interval(footprint,axis,station)
                if interval is None:continue
                other=1-axis
                low=max(interval[0],bounds[other][0]);high=min(interval[1],bounds[other][1])
                bottom=max(broad[2][0],bounds[2][0]);top=min(broad[2][1],bounds[2][1])
                if low>=high or bottom>=top:continue
                piece=(low,high,bottom,top) if u==other else (bottom,top,low,high)
            cut['tools'].add(tool);matched.update(cut['members'])
            if piece in cut['pieces']:continue
            if len(cut['pieces'])>=MAX_SECTION_PIECES or self.total_pieces>=MAX_TOTAL_SECTION_PIECES:
                cut['gaps'].add('LOCAL_SECTION_GEOMETRY_BUDGET_EXCEEDED');continue
            cut['pieces'].add(piece);self.total_pieces+=1
        for key in matched:self.entries[key]['intersecting_records']+=1

    def finish(self,complete=True):
        from shapely import union_all
        from shapely.geometry import Polygon,box
        from shapely.errors import GEOSException
        results={};cut_results={}
        for key,cut in self.cuts.items():
            gaps=set(self.gaps)|cut['gaps']
            if not complete:gaps.add('INCOMPLETE_SOURCE_SCAN')
            if not gaps:
                try:
                    shapes=[Polygon(piece) if cut['axis']==2 else box(piece[0],piece[2],piece[1],piece[3])
                            for piece in cut['pieces']]
                    shape=union_all(shapes,grid_size=0)
                    properties=_plane_properties(shape)
                    properties.update(station_mm=cut['station'],tools=sorted(cut['tools']),
                                      plane_axes=['XYZ'[cut['u']],'XYZ'[cut['v']]],
                                      station_side='POSITIVE_AXIS_LIMIT')
                    cut_results[key]=(properties,[])
                except (UnsupportedGeometry,GEOSException) as error:
                    gaps.add(str(error) if isinstance(error,UnsupportedGeometry) else 'INVALID_LOCAL_SECTION_UNION')
            if gaps:cut_results[key]=(None,sorted(gaps))
        for key,entry in self.entries.items():
            gaps=set(self.gaps)|set(entry['gaps'])
            if not complete:gaps.add('INCOMPLETE_SOURCE_SCAN')
            local={}
            for name,cut_key in entry['cuts'].items():
                properties,reasons=cut_results[cut_key];local[name]=properties;gaps.update(reasons)
            value={'version':VERSION,'status':'WITHHELD' if gaps else 'COMPLETE','complete':not gaps,'sampled':False,
                   'provenance':PROVENANCE,'scope':SCOPE,
                   'geometry_basis':'UNION_OF_DECLARED_RECTANGULAR_ROAD_ENVELOPES',
                   'normal_axis':'XYZ'[entry['axis']] if 'axis' in entry else None,
                   'plane_axes':['XYZ'[entry['u']],'XYZ'[entry['v']]] if 'axis' in entry else None,
                   'section_window_bounds_mm':entry.get('bounds'),'source_records_scanned':self.source_records_scanned,
                   'intersecting_records':entry['intersecting_records'],'assessment_gaps':sorted(gaps),
                   'area_mm2':None,'min_principal_section_modulus_mm3':None,
                   'minimum_all_direction_section_modulus_mm3':None,'tools':[],
                   'printed_bead_geometry_measured':False,'bonded_contact_area_mm2':None,
                   'crop_boundary_applied':True,'whole_object_section_verified':False}
            if not gaps:
                value.update(local,area_mm2=local['axial']['area_mm2'],
                    min_principal_section_modulus_mm3=min(local['bending']['principal_section_moduli_mm3']),
                    minimum_all_direction_section_modulus_mm3=local['bending']['minimum_all_direction_section_modulus_mm3'],
                    tools=sorted(set(local['axial']['tools'])|set(local['bending']['tools'])))
                gradient=[0.,0.,0.];moment=[0.,0.,0.]
                for index,axis in enumerate((entry['u'],entry['v'])):
                    gradient[axis]=local['bending']['critical_stress_gradient_uv'][index]
                    moment[axis]=local['bending']['critical_bending_moment_direction_uv'][index]
                value.update(weakest_local_bending_stress_gradient_xyz=gradient,
                             critical_bending_moment_direction_xyz=moment)
            results[key]=value
        return results
