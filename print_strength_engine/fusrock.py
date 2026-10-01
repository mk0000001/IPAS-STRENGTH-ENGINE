"""Exact-product references extracted from FusRock's official comparison data."""
from __future__ import annotations

import json
import re
from decimal import Decimal
from functools import lru_cache
from pathlib import Path


CATALOG_FILE = Path(__file__).with_name('fusrock_material_catalog.json')


@lru_cache(maxsize=1)
def catalog():
    return json.loads(CATALOG_FILE.read_text(encoding='utf-8'))


def _normalized(value):
    value = str(value or '').split('@', 1)[0]
    value = re.sub(r'\.3mf$', '', value, flags=re.I)
    value = value.replace('™', ' ').replace('®', ' ')
    return ' '.join(re.findall(r'[a-z0-9]+(?:\.[0-9]+)?', value.casefold()))


def _aliases(product):
    name = _normalized(product['material_name'])
    aliases = {name}
    for series in ('fusfun', 'fusforce', 'fusflex', 'fuscoating', 'fusfree'):
        if name.startswith(series + ' '):
            aliases.add(name[len(series) + 1:])
    return sorted(aliases, key=len, reverse=True)


_ALLOWED_SUFFIX = re.compile(
    r'^(?:(?:default|profile|bbl|bambu|lab|h2c|h2d|x1c|x1|carbon|p1s|p1p|a1|mini|'
    r'qidi|q1|q2|pro|combo|voron|stealthchanger|ratrig|vcore|idex|nozzle|layer|'
    r'mm|f?\d+(?:\.\d+)?(?:mm)?|\d{4,8})\s*)*$', re.I)


def _match_one(profile):
    normalized = _normalized(profile)
    if not normalized.startswith('fusrock '):
        return None
    body = normalized[len('fusrock '):]
    candidates = []
    for product in catalog()['products']:
        for alias in _aliases(product):
            if body == alias:
                candidates.append((len(alias), product))
            elif body.startswith(alias + ' '):
                suffix = body[len(alias) + 1:]
                if _ALLOWED_SUFFIX.fullmatch(suffix):
                    candidates.append((len(alias), product))
    if not candidates:
        return None
    candidates.sort(key=lambda row: row[0], reverse=True)
    if len(candidates) > 1 and candidates[0][0] == candidates[1][0]:
        return None
    return candidates[0][1]


def match_profiles(profiles):
    """Return one exact FusRock product only when every active profile agrees."""
    profiles = [str(value) for value in profiles or [] if str(value).strip()]
    if not profiles:
        return None
    matches = [_match_one(profile) for profile in profiles]
    if any(match is None for match in matches):
        return None
    ids = {match['id'] for match in matches}
    return matches[0] if len(ids) == 1 else None


def _number(value):
    if isinstance(value, bool) or value in (None, '', '-'):
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _plain(value):
    value = Decimal(value)
    return format(value, 'f').rstrip('0').rstrip('.') if value else '0'


def exact_directional_reference(product):
    """Use only the official XY/Z tensile-breaking pair from one test state."""
    if not product:
        return None
    metrics = product.get('metrics') or {}
    xy = _number(metrics.get('tbs_xy_unannealed'))
    z = _number(metrics.get('ts_z_unannealed'))
    conditions = product.get('mechanical_test_conditions') or {}
    if xy is None or z is None or not conditions:
        return None
    return {
        'raw_reference_mpa': {'XY': _plain(xy), 'Z': _plain(z)},
        'metric_keys': {'XY': 'tbs_xy_unannealed', 'Z': 'ts_z_unannealed'},
        'test_state': 'UNANNEALED',
        'test_conditions': conditions,
        'source_ref': product['performance_url'],
        'source_catalog_ref': catalog()['source']['url'],
        'source_checked_at': catalog()['source']['checked_date'],
    }


def product_summary(product):
    if not product:
        return None
    metrics = product.get('metrics') or {}
    recommendations = product.get('recommendations') or {}
    def pair(key):
        values = recommendations.get(key) or [None, None]
        return [value for value in values]
    source=catalog()['source']
    return {
        'product': 'FusRock ' + product['material_name'],
        'series': product.get('series'),
        'printing': {
            'nozzle_temp_c': pair('nozzle_temp_c'),
            'bed_temp_c': pair('bed_temp_c'),
            'print_speed_mm_s': pair('print_speed_mm_s'),
            'suggest_nozzle_mm': pair('suggest_nozzle_mm'),
            'cooling_fan_percent': pair('cooling_fan_percent'),
            'dry_before_use': recommendations.get('dry_before_use'),
            'enclosure_printing': recommendations.get('enclosure_printing'),
            'bed_plate_material': recommendations.get('bed_plate_material'),
            'support_material': recommendations.get('support_material'),
            'official_product_page': product.get('product_page_recommendations') or {},
        },
        'physical': {
            'density_g_cm3': metrics.get('physical_density'),
            'water_absorption_percent': metrics.get('physical_saturated_moisture'),
            'melting_temperature_c': metrics.get('physical_melting_point'),
            'glass_transition_temperature_c': metrics.get('custom_physical_glass_transition_temperature'),
        },
        'thermal': {
            'hdt_a_c': metrics.get('hdt_a_unannealed'),
            'hdt_b_c': metrics.get('hdt_b_unannealed'),
        },
        'mechanical': {
            'tensile_break_xy_mpa': metrics.get('tbs_xy_unannealed'),
            'tensile_break_z_mpa': metrics.get('ts_z_unannealed'),
            'youngs_modulus_xy_mpa': metrics.get('tm_xy_unannealed'),
            'youngs_modulus_z_mpa': metrics.get('tm_z_unannealed'),
            'elongation_break_xy_percent': metrics.get('eb_xy_unannealed'),
            'elongation_break_z_percent': metrics.get('eb_z_unannealed'),
            'bending_strength_xy_mpa': metrics.get('fs_xy_unannealed'),
            'bending_modulus_xy_mpa': metrics.get('fm_xy_unannealed'),
            'charpy_impact_xy_kj_m2': metrics.get('ni_xy_unannealed'),
        },
        'test_conditions': product.get('mechanical_test_conditions') or {},
        'source_url': product['performance_url'],
        'catalog_url': source['url'],
        'checked_date': source['checked_date'],
        'catalog': {key:source.get(key) for key in ('product_count','parameter_count','product_pages_linked','bootstrap_sha256')},
        'all_official_facts': {
            'metrics': metrics,
            'recommendations': recommendations,
            'colors': product.get('colors') or [],
            'application_scenarios': product.get('application_scenarios') or [],
            'print_flow_temperature_matrix': product.get('print_flow_temperature_matrix'),
            'official_profiles': product.get('official_profiles') or [],
            'product_page_recommendations': product.get('product_page_recommendations') or {},
        },
    }
