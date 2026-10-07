"""Bounded real-layer reference candidates, independent of thin-region detection."""
from copy import deepcopy
from math import isfinite
from .candidates import rank_layers

COMPONENT_KINDS = frozenset(('COMPONENT_NECK_SECTION', 'COMPONENT_REFERENCE_SECTION'))


def _number(value, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        value = float(value)
    except OverflowError:
        return None
    return value if isfinite(value) and abs(value) <= 1e6 and (not positive or value > 0) else None


def reference_section_candidates(manifest, layer_profile, bounds, max_candidates=6):
    """Choose <=6 actual model layers; unknown heights never become default roads.

    Layer volume ranks screening locations only. Section forces must subsequently
    use complete declared-road geometry, separated into connected polygons.
    """
    if not isinstance(manifest, dict) or not isinstance(layer_profile, dict):
        return []
    if not isinstance(max_candidates, int) or isinstance(max_candidates, bool) or max_candidates <= 0:
        return []
    maximum = min(max_candidates, 6)
    if not isinstance(bounds, (list, tuple)) or len(bounds) != 3:
        return []
    normalized = []
    for index, pair in enumerate(bounds):
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            return []
        lo, hi = [_number(edge) for edge in pair]
        if lo is None or hi is None or (lo >= hi if index < 2 else lo > hi):
            return []
        normalized.append([lo, hi])
    models = manifest.get('layers')
    profile = layer_profile.get('layers')
    if not isinstance(models, list) or not isinstance(profile, (list, type(None))):
        return []
    rows = []; seen = set()
    for row in models:
        if not isinstance(row, dict) or _number(row.get('model'), True) is None:
            continue
        ident = row.get('id'); z = _number(row.get('z_mm'))
        if not isinstance(ident, int) or isinstance(ident, bool) or ident < 0 or ident in seen or z is None:
            continue
        seen.add(ident); rows.append({'id': ident, 'z': z, 'manifest': row})
    rows.sort(key=lambda row: (row['z'], row['id']))
    if not rows:
        return []
    by_id = {}
    for row in profile or []:
        if not isinstance(row, dict):
            continue
        ident = row.get('layer_number')
        if isinstance(ident, int) and not isinstance(ident, bool):
            by_id.setdefault(ident, row)
    for index, row in enumerate(rows):
        source = by_id.get(row['id'], {})
        if _number(source.get('z_mm')) != row['z']:
            source = {}
        row['volume'] = _number(source.get('volume_mm3'), True)
        height = None; basis = None; explicit = False
        for value in (source, row['manifest']):
            for field in ('layer_height_mm', 'height_mm', 'layer_height_for_proxy_mm'):
                if field not in value:
                    continue
                explicit = True; height = _number(value[field], True)
                if height is not None and not .001 <= height <= 5:
                    height = None
                basis = 'SAME_LAYER_HEIGHT_METADATA'
                break
            if explicit:
                break
        if not explicit:
            delta = row['z'] - rows[index-1]['z'] if index else rows[1]['z'] - row['z'] if len(rows) > 1 else None
            if delta is not None and .001 <= delta <= 5:
                height = delta; basis = 'ADJACENT_MODEL_DEPOSITION_Z_SPACING'
        row.update(height=height, height_basis=basis, index=index)
    valid_profile = {'layers': [{'layer_number': row['id'], 'z_mm': row['z'], 'volume_mm3': row['volume']}
                                for row in rows if row['volume'] is not None],
                     'incomplete': bool(layer_profile.get('incomplete'))}
    necks = rank_layers(valid_profile, max_candidates=maximum)['weak_candidates']
    available = {row['id']: row for row in rows}
    selections = [(available[neck['layer_number']], neck) for neck in necks if neck['layer_number'] in available]
    if not selections:
        interior = rows[1:-1] if len(rows) > 2 else rows
        # Rounded comparison avoids tiny binary Z differences reordering equal
        # sections; no rounded value is used by the actual section mechanics.
        score = lambda row: (round(row['volume']/row['height'], 9)
                             if row['volume'] is not None and row['height'] else float('inf'), row['z'], row['id'])
        selections = [(row, None) for row in sorted(interior, key=score)[:maximum]]
    result = []
    for row, neck in selections[:maximum]:
        height = row['height']; z = row['z']; station = z - height/2 if height else None
        neighbors = rows[max(0, row['index']-1):row['index']+2]
        bottom = min(other['z']-other['height'] if other['height'] else other['z'] for other in neighbors)
        top = max(other['z'] for other in neighbors)
        window = deepcopy(normalized); window[2] = [bottom, top]
        kind = 'COMPONENT_NECK_SECTION' if neck else 'COMPONENT_REFERENCE_SECTION'
        reason = 'LAYER_CONSTRICTION_ROAD_SECTION' if neck else 'REPRESENTATIVE_MODEL_ROAD_SECTION'
        result.append({**(deepcopy(neck) if neck else {}), 'kind': kind,
            'region_id': f"ref-{'neck' if neck else 'layer'}-{row['id']}", 'rank': len(result)+1,
            'layer_number': row['id'], 'z_mm': z,
            'position_mm': [(normalized[0][0]+normalized[0][1])/2, (normalized[1][0]+normalized[1][1])/2,
                            station if station is not None else z],
            'bounds_mm': deepcopy(window), 'section_window_bounds_mm': window,
            'section_normal_axis': 'Z', 'section_station_mm': station,
            'axial_section_station_mm': station, 'bending_section_station_mm': station,
            'layer_height_mm': height, 'layer_height_for_proxy_mm': height,
            'reference_height_basis': row['height_basis'],
            'material_area_proxy_mm2': row['volume']/height if row['volume'] is not None and height else None,
            'observed_model_volume_mm3': row['volume'], 'selection_reason': reason,
            'reason': reason, 'selection_basis': 'LAYER_RELATIVE_CONSTRICTION' if neck else 'LOW_MODEL_VOLUME_PER_HEIGHT_INTERIOR_LAYER',
            'component_selection_basis': 'MINIMUM_ALL_DIRECTION_MODULUS_CONNECTED_POLYGON',
            'assessment_gaps': [] if height else ['REFERENCE_LAYER_HEIGHT_REQUIRED'],
            'is_failure_prediction': False, 'whole_object_section_verified': False})
    return result
