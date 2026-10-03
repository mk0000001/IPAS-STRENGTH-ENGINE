"""Bounded, source-motion process context and a separate volume section scenario.

Programmed volume is not measured bead geometry. Local volume is allocated
uniformly along the clipped centerline, not divided by configured wall count.
"""
from copy import deepcopy
from math import hypot, isfinite
from .automatic_sections import StreamingSections

VERSION='LOCAL_COMMANDED_PROCESS_V2_CURA_FEATURE_ROLES'
VOLUME_PROVENANCE='GCODE_COMMANDED_VOLUME_RECTANGULAR_EQUIVALENT'
ROLES=('OUTER_WALL','INNER_WALL','INFILL','SOLID','BRIDGE','OTHER_MODEL')
RANGES={'temperature_setpoint_c':('nozzle_setpoint_c',0,600),
        'bed_setpoint_c':('bed_setpoint_c',0,300),
        'chamber_setpoint_c':('chamber_setpoint_c',0,300),
        'commanded_speed_mm_s':('commanded_speed_mm_s',0,2000),
        'fan_pwm':('part_cooling_fan_pwm',0,255),
        'flow_override_percent':('flow_override_percent',0,1000)}


def _number(value,low=0,high=1e12):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not isfinite(value):return None
    return float(value) if low<=value<=high else None


def _role(feature):
    feature=str(feature or '').lower()
    if feature in ('outer wall','external perimeter','wall-outer'):return 'OUTER_WALL'
    if feature in ('inner wall','perimeter','wall-inner'):return 'INNER_WALL'
    if 'bridge' in feature:return 'BRIDGE'
    if feature in ('sparse infill','infill','internal infill','fill'):return 'INFILL'
    if 'solid' in feature or feature in ('top surface','bottom surface','skin'):return 'SOLID'
    return 'OTHER_MODEL'


def _fraction(start,end,bounds,height):
    # Z is the road top: a top outside the crop can still deposit into it.
    if max(start[2],end[2])<bounds[2][0] or min(start[2],end[2])-height>=bounds[2][1]:return 0
    low,high=0.,1.
    for axis in (0,1):
        delta=end[axis]-start[axis]
        if delta==0:
            if not bounds[axis][0]<=start[axis]<=bounds[axis][1]:return 0
        else:
            a=(bounds[axis][0]-start[axis])/delta;b=(bounds[axis][1]-start[axis])/delta
            low=max(low,min(a,b));high=min(high,max(a,b))
            if high<=low:return 0
    return max(0.,high-low)


class StreamingLocalProcess:
    def __init__(self,candidates):
        self.sections=StreamingSections(candidates)
        self.entries={key:{'bounds':entry.get('bounds'),'roles':{},'length':0.,'records':0,'gaps':set(),
                           'ranges':{key:{'min':None,'max':None,'known_length_mm':0.} for key in RANGES}}
                      for key,entry in self.sections.entries.items()}
        self.source_records=0

    def motion(self,start,end,width,height,tool,feature,context,arc=False):
        self.source_records+=1
        try:start=[float(v) for v in start];end=[float(v) for v in end]
        except (TypeError,ValueError,OverflowError):
            for key,entry in self.entries.items():
                entry['gaps'].add('INVALID_PROCESS_MOTION');self.sections.entries[key]['gaps'].append('INVALID_PROCESS_MOTION')
            return
        if len(start)!=3 or len(end)!=3 or any(not isfinite(v) for v in start+end):
            for key,entry in self.entries.items():
                entry['gaps'].add('INVALID_PROCESS_MOTION');self.sections.entries[key]['gaps'].append('INVALID_PROCESS_MOTION')
            return
        w=_number(width,.001,10);h=_number(height,.001,10)
        if arc:
            # Full-circle arcs have identical endpoints. Their analytic length
            # and allocation cannot be recovered from the endpoint chord.
            for key,entry in self.entries.items():
                entry['gaps'].add('ARC_VOLUME_ALLOCATION_UNSUPPORTED')
                self.sections.entries[key]['gaps'].append('ARC_VOLUME_ALLOCATION_UNSUPPORTED')
            return
        length=hypot(end[0]-start[0],end[1]-start[1])
        if not length:
            if start[2]!=end[2]:
                for key,entry in self.entries.items():
                    bounds=entry['bounds']
                    if bounds and all(bounds[i][0]-(w or 10)/2<=start[i]<=bounds[i][1]+(w or 10)/2 for i in (0,1)) and max(start[2],end[2])>=bounds[2][0] and min(start[2],end[2])-(h or 10)<bounds[2][1]:
                        entry['gaps'].add('NONPLANAR_DEPOSITION_UNSUPPORTED')
                        self.sections.entries[key]['gaps'].append('NONPLANAR_DEPOSITION_UNSUPPORTED')
            return
        role=_role(feature);context=context or {};matched=[]
        broad=[[min(start[i],end[i])-(w or 10)/2,max(start[i],end[i])+(w or 10)/2] for i in (0,1)]
        broad.append([min(start[2],end[2])-(h or 10),max(start[2],end[2])])
        for key,entry in self.entries.items():
            if entry['bounds'] is None:entry['gaps'].add('LOCAL_SECTION_WINDOW_REQUIRED');continue
            bounds=entry['bounds']
            geometric_hit=all(broad[i][1]>=bounds[i][0] and broad[i][0]<bounds[i][1] for i in range(3))
            if not geometric_hit:continue
            fraction=_fraction(start,end,entry['bounds'],h or 0)
            # Unknown or curved paths cannot prove that local volume is complete.
            if arc:
                entry['gaps'].add('ARC_VOLUME_ALLOCATION_UNSUPPORTED')
                self.sections.entries[key]['gaps'].append('ARC_VOLUME_ALLOCATION_UNSUPPORTED')
                continue
            matched.append(key);local_length=length*fraction
            entry['length']+=local_length;entry['records']+=1
            bucket=entry['roles'].setdefault(role,{'path_length_mm':0.,'volume_known_length_mm':0.,
                  'commanded_volume_mm3':None,'records':0,'over_declared_volume_records':0,'tools':set()})
            bucket['path_length_mm']+=local_length;bucket['records']+=1
            if isinstance(tool,int) and not isinstance(tool,bool) and tool>=0:bucket['tools'].add(tool)
            else:entry['gaps'].add('DEPOSITION_TOOL_REQUIRED')
            for field,(input_field,minimum,maximum) in RANGES.items():
                if local_length<=0:continue
                val=_number(context.get(input_field),minimum,maximum)
                if val is None:continue
                r=entry['ranges'][field];r['min']=val if r['min'] is None else min(r['min'],val)
                r['max']=val if r['max'] is None else max(r['max'],val)
                r['known_length_mm']+=local_length
            volume=_number(context.get('commanded_volume_mm3'))
            if volume is not None and local_length>0:
                bucket['volume_known_length_mm']+=local_length
                bucket['commanded_volume_mm3']=(bucket['commanded_volume_mm3'] or 0)+volume*fraction
                if w and h and volume>length*w*h:bucket['over_declared_volume_records']+=1
            gaps=[]
            if w is None or h is None:gaps.append('DECLARED_ROAD_DIMENSIONS_REQUIRED')
            if start[2]!=end[2]:gaps.append('NONPLANAR_DEPOSITION_UNSUPPORTED')
            if volume is None:gaps.append('COMMANDED_VOLUME_REQUIRED')
            if not isinstance(tool,int) or isinstance(tool,bool) or tool<0:gaps.append('DEPOSITION_TOOL_REQUIRED')
            if volume is not None and w and h and volume/(length*h)<.001:gaps.append('VOLUME_EQUIVALENT_WIDTH_BELOW_MODEL_RESOLUTION')
            entry['gaps'].update(str(gap) for gap in context.get('assessment_gaps',()))
            for gap in gaps:self.sections.entries[key]['gaps'].append(gap)
        # All source roads with valid dimensions/volume feed the second union;
        # missing evidence is marked only in affected local windows above.
        volume=_number(context.get('commanded_volume_mm3'))
        if matched and not arc and w and h and volume and start[2]==end[2] and isinstance(tool,int) and not isinstance(tool,bool) and tool>=0:
            equivalent=min(w,volume/(length*h))
            if equivalent>=.001:self.sections.segment(start,end,equivalent,h,tool)

    def finish(self,complete=True):
        self.sections.source_records_scanned=self.source_records
        sections=self.sections.finish(complete=complete);result={}
        for key,entry in self.entries.items():
            section=sections[key]
            section.update(provenance=VOLUME_PROVENANCE,geometry_basis='COMMAND_VOLUME_OVER_LENGTH_AND_DECLARED_HEIGHT_CAPPED_AT_DECLARED_WIDTH',
                           commanded_volume_is_measured=False,width_capped_at_declared=True)
            gaps=set(entry['gaps'])
            if not complete:gaps.add('INCOMPLETE_SOURCE_SCAN')
            roles=deepcopy(entry['roles'])
            for role in roles.values():role['tools']=sorted(role['tools'])
            result[key]={'version':VERSION,'status':'COMPLETE' if complete else 'PARTIAL','complete':bool(complete),
                         'sampled':False,'is_measured':False,'provenance':'ORIGINAL_GCODE_COMMANDED_MOTION',
                         'section_window_bounds_mm':entry['bounds'],'path_length_mm':entry['length'],
                         'records':entry['records'],'source_motion_records':self.source_records,'roles':roles,
                         'volume_allocation_basis':'UNIFORM_ALONG_CLIPPED_CENTERLINE_WITH_ROAD_HEIGHT_INTERSECTION',
                         'individual_wall_passes_resolved':False,'measured_substrate_temperature_c':None,
                         'molecular_weld_quality_verified':False,'assessment_gaps':sorted(gaps),
                         **deepcopy(entry['ranges']),'volume_section':section}
        return result


def valid_process_descriptor(value):
    """Reject unbounded/tampered cached summaries before using their numbers."""
    try:
        if not isinstance(value,dict) or value.get('version')!=VERSION:return False
        if value.get('status') not in ('COMPLETE','PARTIAL') or value.get('complete')!=(value['status']=='COMPLETE'):return False
        if value.get('sampled') is not False or value.get('is_measured') is not False:return False
        if value.get('provenance')!='ORIGINAL_GCODE_COMMANDED_MOTION':return False
        if value.get('measured_substrate_temperature_c') is not None or value.get('molecular_weld_quality_verified') is not False or value.get('individual_wall_passes_resolved') is not False:return False
        bounds=value.get('section_window_bounds_mm')
        if not isinstance(bounds,list) or len(bounds)!=3 or any(not isinstance(pair,list) or len(pair)!=2 or _number(pair[0],-1e9) is None or _number(pair[1],-1e9) is None or pair[0]>=pair[1] for pair in bounds):return False
        total=_number(value.get('path_length_mm'))
        if total is None or not isinstance(value.get('roles'),dict) or set(value['roles'])-set(ROLES):return False
        length=0.
        for role in value['roles'].values():
            if not isinstance(role,dict):return False
            size=_number(role.get('path_length_mm'));known=_number(role.get('volume_known_length_mm'))
            if size is None or known is None or known>size+1e-6:return False
            volume=role.get('commanded_volume_mm3')
            if volume is not None and _number(volume) is None:return False
            if (known>0)!=(volume is not None):return False
            length+=size
            if not isinstance(role.get('tools'),list) or len(role['tools'])>256 or any(not isinstance(t,int) or isinstance(t,bool) or t<0 for t in role['tools']):return False
        if abs(length-total)>1e-6*max(1,total):return False
        for field in RANGES:
            r=value.get(field)
            if not isinstance(r,dict):return False
            known=_number(r.get('known_length_mm'))
            if known is None or known>total+1e-6:return False
            low,high=RANGES[field][1:]
            if known>0:
                if _number(r.get('min'),low,high) is None or _number(r.get('max'),low,high) is None or r['min']>r['max']:return False
            elif r.get('min') is not None or r.get('max') is not None:return False
        return isinstance(value.get('assessment_gaps'),list) and len(value['assessment_gaps'])<=100
    except (ValueError,TypeError,KeyError,OverflowError):return False
