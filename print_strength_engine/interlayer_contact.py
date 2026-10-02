"""Bounded local intersections of adjacent declared-road footprints.

The G-code width/height rectangular-prism assumption is geometric evidence only.
An overlap of one is not a successful weld test. Molecular adhesion, real bead
contact, temperature history, peeling, shear strength and failure load are unknown.
"""
from math import hypot,isfinite
from .deposition_section import finite_number,vector,UnsupportedGeometry

VERSION='LOCAL_DECLARED_INTERLAYER_CONTACT_V1'
PROVENANCE='GCODE_WIDTH_HEIGHT_ASSUMPTION'
SCOPE='LOCAL_DECLARED_ROAD_INTERLAYER_WINDOW'
MAX_CANDIDATES=6
MAX_RECORDS=100_000
MAX_TOTAL_RECORDS=250_000
MAX_LAYERS=2048
MAX_UNION_VERTICES=1_000_000
PLANE_TOLERANCE_MM=1e-4
LOW_OVERLAP_RATIO=.5  # Geometric screening threshold, never a strength factor.


def _components(shape):
    if shape.is_empty:return 0
    return len(shape.geoms) if shape.geom_type=='MultiPolygon' else 1 if shape.geom_type=='Polygon' else 0


def valid_contact_descriptor(value,expected_bounds):
    try:return _valid_contact_descriptor(value,expected_bounds)
    except (KeyError,TypeError,ValueError,OverflowError,RecursionError):return False


def _valid_contact_descriptor(value,expected_bounds):
    """Validate cached geometry claims without reconstructing source or welding."""
    def number(item,positive=False):
        return isinstance(item,(int,float)) and not isinstance(item,bool) and isfinite(item) and (not positive or item>0)
    def integer(item,maximum=MAX_TOTAL_RECORDS):
        return isinstance(item,int) and not isinstance(item,bool) and 0<=item<=maximum
    def tools(items,empty=False):
        return isinstance(items,list) and (empty or bool(items)) and all(integer(tool) for tool in items) and len(set(items))==len(items)
    def equal_number(left,right):return number(left) and number(right) and abs(left-right)<=1e-6*max(1.,abs(left),abs(right))
    if not isinstance(value,dict) or value.get('version')!=VERSION:return False
    if value.get('provenance')!=PROVENANCE or value.get('scope')!=SCOPE:return False
    if value.get('normal_axis')!='Z' or value.get('plane_axes')!=['X','Y'] or value.get('estimated_not_measured') is not True:return False
    if value.get('sampled') is not False or any(value.get(field) is not False for field in ('actual_bond_measured','molecular_weld_quality_verified','is_failure_prediction')):return False
    gaps=value.get('assessment_gaps')
    if not isinstance(gaps,list) or any(not isinstance(gap,str) or not gap for gap in gaps):return False
    if value.get('status')=='WITHHELD':
        if value.get('complete') is not False or not gaps:return False
        if value.get('section_window_bounds_mm')==expected_bounds:return True
        return value.get('section_window_bounds_mm') is None and 'LOCAL_SECTION_WINDOW_REQUIRED' in gaps
    if value.get('section_window_bounds_mm')!=expected_bounds:return False
    if not isinstance(expected_bounds,(list,tuple)) or len(expected_bounds)!=3:return False
    if any(not isinstance(pair,(list,tuple)) or len(pair)!=2 or not all(number(item) for item in pair) or pair[0]>=pair[1] for pair in expected_bounds):return False
    if value.get('status')!='COMPLETE' or value.get('complete') is not True or gaps:return False
    if value.get('geometry_basis')!='INTERSECTION_OF_ADJACENT_DECLARED_RECTANGULAR_ROAD_FOOTPRINTS':return False
    if value.get('plane_tolerance_mm')!=PLANE_TOLERANCE_MM or value.get('low_overlap_screening_threshold')!=LOW_OVERLAP_RATIO:return False
    limits=value.get('limits')
    if not isinstance(limits,dict) or limits!={'maximum_retained_records_per_candidate':MAX_RECORDS,
        'maximum_total_retained_records':MAX_TOTAL_RECORDS,'maximum_layers_per_candidate':MAX_LAYERS,'maximum_union_vertices':MAX_UNION_VERTICES}:return False
    if not integer(value.get('retained_records'),MAX_RECORDS) or not integer(value.get('source_records_scanned'),2**53):return False
    if value['retained_records']>value['source_records_scanned']:return False
    layers=value.get('layers');interfaces=value.get('interfaces')
    if not isinstance(layers,list) or len(layers)>MAX_LAYERS or not isinstance(interfaces,list):return False
    if value.get('layer_count')!=len(layers) or value.get('interfaces_checked')!=len(interfaces) or len(interfaces)!=max(0,len(layers)-1):return False
    crop_area=(expected_bounds[0][1]-expected_bounds[0][0])*(expected_bounds[1][1]-expected_bounds[1][0])
    previous_top=None
    for row in layers:
        if not isinstance(row,dict) or row.get('layer_number') is not None and not integer(row['layer_number'],2**53):return False
        if not all(number(row.get(field),field in ('area_mm2','height_mm','max_declared_width_mm')) for field in ('top_z_mm','bottom_z_mm','height_mm','area_mm2','max_declared_width_mm')):return False
        if row['height_mm']>10 or row['max_declared_width_mm']>10 or row['bottom_z_mm']>=row['top_z_mm']:return False
        if row['top_z_mm']<=expected_bounds[2][0] or row['bottom_z_mm']>=expected_bounds[2][1]:return False
        if abs(row['top_z_mm']-row['bottom_z_mm']-row['height_mm'])>PLANE_TOLERANCE_MM:return False
        if previous_top is not None and row['top_z_mm']<=previous_top:return False
        previous_top=row['top_z_mm']
        if row['area_mm2']>crop_area+1e-6:return False
        xy=row.get('xy_bounds_mm')
        if not isinstance(xy,list) or len(xy)!=4 or not all(number(item) for item in xy) or xy[0]>=xy[2] or xy[1]>=xy[3]:return False
        if any(xy[i]<expected_bounds[i][0]-1e-6 or xy[i+2]>expected_bounds[i][1]+1e-6 for i in (0,1)):return False
        if not integer(row.get('component_count'),MAX_UNION_VERTICES) or row['component_count']<1 or not tools(row.get('tools')):return False
        if not integer(row.get('retained_records'),MAX_RECORDS) or not integer(row.get('raw_record_count'),2**53) or not isinstance(row.get('z_crop_boundary'),bool):return False
        if row['z_crop_boundary']!=(row['bottom_z_mm']<expected_bounds[2][0]-PLANE_TOLERANCE_MM or row['top_z_mm']>expected_bounds[2][1]+PLANE_TOLERANCE_MM):return False
    flags=('adjacent_plane_verified','consecutive_source_layers','both_footprints_substantial','both_footprints_have_extent',
           'has_both_sided_layer_depth','z_crop_boundary','crop_robust','qualifies_for_diagnostic','persistent_low_overlap')
    for index,row in enumerate(interfaces):
        if not isinstance(row,dict):return False
        lower,upper=layers[index:index+2]
        if row.get('lower_layer_number')!=lower['layer_number'] or row.get('upper_layer_number')!=upper['layer_number']:return False
        if not all(isinstance(row.get(field),bool) for field in flags):return False
        numeric=('z_mm','lower_area_mm2','upper_area_mm2','overlap_area_mm2','upper_overlap_ratio','lower_overlap_ratio',
                 'smaller_footprint_overlap_ratio','geometric_vertical_gap_mm','minimum_qualifying_area_mm2',
                 'lower_depth_mm','upper_depth_mm','interior_smaller_area_mm2')
        if not all(number(row.get(field)) for field in numeric):return False
        if not equal_number(row['z_mm'],lower['top_z_mm']) or not equal_number(row['lower_area_mm2'],lower['area_mm2']) or not equal_number(row['upper_area_mm2'],upper['area_mm2']):return False
        if row['overlap_area_mm2']<0 or row['overlap_area_mm2']>min(lower['area_mm2'],upper['area_mm2'])+1e-6:return False
        for field,area in [('upper_overlap_ratio',upper['area_mm2']),('lower_overlap_ratio',lower['area_mm2']),('smaller_footprint_overlap_ratio',min(lower['area_mm2'],upper['area_mm2']))]:
            if not 0<=row[field]<=1+1e-7 or not equal_number(row[field],row['overlap_area_mm2']/area):return False
        inner=row.get('interior_smaller_overlap_ratio')
        if inner is not None and (not number(inner) or not 0<=inner<=1+1e-7):return False
        gap=upper['bottom_z_mm']-lower['top_z_mm']
        if not equal_number(row['geometric_vertical_gap_mm'],gap) or row['adjacent_plane_verified']!=(abs(gap)<=PLANE_TOLERANCE_MM):return False
        max_width=max(lower['max_declared_width_mm'],upper['max_declared_width_mm']);minimum_area=max(1.,4*max_width**2)
        if not equal_number(row['minimum_qualifying_area_mm2'],minimum_area) or row['both_footprints_substantial']!=(min(lower['area_mm2'],upper['area_mm2'])>=minimum_area):return False
        extents=[(item['xy_bounds_mm'][2]-item['xy_bounds_mm'][0],item['xy_bounds_mm'][3]-item['xy_bounds_mm'][1]) for item in (lower,upper)]
        if row['both_footprints_have_extent']!=all(min(extent)>=max(.02,2*max_width) and max(extent)>=3*max_width for extent in extents):return False
        lower_depth=lower['top_z_mm']-layers[0]['bottom_z_mm'];upper_depth=layers[-1]['top_z_mm']-upper['bottom_z_mm']
        if not equal_number(row['lower_depth_mm'],lower_depth) or not equal_number(row['upper_depth_mm'],upper_depth):return False
        depth=index>=1 and index+2<len(layers) and min(lower_depth,upper_depth)>=2*max(lower['height_mm'],upper['height_mm'])-PLANE_TOLERANCE_MM
        if row['has_both_sided_layer_depth']!=depth or row['z_crop_boundary']!=(lower['z_crop_boundary'] or upper['z_crop_boundary']):return False
        interior_area=row['interior_smaller_area_mm2']
        if interior_area<0 or interior_area>min(lower['area_mm2'],upper['area_mm2'])+1e-6 or (interior_area==0)!=(inner is None):return False
        crop_robust=interior_area>=minimum_area and inner is not None and (row['smaller_footprint_overlap_ratio']>LOW_OVERLAP_RATIO or inner<=LOW_OVERLAP_RATIO+1e-8)
        if row['crop_robust']!=crop_robust:return False
        qualifies=row['both_footprints_substantial'] and row['both_footprints_have_extent'] and depth and not row['z_crop_boundary'] and crop_robust
        if row['qualifies_for_diagnostic']!=qualifies:return False
        if row['qualifies_for_diagnostic'] and (not all(row[field] for field in ('both_footprints_substantial','both_footprints_have_extent','has_both_sided_layer_depth','crop_robust')) or row['z_crop_boundary']):return False
        if row['qualifies_for_diagnostic'] and not (index>=1 and index+2<len(layers)):return False
        if not all(integer(row.get(field),MAX_UNION_VERTICES) for field in ('lower_component_count','upper_component_count','overlap_component_count')):return False
        if row.get('lower_tools')!=lower['tools'] or row.get('upper_tools')!=upper['tools']:return False
        if row['lower_component_count']!=lower['component_count'] or row['upper_component_count']!=upper['component_count']:return False
        if row['consecutive_source_layers']!=(lower['layer_number'] is None or upper['layer_number'] is None or upper['layer_number']==lower['layer_number']+1):return False
    for index,row in enumerate(interfaces):
        neighbors=interfaces[max(0,index-1):index]+interfaces[index+1:index+2]
        low=row['qualifies_for_diagnostic'] and row['smaller_footprint_overlap_ratio']<LOW_OVERLAP_RATIO
        persistent=low and any(other['qualifies_for_diagnostic'] and other['smaller_footprint_overlap_ratio']<LOW_OVERLAP_RATIO for other in neighbors)
        if row['persistent_low_overlap']!=persistent:return False
    eligible=[row for row in interfaces if row['qualifies_for_diagnostic']]
    if value.get('qualifying_interface_count')!=len(eligible):return False
    worst=min(eligible,key=lambda row:(row['smaller_footprint_overlap_ratio'],row['overlap_area_mm2'])) if eligible else None
    if value.get('worst_qualifying_interface')!=worst:return False
    if value.get('geometric_overlap_area_mm2')!=(worst['overlap_area_mm2'] if worst else None):return False
    if value.get('minimum_smaller_footprint_overlap_ratio')!=(worst['smaller_footprint_overlap_ratio'] if worst else None):return False
    observations=value.get('observations')
    if not isinstance(observations,list) or len(observations)>2*len(interfaces):return False
    valid_kinds={'DECLARED_VERTICAL_GAP','OVERLAPPING_DECLARED_LAYER_INTERVALS','NO_DECLARED_LAYER_OVERLAP','LOW_DECLARED_LAYER_OVERLAP'}
    expected_observations=[]
    for index,row in enumerate(interfaces):
        if not row['qualifies_for_diagnostic']:continue
        if row['geometric_vertical_gap_mm']>PLANE_TOLERANCE_MM:kind='DECLARED_VERTICAL_GAP'
        elif row['geometric_vertical_gap_mm']<-PLANE_TOLERANCE_MM:kind='OVERLAPPING_DECLARED_LAYER_INTERVALS'
        elif row['persistent_low_overlap']:kind='NO_DECLARED_LAYER_OVERLAP' if row['overlap_area_mm2']<=1e-10 else 'LOW_DECLARED_LAYER_OVERLAP'
        else:continue
        expected_observations.append({'kind':kind,'interface_index':index})
    if observations!=expected_observations:return False
    for observation in observations:
        if not isinstance(observation,dict) or observation.get('kind') not in valid_kinds or not integer(observation.get('interface_index'),MAX_LAYERS):return False
        index=observation['interface_index']
        if index>=len(interfaces) or not interfaces[index]['qualifies_for_diagnostic']:return False
        row=interfaces[index]
        if observation['kind']=='DECLARED_VERTICAL_GAP' and row['geometric_vertical_gap_mm']<=PLANE_TOLERANCE_MM:return False
        if observation['kind']=='OVERLAPPING_DECLARED_LAYER_INTERVALS' and row['geometric_vertical_gap_mm']>=-PLANE_TOLERANCE_MM:return False
        if observation['kind'] in ('NO_DECLARED_LAYER_OVERLAP','LOW_DECLARED_LAYER_OVERLAP') and (not row['persistent_low_overlap'] or not row['adjacent_plane_verified']):return False
    return tools(value.get('tools'),empty=not bool(layers)) and value['tools']==sorted({tool for row in layers for tool in row['tools']})


class StreamingInterlayerContact:
    """Keep only <=6 crop windows during the same full source scan as sections."""
    def __init__(self,candidates,*,cancelled=None,max_records=MAX_RECORDS,max_total_records=MAX_TOTAL_RECORDS):
        candidates=list(candidates)
        if len(candidates)>MAX_CANDIDATES:raise ValueError('LOCAL_CONTACT_CANDIDATE_LIMIT')
        self.entries={};self.source_records_scanned=0;self.total_records=0;self.gaps=set();self.cancelled=cancelled
        self.max_records=min(MAX_RECORDS,max(1,int(max_records)))
        self.max_total_records=min(MAX_TOTAL_RECORDS,max(1,int(max_total_records)))
        for candidate in candidates:
            key=str(candidate.get('region_id') or '')
            if not key or key in self.entries:raise ValueError('UNIQUE_LOCAL_REGION_ID_REQUIRED')
            entry={'layers':{},'gaps':set(),'retained_records':0,'candidate':candidate};self.entries[key]=entry
            try:
                bounds=candidate.get('section_window_bounds_mm')
                if not isinstance(bounds,(list,tuple)) or len(bounds)!=3:raise ValueError()
                normalized=[]
                for pair in bounds:
                    if not isinstance(pair,(list,tuple)) or len(pair)!=2:raise ValueError()
                    lo,hi=[finite_number(value) for value in pair]
                    if lo>=hi:raise ValueError()
                    normalized.append([lo,hi])
                entry['bounds']=normalized
            except (ValueError,TypeError):entry['gaps'].add('LOCAL_SECTION_WINDOW_REQUIRED')

    def check_cancelled(self):
        if self.cancelled and self.cancelled():raise RuntimeError('ANALYSIS_CANCELLED')

    def segment(self,start,end,width,height,tool,*,layer_number=None):
        self.source_records_scanned+=1
        if self.source_records_scanned%1024==1:self.check_cancelled()
        try:
            start=vector(start);end=vector(end)
            if width is None or height is None:raise UnsupportedGeometry('DECLARED_ROAD_DIMENSIONS_REQUIRED')
            width=finite_number(width);height=finite_number(height)
            if not .001<=width<=10 or not .001<=height<=10:raise UnsupportedGeometry('INVALID_ROAD_DIMENSIONS')
            if abs(start[2]-end[2])>PLANE_TOLERANCE_MM:raise UnsupportedGeometry('NONPLANAR_DEPOSITION_UNSUPPORTED')
            if isinstance(tool,bool) or not isinstance(tool,int) or tool<0:raise UnsupportedGeometry('DEPOSITION_TOOL_REQUIRED')
            if layer_number is not None and (isinstance(layer_number,bool) or not isinstance(layer_number,int) or layer_number<0):
                raise UnsupportedGeometry('DEPOSITION_LAYER_REQUIRED')
        except ValueError:self.gaps.add('INVALID_DEPOSITION_RECORD');return
        except UnsupportedGeometry as error:self.gaps.add(str(error));return
        dx=end[0]-start[0];dy=end[1]-start[1];length=hypot(dx,dy)
        if not length:return
        broad=[[min(start[i],end[i])-width/2,max(start[i],end[i])+width/2] for i in (0,1)]
        bottom=end[2]-height;top=end[2]
        possible=[]
        for key,entry in self.entries.items():
            if entry['gaps']:continue
            bounds=entry['bounds']
            if top<=bounds[2][0] or bottom>=bounds[2][1]:continue
            if any(broad[i][1]<=bounds[i][0] or broad[i][0]>=bounds[i][1] for i in (0,1)):continue
            possible.append(entry)
        if not possible:return
        nx=-dy/length*width/2;ny=dx/length*width/2
        footprint=((start[0]+nx,start[1]+ny),(end[0]+nx,end[1]+ny),
                   (end[0]-nx,end[1]-ny),(start[0]-nx,start[1]-ny))
        for entry in possible:
            layers=entry['layers'];bounds=entry['bounds'];number=layer_number
            # Real parser layer ids separate repeated-height/simultaneous objects.
            # Public callers without ids retain the actual numeric top plane.
            key=(number,top)
            if key not in layers:
                if len(layers)>=MAX_LAYERS:entry['gaps'].add('INTERLAYER_GEOMETRY_BUDGET_EXCEEDED');continue
                layers[key]={'layer_number':number,'top_z_mm':top,'bottom_min':bottom,'bottom_max':bottom,
                             'width_max':width,'height_max':height,'pieces':set(),'tools':set(),
                             'z_crop_boundary':False,'raw_record_count':0}
            row=layers[key]
            row['bottom_min']=min(row['bottom_min'],bottom);row['bottom_max']=max(row['bottom_max'],bottom)
            row['width_max']=max(row['width_max'],width);row['height_max']=max(row['height_max'],height)
            row['tools'].add(tool);row['raw_record_count']+=1
            row['z_crop_boundary']|=bottom<bounds[2][0]-PLANE_TOLERANCE_MM or top>bounds[2][1]+PLANE_TOLERANCE_MM
            if footprint in row['pieces']:continue
            if entry['retained_records']>=self.max_records or self.total_records>=self.max_total_records:
                entry['gaps'].add('INTERLAYER_GEOMETRY_BUDGET_EXCEEDED');entry['layers'].clear();continue
            row['pieces'].add(footprint);entry['retained_records']+=1;self.total_records+=1

    def _finish_entry(self,entry):
        from shapely import union_all
        from shapely.geometry import Polygon,box
        bounds=entry['bounds'];crop=box(bounds[0][0],bounds[1][0],bounds[0][1],bounds[1][1])
        descriptors=[];shapes=[];vertices=0
        for raw in sorted(entry['layers'].values(),key=lambda row:(row['top_z_mm'],row['layer_number'] if row['layer_number'] is not None else -1)):
            self.check_cancelled()
            if raw['bottom_max']-raw['bottom_min']>PLANE_TOLERANCE_MM:
                raise UnsupportedGeometry('INCONSISTENT_DECLARED_LAYER_INTERVAL')
            pieces=list(raw['pieces']);chunks=[]
            for start in range(0,len(pieces),2048):
                self.check_cancelled()
                chunks.append(union_all([Polygon(points) for points in pieces[start:start+2048]]).intersection(crop))
            shape=union_all(chunks)
            if shape.is_empty or shape.area<=0:continue
            if shape.geom_type not in ('Polygon','MultiPolygon'):raise UnsupportedGeometry('UNSUPPORTED_LAYER_FOOTPRINT')
            polygons=list(shape.geoms) if shape.geom_type=='MultiPolygon' else [shape]
            vertices+=sum(len(p.exterior.coords)+sum(len(r.coords) for r in p.interiors) for p in polygons)
            if vertices>MAX_UNION_VERTICES:raise UnsupportedGeometry('INTERLAYER_GEOMETRY_BUDGET_EXCEEDED')
            xy=list(shape.bounds)
            descriptors.append({'layer_number':raw['layer_number'],'top_z_mm':raw['top_z_mm'],
                'bottom_z_mm':raw['bottom_min'],'height_mm':raw['height_max'],'area_mm2':float(shape.area),
                'xy_bounds_mm':xy,'component_count':_components(shape),'tools':sorted(raw['tools']),
                'max_declared_width_mm':raw['width_max'],'retained_records':len(pieces),
                'raw_record_count':raw['raw_record_count'],'z_crop_boundary':bool(raw['z_crop_boundary'])})
            shapes.append(shape)
        interfaces=[]
        for index in range(1,len(descriptors)):
            self.check_cancelled()
            lower=descriptors[index-1];upper=descriptors[index]
            previous=shapes[index-1];current=shapes[index];gap=upper['bottom_z_mm']-lower['top_z_mm']
            adjacent=abs(gap)<=PLANE_TOLERANCE_MM
            intersection=previous.intersection(current);area=float(intersection.area)
            small=min(lower['area_mm2'],upper['area_mm2'])
            ratio=area/small
            max_width=max(lower['max_declared_width_mm'],upper['max_declared_width_mm'])
            min_area=max(1.,4*max_width**2)
            enough_area=small>=min_area
            extents=[(row['xy_bounds_mm'][2]-row['xy_bounds_mm'][0],row['xy_bounds_mm'][3]-row['xy_bounds_mm'][1]) for row in (lower,upper)]
            enough_extent=all(min(extent)>=max(.02,2*max_width) and max(extent)>=3*max_width for extent in extents)
            lower_depth=lower['top_z_mm']-descriptors[0]['bottom_z_mm']
            upper_depth=descriptors[-1]['top_z_mm']-upper['bottom_z_mm']
            enough_depth=index>=2 and index+1<len(descriptors) and min(lower_depth,upper_depth)>=2*max(lower['height_mm'],upper['height_mm'])-PLANE_TOLERANCE_MM
            crop_z=lower['z_crop_boundary'] or upper['z_crop_boundary']
            inner_bounds=(bounds[0][0]+max_width,bounds[1][0]+max_width,bounds[0][1]-max_width,bounds[1][1]-max_width)
            inner_ratio=None;inner_area=0.
            if inner_bounds[0]<inner_bounds[2] and inner_bounds[1]<inner_bounds[3]:
                inner_crop=box(*inner_bounds);inner_lower=previous.intersection(inner_crop);inner_upper=current.intersection(inner_crop)
                inner_area=min(inner_lower.area,inner_upper.area)
                if inner_area>0:inner_ratio=float(inner_lower.intersection(inner_upper).area/inner_area)
            # A loss disappearing when the crop border is removed is a window
            # artifact. Expansion with overlap/smaller=1 is supported growth.
            crop_robust=inner_area>=min_area and inner_ratio is not None and (ratio>LOW_OVERLAP_RATIO or inner_ratio<=LOW_OVERLAP_RATIO+1e-8)
            eligible=enough_area and enough_extent and enough_depth and not crop_z and crop_robust
            number_adjacent=lower['layer_number'] is None or upper['layer_number'] is None or upper['layer_number']==lower['layer_number']+1
            interfaces.append({'z_mm':lower['top_z_mm'],'lower_layer_number':lower['layer_number'],
                'upper_layer_number':upper['layer_number'],'lower_area_mm2':lower['area_mm2'],'upper_area_mm2':upper['area_mm2'],
                'overlap_area_mm2':area,'upper_overlap_ratio':area/upper['area_mm2'],
                'lower_overlap_ratio':area/lower['area_mm2'],'smaller_footprint_overlap_ratio':ratio,
                'geometric_vertical_gap_mm':gap,'adjacent_plane_verified':adjacent,'consecutive_source_layers':number_adjacent,
                'lower_component_count':lower['component_count'],'upper_component_count':upper['component_count'],
                'overlap_component_count':_components(intersection),'lower_tools':lower['tools'],'upper_tools':upper['tools'],
                'minimum_qualifying_area_mm2':min_area,'both_footprints_substantial':enough_area,
                'both_footprints_have_extent':enough_extent,'has_both_sided_layer_depth':enough_depth,
                'lower_depth_mm':lower_depth,'upper_depth_mm':upper_depth,'z_crop_boundary':crop_z,
                'interior_smaller_overlap_ratio':inner_ratio,'interior_smaller_area_mm2':float(inner_area),
                'crop_robust':crop_robust,'qualifies_for_diagnostic':bool(eligible),'persistent_low_overlap':False})
        observations=[]
        for index,row in enumerate(interfaces):
            low=row['qualifies_for_diagnostic'] and row['smaller_footprint_overlap_ratio']<LOW_OVERLAP_RATIO
            neighbors=interfaces[max(0,index-1):index]+interfaces[index+1:index+2]
            persistent=low and any(other['qualifies_for_diagnostic'] and other['smaller_footprint_overlap_ratio']<LOW_OVERLAP_RATIO for other in neighbors)
            row['persistent_low_overlap']=bool(persistent)
            if not row['qualifies_for_diagnostic']:continue
            if row['geometric_vertical_gap_mm']>PLANE_TOLERANCE_MM:
                observations.append({'kind':'DECLARED_VERTICAL_GAP','interface_index':index})
            elif row['geometric_vertical_gap_mm']<-PLANE_TOLERANCE_MM:
                observations.append({'kind':'OVERLAPPING_DECLARED_LAYER_INTERVALS','interface_index':index})
            elif persistent:
                kind='NO_DECLARED_LAYER_OVERLAP' if row['overlap_area_mm2']<=1e-10 else 'LOW_DECLARED_LAYER_OVERLAP'
                observations.append({'kind':kind,'interface_index':index})
        eligible=[row for row in interfaces if row['qualifies_for_diagnostic']]
        worst=min(eligible,key=lambda row:(row['smaller_footprint_overlap_ratio'],row['overlap_area_mm2'])) if eligible else None
        return {'layers':descriptors,'interfaces':interfaces,'layer_count':len(descriptors),
                'interfaces_checked':len(interfaces),'qualifying_interface_count':len(eligible),
                'geometric_overlap_area_mm2':worst['overlap_area_mm2'] if worst else None,
                'minimum_smaller_footprint_overlap_ratio':worst['smaller_footprint_overlap_ratio'] if worst else None,
                'worst_qualifying_interface':worst,'observations':observations,
                'tools':sorted({tool for row in descriptors for tool in row['tools']})}

    def finish(self,complete=True):
        from shapely.errors import GEOSException
        self.check_cancelled();results={}
        for key,entry in self.entries.items():
            self.check_cancelled();gaps=set(self.gaps)|entry['gaps']
            if not complete:gaps.add('INCOMPLETE_SOURCE_SCAN')
            base={'version':VERSION,'provenance':PROVENANCE,'scope':SCOPE,
                'normal_axis':'Z','plane_axes':['X','Y'],'estimated_not_measured':True,
                'section_window_bounds_mm':entry.get('bounds'),'source_records_scanned':self.source_records_scanned,
                'retained_records':entry['retained_records'],'sampled':False,
                'actual_bond_measured':False,'molecular_weld_quality_verified':False,'is_failure_prediction':False,
                'geometry_basis':'INTERSECTION_OF_ADJACENT_DECLARED_RECTANGULAR_ROAD_FOOTPRINTS',
                'plane_tolerance_mm':PLANE_TOLERANCE_MM,'low_overlap_screening_threshold':LOW_OVERLAP_RATIO,
                'limits':{'maximum_retained_records_per_candidate':self.max_records,'maximum_total_retained_records':self.max_total_records,
                          'maximum_layers_per_candidate':MAX_LAYERS,'maximum_union_vertices':MAX_UNION_VERTICES},
                'limitations':['Declared rectangular footprints are not measured polymer bead contact or molecular weld strength.',
                    'Overlap/smaller compares support of the smaller footprint; one does not validate whole-part adhesion.',
                    'Tiny caps, first/last interfaces, unsupported crop transitions and mere footprint growth are not contact-failure predictions.',
                    'Temperature, cooling, extrusion quality, peeling/shear stresses and fracture load are not solved.']}
            details={'layers':[],'interfaces':[],'layer_count':0,'interfaces_checked':0,'qualifying_interface_count':0,
                     'geometric_overlap_area_mm2':None,'minimum_smaller_footprint_overlap_ratio':None,
                     'worst_qualifying_interface':None,'observations':[],'tools':[]}
            if not gaps:
                try:details=self._finish_entry(entry)
                except (UnsupportedGeometry,GEOSException) as error:gaps.add(str(error))
            results[key]={**base,**details,'status':'WITHHELD' if gaps else 'COMPLETE','complete':not bool(gaps),
                          'assessment_gaps':sorted(gaps)}
        return results
