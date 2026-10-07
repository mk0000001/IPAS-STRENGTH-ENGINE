"""Stream exact selected cuts of declared road prisms without storing whole G-code.

Only local cropped section geometry is reconstructed. Geometric continuity,
printed bead shape, weld strength and a whole-part load path are not certified.
"""
from math import fsum,hypot,isfinite,isclose
from .deposition_section import finite_number,vector,UnsupportedGeometry

MAX_CANDIDATES=6
MAX_CUTS=12
MAX_SECTION_PIECES=100_000
MAX_TOTAL_SECTION_PIECES=250_000
MAX_UNION_VERTICES=1_000_000
MAX_SUPPORT_VERTICES=4096
MAX_SECTION_COMPONENTS=4096
PROVENANCE='GCODE_WIDTH_HEIGHT_ASSUMPTION'
SCOPE='LOCAL_DECLARED_ROAD_REGION'
VERSION='LOCAL_DECLARED_ROAD_SECTIONS_V4_COMPONENT_SELECTION'
COMPONENT_KINDS=frozenset(('COMPONENT_NECK_SECTION','COMPONENT_REFERENCE_SECTION'))
COMPONENT_SELECTION='MINIMUM_ALL_DIRECTION_MODULUS_CONNECTED_POLYGON'


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
    # A linear normal stress reaches its extreme on the convex support hull.
    # Retain this small geometric witness so cache readers can recompute all
    # moduli from the same inertia, rather than merely bound finite values.
    support=[(x-cu,y-cv) for x,y in list(shape.convex_hull.exterior.coords)[:-1]]
    if len(support)>MAX_SUPPORT_VERTICES:
        raise UnsupportedGeometry('LOCAL_SECTION_SUPPORT_PROOF_BUDGET_EXCEEDED')
    return {'area_mm2':float(shape.area),'centroid_uv_mm':[cu,cv],
            'coordinate_second_moment_mm4':tensor.tolist(),
            'principal_second_moments_mm4':moments.tolist(),
            'principal_section_moduli_mm3':moduli.tolist(),
            'principal_stress_gradient_directions_uv':directions.T.tolist(),
            'minimum_all_direction_section_modulus_mm3':float(1/response),
            'critical_stress_gradient_uv':gradient.tolist(),
            'critical_bending_moment_direction_uv':[float(resultant[1]),float(-resultant[0])],
            'boundary_support_vertices_relative_uv_mm':support,
            'component_count':len(polygons),'hole_count':holes,'boundary_vertex_count':len(vertices)}


def valid_plane_mechanics(section,bounds_uv_mm):
    """Check cached derived mechanics against bounded geometric support.

    This checks internal geometry/arithmetic consistency. It does not certify
    source authenticity, physical bead shape, bonding or fracture resistance.
    """
    try:
        return _valid_plane_mechanics(section,bounds_uv_mm)
    except (ValueError,TypeError,KeyError,OverflowError,ZeroDivisionError):
        return False


def _valid_plane_mechanics(section,bounds):
    import numpy as np
    def numeric(x):
        return isinstance(x,(int,float)) and not isinstance(x,bool) and isfinite(x)
    def pairs(values,count=None):
        return isinstance(values,(list,tuple)) and (count is None or len(values)==count) and all(
            isinstance(row,(list,tuple)) and len(row)==2 and all(numeric(x) for x in row) for row in values)
    if not isinstance(section,dict) or not pairs(bounds,2):return False
    support=section.get('boundary_support_vertices_relative_uv_mm')
    if not pairs(support) or not 3<=len(support)<=MAX_SUPPORT_VERTICES:return False
    centroid=section.get('centroid_uv_mm')
    if not isinstance(centroid,(list,tuple)) or len(centroid)!=2 or not all(numeric(x) for x in centroid):return False
    points=np.asarray(support,dtype=float)
    for i in range(2):
        if bounds[i][0]>=bounds[i][1]:return False
        if any(not bounds[i][0]-1e-6<=value+centroid[i]<=bounds[i][1]+1e-6 for value in points[:,i]):return False
    # The witness must span a nondegenerate envelope containing the net area.
    envelope=abs(fsum(a*d-c*b for (a,b),(c,d) in zip(support,(*support[1:],support[0]))))/2
    area=section.get('area_mm2')
    if not numeric(area) or area<=0 or not isfinite(envelope) or envelope<area*(1-1e-6):return False
    tensor=section.get('coordinate_second_moment_mm4')
    directions=section.get('principal_stress_gradient_directions_uv')
    if not pairs(tensor,2) or not pairs(directions,2):return False
    matrix=np.asarray(tensor,dtype=float);vectors=np.asarray(directions,dtype=float)
    # Relative dimensional tolerances must scale with the geometry. An
    # absolute mm^3/mm^4 allowance could accept large errors in tiny sections.
    matrix_scale=float(np.max(np.abs(matrix)))
    if not np.allclose(matrix,matrix.T,rtol=1e-6,atol=matrix_scale*1e-9):return False
    moments=section.get('principal_second_moments_mm4')
    moduli=section.get('principal_section_moduli_mm3')
    if any(not isinstance(values,(list,tuple)) or len(values)!=2 or any(not numeric(x) or x<=0 for x in values)
           for values in (moments,moduli)):return False
    if not np.allclose(vectors@vectors.T,np.eye(2),rtol=1e-6,atol=1e-6):return False
    eigenvalues=np.linalg.eigvalsh(matrix)
    if (eigenvalues<=0).any() or not np.isfinite(eigenvalues).all():return False
    if not np.allclose(eigenvalues,moments,rtol=1e-6,atol=0):return False
    if not np.allclose(vectors@matrix,np.asarray(moments)[:,None]*vectors,rtol=1e-6,atol=matrix_scale*1e-9):return False
    distances=np.max(np.abs(points@vectors.T),axis=0)
    if (distances<=0).any():return False
    expected_moduli=np.asarray(moments)/distances
    if not np.allclose(expected_moduli,moduli,rtol=1e-6,atol=0):return False
    responses=np.linalg.solve(matrix,points.T).T
    maximum=float(np.max(np.linalg.norm(responses,axis=1)))
    minimum=section.get('minimum_all_direction_section_modulus_mm3')
    if not numeric(minimum) or minimum<=0 or maximum<=0 or not isfinite(maximum):return False
    if not isclose(minimum,1/maximum,rel_tol=1e-6,abs_tol=0):return False
    gradient=section.get('critical_stress_gradient_uv')
    moment=section.get('critical_bending_moment_direction_uv')
    if any(not isinstance(values,(list,tuple)) or len(values)!=2 or any(not numeric(x) for x in values)
           for values in (gradient,moment)):return False
    g=np.asarray(gradient);resultant=matrix@g;scale=float(np.linalg.norm(resultant))
    if scale<=0 or not isfinite(scale) or not isclose(float(g@g),1,rel_tol=1e-6,abs_tol=1e-6):return False
    # Any tied extreme direction is valid; don't require a particular corner.
    if not isclose(float(np.max(np.abs(points@g)))/scale,maximum,rel_tol=1e-6,abs_tol=0):return False
    expected_moment=np.asarray([resultant[1],-resultant[0]])/scale
    return bool(np.allclose(expected_moment,moment,rtol=1e-6,atol=1e-6))


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


def valid_component_selection(section):
    """Verify the selected polygon proof, never accept a relabelled plate union."""
    try:
        count=section.get('component_count')
        if not isinstance(count,int) or isinstance(count,bool) or not 1<=count<=MAX_SECTION_COMPONENTS:return False
        if section.get('normal_axis')!='Z' or section.get('component_selection_basis')!=COMPONENT_SELECTION:return False
        axial=section.get('axial');bending=section.get('bending')
        if not isinstance(axial,dict) or axial!=bending or axial.get('component_count')!=1:return False
        if axial.get('reference_component_count')!=count or axial.get('component_selection_basis')!=COMPONENT_SELECTION:return False
        limits=section.get('component_selection_limits')
        if limits!=axial.get('component_selection_limits') or not isinstance(limits,list) or not limits:return False
        if any(not isinstance(limit,str) or len(limit)>256 for limit in limits):return False
        bounds=section.get('selected_component_bounds_uv_mm');centroid=section.get('selected_component_centroid_uv_mm')
        if bounds!=axial.get('selected_component_bounds_uv_mm') or centroid!=axial.get('centroid_uv_mm') or centroid!=axial.get('selected_component_centroid_uv_mm'):return False
        if not isinstance(bounds,list) or len(bounds)!=2 or not isinstance(centroid,list) or len(centroid)!=2:return False
        center=[finite_number(value) for value in centroid]
        support=axial.get('boundary_support_vertices_relative_uv_mm')
        if not isinstance(support,list) or not 3<=len(support)<=MAX_SUPPORT_VERTICES:return False
        for index in range(2):
            if not isinstance(bounds[index],list) or len(bounds[index])!=2:return False
            lo,hi=[finite_number(value) for value in bounds[index]]
            values=[finite_number(point[index])+center[index] for point in support]
            if lo>=hi or not isclose(lo,min(values),rel_tol=1e-9,abs_tol=1e-7) or not isclose(hi,max(values),rel_tol=1e-9,abs_tol=1e-7):return False
        return True
    except (AttributeError,ValueError,TypeError,KeyError,IndexError,OverflowError):return False


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
            if candidate.get('kind') in COMPONENT_KINDS:
                gaps=candidate.get('assessment_gaps',[])
                if isinstance(gaps,list):entry['gaps'].extend(gap for gap in gaps[:64] if isinstance(gap,str) and len(gap)<=256)
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
            component=candidate.get('kind') in COMPONENT_KINDS
            if component and (axis!=2 or axial!=bending):
                entry['gaps'].append('COMPONENT_REFERENCE_COMMON_Z_PLANE_REQUIRED');continue
            u=(axis+1)%3;v=(axis+2)%3
            entry.update(axis=axis,u=u,v=v,bounds=normalized)
            for name,station in (('axial',axial),('bending',bending)):
                cut_key=(axis,station,tuple(normalized[u]),tuple(normalized[v]),component)
                if cut_key not in self.cuts:
                    self.cuts[cut_key]={'axis':axis,'u':u,'v':v,'station':station,'bounds':normalized,
                                         'pieces':set(),'tools':set(),'members':set(),'gaps':set(),
                                         'component_selection':component,'piece_tools':{} if component else None}
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
            if cut['component_selection']:
                cut['piece_tools'].setdefault(piece,set()).add(tool)
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
                    pieces=list(cut['pieces'])
                    shapes=[Polygon(piece) if cut['axis']==2 else box(piece[0],piece[2],piece[1],piece[3])
                            for piece in pieces]
                    shape=union_all(shapes,grid_size=0)
                    tools=cut['tools']
                    if cut['component_selection']:
                        polygons=list(shape.geoms) if shape.geom_type=='MultiPolygon' else [shape]
                        if len(polygons)>MAX_SECTION_COMPONENTS:
                            raise UnsupportedGeometry('LOCAL_SECTION_GEOMETRY_BUDGET_EXCEEDED')
                        if sum(len(ring.coords)-1 for polygon in polygons if polygon.geom_type=='Polygon'
                               for ring in (polygon.exterior,*polygon.interiors))>MAX_UNION_VERTICES:
                            raise UnsupportedGeometry('LOCAL_SECTION_GEOMETRY_BUDGET_EXCEEDED')
                        choices=[(_plane_properties(polygon),polygon) for polygon in polygons]
                        properties,selected=min(choices,key=lambda item:(item[0]['minimum_all_direction_section_modulus_mm3'],
                                                                         item[1].bounds))
                        tools=set()
                        for piece,road in zip(pieces,shapes):
                            if selected.intersects(road) and selected.intersection(road).area>0:
                                tools.update(cut['piece_tools'][piece])
                        x0,y0,x1,y1=selected.bounds
                        properties.update(reference_component_count=len(polygons),
                            selected_component_bounds_uv_mm=[[x0,x1],[y0,y1]],
                            selected_component_centroid_uv_mm=list(selected.centroid.coords[0]),
                            component_selection_basis=COMPONENT_SELECTION,
                            component_selection_limits=['CONNECTED_2D_ROAD_POLYGON_NOT_SOURCE_OBJECT_ID',
                                'NO_WHOLE_PART_LOAD_PATH_OR_WELD_STRENGTH_VERIFICATION'])
                    else:properties=_plane_properties(shape)
                    properties.update(station_mm=cut['station'],tools=sorted(tools),
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
                if entry['candidate'].get('kind') in COMPONENT_KINDS:
                    value.update(component_count=local['bending']['reference_component_count'],
                                 **{key:local['bending'][key] for key in ('selected_component_bounds_uv_mm',
                                    'selected_component_centroid_uv_mm','component_selection_basis','component_selection_limits')})
            results[key]=value
        return results
