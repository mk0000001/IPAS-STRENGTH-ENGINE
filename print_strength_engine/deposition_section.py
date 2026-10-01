"""Bounded unions of declared rectangular road prisms, not printed weld geometry."""
from collections import deque
from math import fsum,isfinite
from struct import error as StructError

MAX_SEGMENTS=200_000
MAX_STATIONS=256
MAX_SECTION_CELLS=250_000
MAX_CELL_WORK=2_000_000
COORDINATE_TOLERANCE_MM=1e-7


class UnsupportedGeometry(Exception):
    pass


def finite_number(value,limit=1e6):
    if isinstance(value,bool) or not isinstance(value,(int,float)):
        raise ValueError('FINITE_JSON_NUMBER_REQUIRED')
    value=float(value)
    if not isfinite(value) or abs(value)>limit:raise ValueError('FINITE_JSON_NUMBER_REQUIRED')
    return value


def vector(value):
    if not isinstance(value,(list,tuple)) or len(value)!=3:raise ValueError('THREE_COORDINATES_REQUIRED')
    return [finite_number(item) for item in value]


def road_boxes(geometry):
    if not isinstance(geometry,dict) or geometry.get('complete') is not True or \
       geometry.get('sampled') is not False or geometry.get('provenance')!='GCODE_WIDTH_HEIGHT_ASSUMPTION':
        raise UnsupportedGeometry('COMPLETE_DEPOSITION_GEOMETRY_REQUIRED')
    segments=geometry.get('segments')
    if segments is None:raise UnsupportedGeometry('COMPLETE_DEPOSITION_GEOMETRY_REQUIRED')
    boxes=[];tools=set();count=0
    try:
        for index,row in enumerate(segments):
            count=index+1
            if index>=MAX_SEGMENTS:raise UnsupportedGeometry('DEPOSITION_SEGMENT_BUDGET_EXCEEDED')
            if not isinstance(row,dict):raise UnsupportedGeometry('INVALID_DEPOSITION_RECORD')
            if row.get('role','model') not in ('model','bridge',0,2):
                raise UnsupportedGeometry('MODEL_ONLY_DEPOSITION_REQUIRED')
            if 'width_mm' not in row or 'height_mm' not in row:
                raise UnsupportedGeometry('DECLARED_ROAD_DIMENSIONS_REQUIRED')
            start=vector(row.get('start'));end=vector(row.get('end'))
            width=finite_number(row['width_mm']);height=finite_number(row['height_mm'])
            if not .001<=width<=10 or not .001<=height<=10:raise UnsupportedGeometry('INVALID_ROAD_DIMENSIONS')
            if start[2]!=end[2]:raise UnsupportedGeometry('NONPLANAR_DEPOSITION_UNSUPPORTED')
            if start[:2]==end[:2]:continue
            # A rotated bounding box would fill gaps and invent connections.
            if start[0]!=end[0] and start[1]!=end[1]:
                raise UnsupportedGeometry('OBLIQUE_ROAD_GEOMETRY_UNSUPPORTED')
            tool=row.get('tool')
            if isinstance(tool,bool) or not isinstance(tool,int) or tool<0:
                raise UnsupportedGeometry('DEPOSITION_TOOL_REQUIRED')
            tools.add(tool)
            if len(tools)>1:raise UnsupportedGeometry('MULTITOOL_STIFFNESS_UNVERIFIED')
            if start[0]!=end[0]:
                box=[sorted((start[0],end[0])),[start[1]-width/2,start[1]+width/2]]
            else:
                box=[[start[0]-width/2,start[0]+width/2],sorted((start[1],end[1]))]
            box.append([start[2]-height,start[2]])
            boxes.append(box)
    except (TypeError,ValueError,KeyError,EOFError,OSError,StructError) as error:
        raise UnsupportedGeometry('INVALID_DEPOSITION_RECORD') from error
    if geometry.get('count') is not None and geometry['count']!=count:
        raise UnsupportedGeometry('DEPOSITION_RECORD_COUNT_MISMATCH')
    if not boxes:raise UnsupportedGeometry('NO_DEPOSITED_MODEL_GEOMETRY')
    # Merge only round-off scale boundaries, never by chained proximity:
    # every cluster's total span is bounded. Float64 sidecars are preferred;
    # lost float32 precision at large coordinates must not widen this tolerance.
    for axis in range(3):
        coordinates=sorted({x for box in boxes for x in box[axis]})
        clusters=[]
        for value in coordinates:
            if not clusters or value-clusters[-1][0]>COORDINATE_TOLERANCE_MM:
                clusters.append([value])
            else:clusters[-1].append(value)
        aliases={value:fsum(cluster)/len(cluster) for cluster in clusters for value in cluster}
        for box in boxes:
            box[axis]=[aliases[value] for value in box[axis]]
            if box[axis][0]>=box[axis][1]:raise UnsupportedGeometry('DEGENERATE_ROAD_GEOMETRY')
    return boxes


def _connected(cells):
    if not cells:return False
    remaining=set(cells);queue=deque([remaining.pop()])
    while queue:
        i,j=queue.popleft()
        for neighbor in ((i-1,j),(i+1,j),(i,j-1),(i,j+1)):
            if neighbor in remaining:remaining.remove(neighbor);queue.append(neighbor)
    return not remaining


def _section_cells(boxes,axis,station,u,v,ui,vi):
    cells=set();work=0
    for box in boxes:
        if box[axis][0]<station<box[axis][1]:
            left,right=ui[box[u][0]],ui[box[u][1]]
            bottom,top=vi[box[v][0]],vi[box[v][1]]
            work+=(right-left)*(top-bottom)
            if work>MAX_CELL_WORK:raise UnsupportedGeometry('DEPOSITION_CELL_BUDGET_EXCEEDED')
            cells.update((i,j) for i in range(left,right) for j in range(bottom,top))
    if not _connected(cells):raise UnsupportedGeometry('DISCONNECTED_SECTION')
    return cells,work


def _properties(cells,us,vs):
    rectangles=[(us[i],us[i+1],vs[j],vs[j+1]) for i,j in sorted(cells)]
    areas=[(b-a)*(d-c) for a,b,c,d in rectangles];area=fsum(areas)
    cu=fsum(a*(r[0]+r[1])/2 for a,r in zip(areas,rectangles))/area
    cv=fsum(a*(r[2]+r[3])/2 for a,r in zip(areas,rectangles))/area
    c00=fsum(a*((r[1]-r[0])**2/12+((r[0]+r[1])/2-cu)**2) for a,r in zip(areas,rectangles))
    c11=fsum(a*((r[3]-r[2])**2/12+((r[2]+r[3])/2-cv)**2) for a,r in zip(areas,rectangles))
    c01=fsum(a*((r[0]+r[1])/2-cu)*((r[2]+r[3])/2-cv) for a,r in zip(areas,rectangles))
    return {'area_mm2':area,'centroid_uv_mm':[cu,cv],
            'coordinate_second_moment_mm4':[[c00,c01],[c01,c11]],'cell_count':len(cells)},rectangles


def prismatic_section(geometry,case):
    """Check every prism boundary; coordinate compression preserves real gaps."""
    boxes=road_boxes(geometry)
    bounds=[[min(b[i][0] for b in boxes),max(b[i][1] for b in boxes)] for i in range(3)]
    fixed=case['fixed_region_mm'];point=case['load_point_mm']
    # A supported slender beam's material length exceeds every transverse
    # extent. Empty fixture space must not rotate its inferred longitudinal axis.
    axis=max(range(3),key=lambda i:bounds[i][1]-bounds[i][0]);u=(axis+1)%3;v=(axis+2)%3
    epsilon=COORDINATE_TOLERANCE_MM
    if abs(point[axis]-bounds[axis][1])<=epsilon:
        sign=1;face=fixed[axis][1]
        if fixed[axis][0]>bounds[axis][0]+epsilon:raise UnsupportedGeometry('END_FIXTURE_REQUIRED')
    elif abs(point[axis]-bounds[axis][0])<=epsilon:
        sign=-1;face=fixed[axis][0]
        if fixed[axis][1]<bounds[axis][1]-epsilon:raise UnsupportedGeometry('END_FIXTURE_REQUIRED')
    else:raise UnsupportedGeometry('END_POINT_LOAD_REQUIRED')
    if not bounds[axis][0]<face<bounds[axis][1]:raise UnsupportedGeometry('FIXTURE_MUST_INTERSECT_MODEL')
    if any(fixed[i][0]>bounds[i][0]+epsilon or fixed[i][1]<bounds[i][1]-epsilon for i in (u,v)):
        raise UnsupportedGeometry('FULL_SECTION_FIXTURE_REQUIRED')
    span=abs(point[axis]-face)
    if span<5*max(bounds[i][1]-bounds[i][0] for i in (u,v)):
        raise UnsupportedGeometry('SLENDER_BEAM_MODEL_NOT_APPLICABLE')
    # Include the clamped part too: a disconnected body inside the fixture box
    # must not make an unclamped free beam appear anchored at the selected face.
    lo,hi=bounds[axis]
    stations=sorted({lo,hi}|{x for box in boxes for x in box[axis] if lo<x<hi})
    if len(stations)>MAX_STATIONS+1:raise UnsupportedGeometry('DEPOSITION_STATION_BUDGET_EXCEEDED')
    if len(boxes)*(len(stations)-1)>MAX_CELL_WORK:
        raise UnsupportedGeometry('DEPOSITION_SCAN_BUDGET_EXCEEDED')
    us=sorted({x for b in boxes for x in b[u]});vs=sorted({x for b in boxes for x in b[v]})
    if (len(us)-1)*(len(vs)-1)>MAX_SECTION_CELLS:raise UnsupportedGeometry('DEPOSITION_SECTION_BUDGET_EXCEEDED')
    ui={x:i for i,x in enumerate(us)};vi={x:i for i,x in enumerate(vs)}
    previous=None;work=0
    for left,right in zip(stations,stations[1:]):
        cells,operations=_section_cells(boxes,axis,(left+right)/2,u,v,ui,vi)
        work+=operations
        if work>MAX_CELL_WORK:raise UnsupportedGeometry('DEPOSITION_CELL_BUDGET_EXCEEDED')
        if previous is not None and cells!=previous:raise UnsupportedGeometry('NONPRISMATIC_GEOMETRY')
        previous=cells
    properties,rectangles=_properties(previous,us,vs)
    if not any(a-epsilon<=point[u]<=b+epsilon and c-epsilon<=point[v]<=d+epsilon for a,b,c,d in rectangles):
        raise UnsupportedGeometry('LOAD_POINT_NOT_ON_DEPOSITED_SECTION')
    properties.update({'plane_axes':['XYZ'[u],'XYZ'[v]],'station_mm':face,
        'geometry_basis':'UNION_OF_DECLARED_RECTANGULAR_ROAD_ENVELOPES',
        'section_geometry_status':'CONNECTED_PRISMATIC_ROAD_ENVELOPE',
        'checked_intervals':len(stations)-1,'bonded_contact_area_mm2':None,
        'coordinate_tolerance_mm':COORDINATE_TOLERANCE_MM,
        'printed_void_geometry_measured':False,'solid_infill_assumed':False})
    return properties,rectangles,axis,u,v,sign,face,span
