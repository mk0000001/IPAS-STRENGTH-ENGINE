"""Finished-part thin-region screening from outer contours; not FEA or failure load."""
import math
VERSION='LOCAL_OUTER_ENVELOPE_V7_SELECTED_TERMINAL_ROOT_METADATA'
AXIS_NAMES=('Z','Y','X')


def section_metrics(solid,part,spacing,threshold_mm,axis=None,component_labels=None,
                    station_interval=None,preferred_station=None,prefer_high_station=False):
    """Separate area and principal-bending minima within one connected region.

    Stations are grid-relative here; screen_solid exports world coordinates.
    Principal bending is a geometric comparison, not a supplied loading case.
    """
    import numpy as np
    if component_labels is None:
        from scipy import ndimage as ndi
        component_labels,_=ndi.label(solid)  # Face-connected material, not corner contact.
    ids=component_labels[tuple(part.T)]
    occupied=ids[ids>0]
    if not len(occupied):return None
    components=np.unique(occupied)
    if len(components)!=1:return None  # Never aggregate unrelated candidate objects.
    component=int(components[0])
    # The load axis follows the whole connected region, never a sampling bucket.
    axis=int(np.argmax(np.ptp(part,axis=0))) if axis is None else int(axis)
    pad=int(math.ceil(threshold_mm/spacing))+1
    low=np.maximum(part.min(axis=0)-pad,0);high=np.minimum(part.max(axis=0)+pad+1,solid.shape)
    if station_interval is not None:
        low[axis]=max(int(low[axis]),int(station_interval[0]))
        high[axis]=min(int(high[axis]),int(station_interval[1])+1)
        if low[axis]>=high[axis]:return None
    window=component_labels[low[0]:high[0],low[1]:high[1],low[2]:high[2]]==component
    counts=window.sum(axis=tuple(i for i in range(3) if i!=axis))
    stations=np.flatnonzero(counts>0)
    if not len(stations):return None
    start=max(0,int(part.min(axis=0)[axis])-int(low[axis]));end=min(len(counts)-1,int(part.max(axis=0)[axis])-int(low[axis]))
    inside=stations[(stations>=start)&(stations<=end)]
    if not len(inside):inside=stations
    minimum=counts[inside].min();ties=inside[counts[inside]==minimum]
    if preferred_station is None:station=int(ties[0])
    else:
        distances=abs(ties+low[axis]-preferred_station)
        preferred=ties[distances==distances.min()]
        station=int(preferred[-1] if prefer_high_station else preferred[0])
    area=float(counts[station])*spacing**2
    modulus=None;bending_station=None;bending_area=None;bending_properties=None
    # Repeated planes are common in prismatic parts. Cache only the preceding
    # plane, bounding memory and retaining exact station/tie ordering.
    previous_plane=None;previous_properties=None
    for index in inside:
        selection=[slice(None)]*3;selection[axis]=int(index)
        plane=window[tuple(selection)]
        if previous_plane is not None and np.array_equal(plane,previous_plane):
            properties=previous_properties
        else:
            cells=np.argwhere(plane);offsets=(cells-cells.mean(axis=0))*spacing
            # Finite square-cell coordinate second-moment tensor, including
            # product of inertia. Eigenvectors describe principal stress gradients.
            tensor=offsets.T@offsets*spacing**2+np.eye(2)*len(cells)*spacing**4/12
            moments,directions=np.linalg.eigh(tensor)
            distances=np.max(np.abs(offsets@directions),axis=0)+spacing/2*np.sum(np.abs(directions),axis=0)
            moduli=moments/distances;weak=int(np.argmin(moduli))
            normal=np.zeros(3)
            plane_axes=[i for i in range(3) if i!=axis]
            for i,plane_axis in enumerate(plane_axes):normal[2-plane_axis]=directions[i,weak]
            properties=(float(moduli[weak]),len(cells)*spacing**2,
                        {'principal_second_moments_mm4':moments.tolist(),
                         'principal_section_moduli_mm3':moduli.tolist(),
                         'bending_coordinate_moment_tensor_mm4':tensor.tolist(),
                         'section_plane_axes':[AXIS_NAMES[i] for i in plane_axes],
                         'bending_stress_gradient_xyz':normal.tolist()})
            previous_plane=plane.copy();previous_properties=properties
        closer=(preferred_station is not None and bending_station is not None and
                abs(int(low[axis])+int(index)-preferred_station)<
                abs(int(low[axis])+bending_station-preferred_station))
        if preferred_station is not None and bending_station is not None and prefer_high_station:
            closer=closer or (abs(int(low[axis])+int(index)-preferred_station)==
                              abs(int(low[axis])+bending_station-preferred_station) and int(index)>bending_station)
        if (modulus is None or properties[0]<modulus-1e-12 or
                (abs(properties[0]-modulus)<=1e-12 and closer)):
            modulus,bending_area,bending_properties=properties;bending_station=int(index)
    return {'min_section_area_mm2':round(area,4),'section_normal_axis':AXIS_NAMES[axis],
            'section_modulus_mm3':round(modulus,4) if modulus else None,
            'section_station_mm':float((int(low[axis])+station+.5)*spacing),
            'axial_section_station_mm':float((int(low[axis])+station+.5)*spacing),
            'bending_section_station_mm':float((int(low[axis])+bending_station+.5)*spacing),
            'bending_section_area_mm2':round(bending_area,4),
            'section_window_bounds_mm':[[float(low[i]*spacing),float(high[i]*spacing)] for i in (2,1,0)],
            **bending_properties,
            'section_basis':'SEPARATE_AREA_AND_PRINCIPAL_BENDING_MINIMA',
            'section_scope':'CROPPED_FACE_CONNECTED_MATERIAL_COMPONENT'}


def _representative_regions(candidates):
    """Collapse equal-section body buckets without losing either end or object.

    Equal means identical reported voxel A/Z, not a calibrated tolerance. This
    removes the arbitrary long-strip voxel-count order, while real changes in
    section geometry remain visible.
    """
    groups={}
    for candidate in candidates:
        key=(candidate['object_component_id'],candidate['thin_component_id'],
             candidate['end_role'],candidate['terminal_kind'],
             candidate.get('min_section_area_mm2'),candidate.get('section_modulus_mm3'))
        groups.setdefault(key,[]).append(candidate)
    representatives=[]
    for group in groups.values():
        axis='XYZ'.index(group[0]['section_normal_axis'])
        bounds=group[0]['thin_component_bounds_mm'][axis]
        center=(bounds[0]+bounds[1])/2
        candidate=min(group,key=lambda row:(abs(row['position_mm'][axis]-center),
                                            tuple(row['position_mm'])))
        candidate['equivalent_bucket_count']=len(group)
        if candidate['end_role']=='INTERIOR':
            candidate['selection_reason']=('UNIFORM_THIN_REGION' if len(group)>1
                                           else 'LOCAL_SECTION_REDUCTION')
        representatives.append(candidate)
    return representatives


def screen_solid(solid,origin_xyz,spacing_mm,*,threshold_mm=2.4,max_candidates=6):
    import numpy as np
    from scipy import ndimage as ndi
    spacing=float(spacing_mm)
    if spacing<=0 or not math.isfinite(spacing):raise ValueError('INVALID_GRID_SPACING')
    solid=np.asarray(solid,dtype=bool)
    if solid.ndim!=3 or solid.size>4_000_000:raise ValueError('LOCAL_GEOMETRY_GRID_LIMIT')
    base={'version':VERSION,'status':'NO_THIN_REGION_DETECTED','candidates':[],
          'resolution_mm':spacing,'threshold_mm':threshold_mm,'basis':'OUTER_CONTOUR_ENVELOPE_DISTANCE_RIDGE',
          'is_failure_prediction':False,'support_included':False,'confidence':'GEOMETRIC_SCREENING',
          'rank_basis':'GEOMETRIC_COMPARISON_NOT_FAILURE_ORDER',
          'screening_comparison_basis':'EQUAL_25MM_PRINCIPAL_BENDING_GEOMETRY',
          'terminal_policy':{'evaluation':'INTERIOR_QUARTER_OF_FREE_END_BUCKET',
                             'is_actual_fixture_identified':False,
                             'end_transition_is_not_free_end':True,
                             'abrupt_transition_guard':{'max_next_to_previous_area_ratio':.5,
                                'search_extent':'INTERIOR_HALF_OF_TERMINAL_BUCKET',
                                'is_empirically_calibrated':False}},
          'limitations':['Outer-envelope thickness is a voxel proxy; this does not model infill bonding or failure load.',
                         'Thickness uncertainty is at least one voxel plus contour/line-width uncertainty.',
                          'Load direction, restraints, stress concentration, anisotropy and fatigue are not solved.',
                          'Free-end root windows are declared screening zones, not identified fixtures or validated failure locations.',
                          'Order compares voxel section geometry under an equal 25 mm reference moment arm; it is not actual part-failure order.']}
    if not solid.any():return {**base,'status':'NO_MODEL_ENVELOPE'}
    distance=ndi.distance_transform_edt(np.pad(solid,1),sampling=spacing)[1:-1,1:-1,1:-1].astype(np.float32)
    maximum=ndi.maximum_filter(distance,size=3,mode='constant')
    ridge=solid&(distance>=maximum-1e-5)&(distance>0)&(2*distance<=threshold_mm+1e-5)
    del maximum
    # Only medial ridges qualify: ordinary surfaces of a thick solid are not thin sections.
    grown=ndi.binary_dilation(ridge)&solid
    labels,count=ndi.label(grown)
    # Label the full material once; candidate windows must not include neighbors.
    material_labels=ndi.label(solid)[0] if count else None
    material_objects=ndi.find_objects(material_labels) if count else []
    material_sizes=np.bincount(material_labels.ravel()) if count else []
    objects=ndi.find_objects(labels);candidates=[]
    overall_span=max(np.asarray(solid.shape)*spacing);bin_mm=max(10.,overall_span/8)
    for label,slices in enumerate(objects,1):
        if slices is None:continue
        local=np.argwhere((labels[slices]==label)&ridge[slices])
        if len(local)<8:continue
        points=local+np.array([s.start for s in slices])
        axis=int(np.argmax(np.ptp(points,axis=0)));bins=np.floor((points[:,axis]-points[:,axis].min())*spacing/bin_mm).astype(int)
        component_ids=np.unique(material_labels[tuple(points.T)])
        component_ids=component_ids[component_ids>0]
        if len(component_ids)!=1:continue
        object_id=int(component_ids[0]);object_slices=material_objects[object_id-1]
        object_low=np.array([s.start for s in object_slices]);object_high=np.array([s.stop for s in object_slices])
        thin_low=points.min(axis=0);thin_high=points.max(axis=0)+1
        world_bounds=lambda lo,hi:[[float(origin_xyz[i]+lo[2-i]*spacing),
                                  float(origin_xyz[i]+hi[2-i]*spacing)] for i in range(3)]
        object_bounds=world_bounds(object_low,object_high)
        thin_bounds=world_bounds(thin_low,thin_high)
        unique_bins=np.unique(bins)
        for bucket in np.unique(bins):
            part=points[bins==bucket]
            if len(part)<8:continue
            span=(np.ptp(part,axis=0)+1)*spacing
            if max(span)<3:continue
            thickness=2*distance[tuple(part.T)]
            proxy=float(np.percentile(thickness,25))
            if max(span)/max(proxy,spacing)<3:continue
            median=np.median(part,axis=0)
            eligible=np.flatnonzero(thickness<=proxy+1e-5)
            index=int(eligible[np.argmin(np.sum((part[eligible]-median)**2,axis=1))])
            proxy=float(thickness[index])
            position=(np.asarray(origin_xyz)+(part[index][::-1]+.5)*spacing).tolist()
            low=(np.asarray(origin_xyz)+part.min(axis=0)[::-1]*spacing).tolist()
            high=(np.asarray(origin_xyz)+(part.max(axis=0)[::-1]+1)*spacing).tolist()
            # End roles are geometric region identities, independent of score.
            # A medial region may stop inside a larger object; that is not a
            # free end and must not activate the cap-exclusion policy.
            roles=[]
            if bucket==unique_bins[0]:roles.append('LOW_END')
            if bucket==unique_bins[-1]:roles.append('HIGH_END')
            if not roles:roles=['INTERIOR']
            if len(roles)==2:
                low_free=abs(int(thin_low[axis])-int(object_low[axis]))<=1
                high_free=abs(int(thin_high[axis])-int(object_high[axis]))<=1
                # A short appendage has one free end, while an independently
                # short region can have two. Never erase their end identity.
                roles=(['BOTH_ENDS'] if low_free and high_free else
                       ['LOW_END'] if low_free else ['HIGH_END'] if high_free else ['INTERIOR'])
            end_role=roles[0];terminal_kind=None;station_interval=None;terminal_profile=None
            root_basis=None
            world_axis=2-axis
            if end_role!='INTERIOR':
                is_low=end_role=='LOW_END'
                endpoint=int(thin_low[axis] if is_low else thin_high[axis]-1)
                object_endpoint=int(object_low[axis] if is_low else object_high[axis]-1)
                terminal_kind=('OBJECT_FREE_END' if end_role=='BOTH_ENDS' or abs(endpoint-object_endpoint)<=1
                               else 'THIN_REGION_TRANSITION')
                if terminal_kind=='OBJECT_FREE_END':
                    a=int(part[:,axis].min());b=int(part[:,axis].max())
                    root_count=max(1,int(math.ceil((b-a+1)/4)))
                    if end_role=='BOTH_ENDS':
                        inner_a=a+root_count;inner_b=b-root_count
                        station_interval=(inner_a,inner_b) if inner_a<=inner_b else ((a+b)//2,)*2
                    else:station_interval=(b-root_count+1,b) if is_low else (a,a+root_count-1)
                    root_basis=('CENTRAL_HALF_OF_SHORT_FREE_REGION' if end_role=='BOTH_ENDS'
                                else 'INTERIOR_QUARTER_OF_TERMINAL_BUCKET')
                    pad=int(math.ceil(threshold_mm/spacing))+1
                    profile_low=np.maximum(part.min(axis=0)-pad,0)
                    profile_high=np.minimum(part.max(axis=0)+pad+1,solid.shape)
                    profile_low[axis]=a;profile_high[axis]=b+1
                    profile_slices=tuple(slice(int(left),int(right)) for left,right in zip(profile_low,profile_high))
                    terminal_profile=(material_labels[profile_slices]==object_id).sum(
                        axis=tuple(i for i in range(3) if i!=axis))
                    if end_role!='BOTH_ENDS':
                        # A short abrupt narrowing can sit just outside the
                        # nominal inner quarter after reflection/rebucketing.
                        # Recognize the narrowing in the inner half, keeping
                        # the outer cap half from becoming a root by itself.
                        oriented=terminal_profile[::-1] if is_low else terminal_profile
                        transitions=np.flatnonzero((oriented[1:]>0)&(oriented[:-1]>0)&
                                                    (oriented[1:]<=oriented[:-1]*.5))+1
                        transitions=transitions[transitions<=len(oriented)//2]
                        if len(transitions):
                            transition=int(transitions[0])
                            n=max(1,int(math.ceil(bin_mm/spacing/4)))
                            if is_low:
                                root_end=b-transition;station_interval=(max(a,root_end-n+1),root_end)
                            else:
                                root_start=a+transition;station_interval=(root_start,min(b,root_start+n-1))
                            root_basis='ABRUPT_NARROWING_IN_INTERIOR_HALF'
            quality_reasons=[]
            if int((object_high-object_low).min())<=1:
                quality_reasons.append('SINGLE_VOXEL_CONNECTED_COMPONENT_THICKNESS')
            if station_interval and station_interval[1]-station_interval[0]<1:
                quality_reasons.append('ROOT_INTERVAL_LESS_THAN_TWO_VOXELS')
            quality='RESOLUTION_LIMITED_FEATURE' if quality_reasons else 'RESOLVED_GEOMETRIC_REGION'
            comparison_position=position[:]
            preferred=(sum(station_interval)/2 if station_interval else float(np.median(part[:,axis])))
            candidates.append({'kind':'LOCAL_THIN_SECTION','position_mm':position,'z_mm':position[2],
                'bounds_mm':[[float(a),float(b)] for a,b in zip(low,high)],'thickness_proxy_mm':round(proxy,3),
                'extent_mm':span[::-1].tolist(),'ridge_voxels':len(part),'resolution_mm':spacing,
                'reason':'THIN_FINISHED_PART_ENVELOPE','load_capacity_n':None,
                'slenderness_ratio':float(max(span)/max(proxy,spacing)),
                'object_component_id':object_id,'thin_component_id':label,
                'object_bounds_mm':object_bounds,'thin_component_bounds_mm':thin_bounds,
                'object_component_basis':'VOXEL_FACE_CONNECTED_REGION_NOT_SOURCE_OBJECT_ID',
                'object_component_voxel_count':int(material_sizes[object_id]),
                'object_component_voxel_span_xyz':(object_high-object_low)[::-1].tolist(),
                'thin_component_ridge_voxels':len(points),
                'component_axis':AXIS_NAMES[axis],'end_role':end_role,'terminal_kind':terminal_kind,
                'screening_quality':quality,'screening_quality_reasons':quality_reasons,
                'cap_exclusion_policy':('TERMINAL_ABRUPT_ROOT_WITH_OUTER_HALF_GUARD'
                                       if root_basis=='ABRUPT_NARROWING_IN_INTERIOR_HALF' else
                                       'TERMINAL_CENTRAL_HALF' if end_role=='BOTH_ENDS' else
                                       'TERMINAL_INTERIOR_QUARTER') if station_interval else 'NONE',
                'selection_reason':'THIN_TERMINAL_ROOT' if terminal_kind=='OBJECT_FREE_END'
                                   else 'THIN_REGION_TRANSITION' if terminal_kind else 'LOCAL_SECTION_REDUCTION',
                'terminal_root_selection_basis':root_basis,
                'terminal_root_is_actual_attachment':False,
                'rank_basis':'GEOMETRIC_COMPARISON_NOT_FAILURE_ORDER'})
            section=section_metrics(solid,part,spacing,threshold_mm,axis,material_labels,
                                    station_interval=station_interval,preferred_station=preferred,
                                    prefer_high_station=end_role=='LOW_END')
            if section:
                # section_metrics uses grid-relative coordinates; exported stations
                # share the world coordinate system used by bounds and markers.
                for field in ('section_station_mm','axial_section_station_mm','bending_section_station_mm'):
                    section[field]=round(section[field]+float(origin_xyz[2-axis]),3)
                section['section_window_bounds_mm']=[[edge+float(origin_xyz[i]) for edge in pair]
                                                     for i,pair in enumerate(section['section_window_bounds_mm'])]
                position[2-axis]=section['section_station_mm']
                candidates[-1]['z_mm']=position[2]
                candidates[-1].update(section)
                candidate=candidates[-1]
                if terminal_kind:
                    end_station=float(thin_bounds[world_axis][0 if end_role=='LOW_END' else 1])
                    end_position=comparison_position[:];end_position[world_axis]=end_station
                    candidate.update(terminal_axis=AXIS_NAMES[axis],terminal_end_position_mm=end_position,
                                     terminal_end_station_mm=end_station,terminal_root_position_mm=position[:],
                                     terminal_root_station_mm=section['section_station_mm'])
                    if end_role=='BOTH_ENDS':
                        both=[]
                        for edge in thin_bounds[world_axis]:
                            end=comparison_position[:];end[world_axis]=edge;both.append(end)
                        candidate['terminal_end_positions_mm']=both
                    if station_interval:
                        # Declared taper evidence is a geometric area comparison
                        # at the same transverse crop. It measures neither weld
                        # quality nor adhesion. Both end profiles remain outside
                        # the root cuts used for the comparison load.
                        profile=terminal_profile
                        n=max(1,int(math.ceil(len(profile)/4)))
                        if end_role=='BOTH_ENDS':
                            outer=np.concatenate((profile[:n],profile[-n:]))
                            root=profile[station_interval[0]-profile_low[axis]:station_interval[1]-profile_low[axis]+1]
                        else:
                            outer=profile[:n] if end_role=='LOW_END' else profile[-n:]
                            root=profile[station_interval[0]-profile_low[axis]:station_interval[1]-profile_low[axis]+1]
                        root_area=float(np.median(root))*spacing**2
                        outer_area=float(np.median(outer))*spacing**2
                        ratio=outer_area/root_area if root_area>0 else None
                        candidate['terminal_geometry']={'interior_median_area_mm2':root_area,
                            'outer_quarter_median_area_mm2':outer_area,'outer_to_interior_area_ratio':ratio,
                            'basis':'SAME_CROPPED_COMPONENT_VOXEL_SECTION_AREA',
                            'is_layer_adhesion_assessment':False}
                        if ratio is not None and ratio<1-1e-9:
                            candidate['selection_reason']='TAPERED_TERMINAL_ROOT'
                interval=station_interval or (int(part[:,axis].min()),int(part[:,axis].max()))
                candidate['section_evaluation_interval_mm']=[float(origin_xyz[world_axis]+interval[0]*spacing),
                                                             float(origin_xyz[world_axis]+(interval[1]+1)*spacing)]
                modulus=section['section_modulus_mm3']
                score=25/modulus if modulus and modulus>0 else 0.
                candidate['screening_score']=score
                candidate['screening_comparison']={'basis':'EQUAL_25MM_PRINCIPAL_BENDING_GEOMETRY',
                    'lever_mm':25,'section_modulus_mm3':modulus,'stress_per_unit_force_mpa_per_n':score}
    raw_candidate_count=len(candidates)
    candidates=_representative_regions([c for c in candidates if c.get('section_modulus_mm3')])
    # Equal moment-arm comparison is dimensionally consistent (stress per N).
    # Stable world coordinates settle exact ties; bucket length and voxel count
    # cannot make a same-section body outrank a short weaker terminal root.
    ordered=sorted(candidates,key=lambda c:(c['screening_quality']!='RESOLVED_GEOMETRIC_REGION',
                                            c['section_modulus_mm3'],c['min_section_area_mm2'],
                                            tuple(c['position_mm']),c['object_component_id'],c['end_role']))
    chosen=[]
    for c in ordered:
        if any(c['object_component_id']==p['object_component_id'] and
               not (c['terminal_kind']=='OBJECT_FREE_END' and p['terminal_kind']=='OBJECT_FREE_END'
                    and c['end_role']!=p['end_role']) and
               math.dist(c['position_mm'],p['position_mm'])<max(5.,bin_mm*.7) for p in chosen):continue
        c.update(rank=len(chosen)+1,region_id=f"local-thin-{len(chosen)+1}");chosen.append(c)
        if len(chosen)>=max_candidates:break
    return {**base,'status':'THIN_REGIONS_FOUND' if chosen else base['status'],'candidates':chosen,
            'occupied_voxels':int(solid.sum()),'medial_thin_voxels':int(ridge.sum()),'component_count':count,
            'raw_candidate_count':raw_candidate_count,'representative_candidate_count':len(candidates),
            'selection_parameters':{'max_candidates':max_candidates,'bucket_mm':bin_mm,
                                    'spatial_separation_mm':max(5.,bin_mm*.7),
                                    'quality_order':'RESOLVED_REGIONS_BEFORE_RESOLUTION_LIMITED_FEATURES',
                                    'equivalent_body_policy':'SAME_OBJECT_REGION_ROLE_AND_REPORTED_AREA_MODULUS'}}


def screen_contour_layers(layers,bounds,*,resolution_mm=.4,max_voxels=4_000_000,progress=None,cancelled=None):
    import numpy as np
    import shapely
    from shapely.geometry import Polygon,LineString
    low=np.array([v[0] for v in bounds],dtype=float);high=np.array([v[1] for v in bounds],dtype=float)
    if not np.isfinite([low,high]).all() or (high<=low).any():raise ValueError('INVALID_MODEL_BOUNDS')
    spacing=float(resolution_mm)
    while int(np.prod(np.ceil((high-low)/spacing).astype(int)+6))>max_voxels:spacing*=1.1
    if spacing>1:return {'version':VERSION,'status':'RESOLUTION_LIMIT','candidates':[],'resolution_mm':spacing,'support_included':False}
    origin=low-3*spacing;shape=(np.ceil((high-low)/spacing).astype(int)+6)[::-1]
    solid=np.zeros(tuple(shape),dtype=bool)
    xs=origin[0]+(np.arange(shape[2])+.5)*spacing
    ys=origin[1]+(np.arange(shape[1])+.5)*spacing
    def raster_into(target,geometry,parity=False):
        # Outside the exact geometry bounds contains_xy is always false. Keep
        # the original grid coordinates (including boundary rounding) unchanged.
        if geometry.is_empty:return
        x0,y0,x1,y1=geometry.bounds
        left=np.searchsorted(xs,x0,side='left')
        right=np.searchsorted(xs,x1,side='right')
        bottom=np.searchsorted(ys,y0,side='left')
        top=np.searchsorted(ys,y1,side='right')
        if left>=right or bottom>=top:return
        mask=shapely.contains_xy(geometry,xs[None,left:right],ys[bottom:top,None])
        view=target[bottom:top,left:right]
        if parity:view^=mask
        else:view|=mask
    mapping=[];closed_count=open_count=invalid_count=0
    for index,row in enumerate(layers):
        if cancelled and cancelled():raise RuntimeError('ANALYSIS_CANCELLED')
        if progress and index%20==0:progress(index)
        parity=np.zeros((len(ys),len(xs)),dtype=bool);walls=np.zeros_like(parity)
        for run_index,run in enumerate(row.get('runs',[])):
            if run_index%32==0 and cancelled and cancelled():raise RuntimeError('ANALYSIS_CANCELLED')
            points=run['points'];width=float(run['width_mm'])
            if len(points)<2 or not .02<=width<=5:continue
            line=LineString(points)
            if len(points)>=4 and math.dist(points[0],points[-1])<=max(.05,width*.5):
                polygon=Polygon(points)
                if polygon.area>width*width:
                    if not polygon.is_valid:invalid_count+=1;polygon=shapely.make_valid(polygon)
                    raster_into(parity,polygon,parity=True);closed_count+=1
                else:open_count+=1
            else:open_count+=1
            raster_into(walls,line.buffer(width/2,cap_style=2,join_style=2))
        plane=parity|walls
        z=float(row['z_mm']);h=float(row.get('height_mm') or .2)
        start=max(0,int(math.floor((z-h-origin[2])/spacing)))
        end=min(shape[0]-1,int(math.floor((z-origin[2]-1e-8)/spacing)))
        for zi in range(start,end+1):solid[zi]|=plane
        mapping.append((z,row['layer_number']))
    result=screen_solid(solid,origin.tolist(),spacing)
    for candidate in result['candidates']:
        candidate['layer_number']=min(mapping,key=lambda row:abs(row[0]-candidate['z_mm']))[1]
    result.update(coverage={'outer_layer_count':len(mapping),'closed_contours':closed_count,'open_runs':open_count,'repaired_contours':invalid_count},
                  grid_shape_zyx=[int(v) for v in shape],geometry_basis='EVEN_ODD_OUTER_WALL_ENVELOPE_WITH_LINE_WIDTH_BUFFER',
                  infill_voids_ignored=True,estimated_not_measured=True)
    return result
