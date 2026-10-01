"""Build a factual FusRock catalogue snapshot from official public pages.

Long marketing prose and images are deliberately excluded. The snapshot keeps
the comparison facts, test conditions, source links, colour specifications and
official slicer-profile metadata needed for product identification.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen


DISPLAY_URL = 'https://www.fusrock.com/fusrock/tools/comparison.html'
BOOTSTRAP_URL = 'https://www.fusrock.com/?page=comparison&embed=fusrock'
PRODUCT_INDEX_URL = 'https://www.fusrock.com/products'
USER_AGENT = 'PrintOps-FusRock-Catalog/1.0 (+local material reference audit)'
PRODUCT_PAGE_FACT_LABELS = {
    'Nozzle Temperature': 'nozzle_temperature',
    'Recommended Nozzle Diameter': 'recommended_nozzle_diameter',
    'Recommended build surface treatment': 'build_surface_treatment',
    'Build plate temperature': 'build_plate_temperature',
    'Chamber Temp': 'chamber_temp',
    'Cooling fan speed': 'cooling_fan_speed',
    'Print speed': 'print_speed',
    'Retraction distance': 'retraction_distance',
    'Retraction speed': 'retraction_speed',
    'Recommended Support Material': 'recommended_support_material',
    'Drying setting': 'drying_setting',
    'Annealing': 'annealing',
}


def fetch(url: str) -> str:
    request = Request(url, headers={'User-Agent': USER_AGENT})
    with urlopen(request, timeout=60) as response:
        return response.read().decode(response.headers.get_content_charset() or 'utf-8')


class JsonScriptParser(HTMLParser):
    def __init__(self, wanted: str):
        super().__init__(convert_charrefs=False)
        self.wanted = wanted
        self.active = False
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == 'script' and values.get('id') == self.wanted:
            self.active = True

    def handle_endtag(self, tag):
        if tag == 'script' and self.active:
            self.active = False

    def handle_data(self, data):
        if self.active:
            self.parts.append(data)


class ProductIndexParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls: set[str] = set()

    def handle_starttag(self, tag, attrs):
        if tag != 'a':
            return
        href = dict(attrs).get('href', '')
        if re.fullmatch(r'/products/[a-z0-9-]+', href) and 'fusdry-' not in href:
            self.urls.add(urljoin(PRODUCT_INDEX_URL, href))


class ProductPageParser(HTMLParser):
    def __init__(self, url: str):
        super().__init__()
        self.url = url
        self.archive_id = None
        self.material_id = None
        self.rows: list[dict] = []
        self.current_row = None

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        classes = set(values.get('class', '').split())
        if tag == 'body' and values.get('data-wwh-archive-id'):
            self.archive_id = values['data-wwh-archive-id']
        if tag == 'tr' and 'js-product-config-row' in classes:
            self.current_row = {
                key: values.get('data-' + key, '')
                for key in ('slicer', 'printer_brand', 'printer_model', 'nozzle_diameter',
                            'provider_source', 'strict_mode', 'keyword')
            }
        if tag == 'a' and 'js-product-config-download' in classes:
            detail = values.get('data-detail-url', '')
            match = re.search(r'/id/(\d+)', detail)
            if match:
                self.material_id = int(match.group(1))
            if self.current_row is not None:
                self.current_row.update({
                    'download_url': urljoin(self.url, values.get('href', '')),
                    'detail_url': detail,
                    'material': values.get('data-material', ''),
                })
                self.rows.append(self.current_row)
                self.current_row = None


def json_field(value):
    if value in (None, ''):
        return None
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return value


def numeric(value):
    if value in (None, '', '-', 0, '0', '0.00'):
        return None
    return value


def test_conditions(material):
    text = material.get('mechanical_test_params_en') or ''
    patterns = {
        'nozzle_mm': r'Nozzle size\s*([\d.]+)\s*mm',
        'nozzle_c': r'Nozzle temp\s*([\d.]+)\s*°?C',
        'bed_c': r'Bed temp\s*([\d.]+)\s*°?C',
        'speed_mm_s': r'Print speed\s*([\d.]+)\s*mm/s',
        'infill_percent': r'Infill\s*([\d.]+)\s*%',
        'infill_angle': r'Infill angle\s*([^,]+)',
    }
    parsed = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.I)
        if not match:
            continue
        value = match.group(1).strip()
        parsed[key] = value if key == 'infill_angle' else float(value)
        if key != 'nozzle_mm' and key != 'infill_angle' and parsed[key].is_integer():
            parsed[key] = int(parsed[key])
    if material.get('mechanical_anneal_condition_en'):
        parsed['anneal_condition'] = material['mechanical_anneal_condition_en']
    return parsed


def factual_product(material, page):
    metrics = material.get('metrics') or {}
    recommendations = {
        'nozzle_temp_c': [material.get('nozzle_temp_min'), material.get('nozzle_temp_max')],
        'bed_temp_c': [material.get('bed_temp_min'), material.get('bed_temp_max')],
        'print_speed_mm_s': [material.get('print_speed_min'), material.get('print_speed_max')],
        'suggest_nozzle_mm': [material.get('suggest_nozzle_mm_min'), material.get('suggest_nozzle_mm_max')],
        'chamber_temp_c': [material.get('chamber_temp_c_min'), material.get('chamber_temp_c_max')],
        'raft_gap_mm': [material.get('raft_gap_mm_min'), material.get('raft_gap_mm_max')],
        'retraction_mm': [material.get('retraction_mm_min'), material.get('retraction_mm_max')],
        'retraction_speed_mm_s': [material.get('retraction_speed_mm_s_min'), material.get('retraction_speed_mm_s_max')],
        'cooling_fan_percent': [material.get('cooling_fan_pct_min'), material.get('cooling_fan_pct_max')],
        'support_density_percent': [material.get('support_density_pct_min'), material.get('support_density_pct_max')],
        'support_z_distance_mm': [material.get('support_z_distance_mm_min'), material.get('support_z_distance_mm_max')],
        'support_xy_distance_mm': [material.get('support_xy_distance_mm_min'), material.get('support_xy_distance_mm_max')],
        'support_border_loops': [material.get('support_border_loops_min'), material.get('support_border_loops_max')],
        'volumetric_print_temp_c': [numeric(material.get('volumetric_print_temp_c')),
                                    numeric(material.get('volumetric_print_temp_c_2')),
                                    numeric(material.get('volumetric_print_temp_c_3'))],
        'volumetric_flow_mm3_s': numeric(material.get('volumetric_flow_speed')),
        'nozzle_material': material.get('nozzle_material_display') or material.get('nozzle_material_en') or None,
        'bed_plate_material': material.get('bed_plate_material_display') or material.get('bed_plate_material_en') or None,
        'support_material': material.get('support_material_display') or None,
        'compatible_materials': material.get('compatible_materials_display') or None,
        'auxiliary_devices': material.get('auxiliary_devices_display') or None,
        'dry_before_use': material.get('dry_before_use_display') or material.get('dry_before_use_en') or None,
        'enclosure_printing': material.get('enclosure_printing_display') or material.get('enclosure_printing_en') or None,
        'post_print_operations': material.get('post_print_operations_display') or material.get('post_print_operations_en') or None,
        'precautions': material.get('precautions_en') or None,
    }
    return {
        'id': material['id'],
        'material_name': material['material_name'],
        'material_model': material.get('material_model'),
        'brand': material.get('brand'),
        'series': material.get('series_key'),
        'forming_process': material.get('forming_process_en'),
        'weights_kg': [float(v) for v in str(material.get('weight_kg_multi') or material.get('weight_kg') or '').split(',') if v],
        'filament_diameters_mm': [float(v) for v in str(material.get('filament_diameter_mm_multi') or '').split(',') if v],
        'colors': (json_field(material.get('color_multi')) or {}).get('colors', []),
        'application_scenarios': material.get('application_scenarios') or json_field(material.get('application_scenarios_json')) or [],
        'recommendations': recommendations,
        'mechanical_test_conditions': test_conditions(material),
        'mechanical_test_conditions_text_en': material.get('mechanical_test_params_en') or None,
        'mechanical_test_conditions_text_zh': material.get('mechanical_test_params_zh') or None,
        'print_flow_temperature_matrix': json_field(material.get('print_flow_temp_json')),
        'metrics': metrics,
        'performance_url': f"https://www.fusrock.com/material/performance/id/{material['id']}/lang/en",
        'product_page_url': page.get('url') if page else None,
        'product_page_archive_id': page.get('archive_id') if page else None,
        'product_page_recommendations': page.get('recommendations', {}) if page else {},
        'official_profiles': page.get('profiles', []) if page else [],
    }


def parse_product_page(url):
    source=fetch(url)
    parser = ProductPageParser(url)
    parser.feed(source)
    cell=re.search(r'<th>\s*Recommended printing conditions[^<]*</th>\s*<td>(.*?)</td>',source,re.I|re.S)
    recommendations={}
    if cell:
        factual=html.unescape(re.sub(r'<[^>]+>',' ',cell.group(1)))
        factual=re.sub(r'\s+',' ',factual).strip()
        labels='|'.join(re.escape(label) for label in sorted(PRODUCT_PAGE_FACT_LABELS,key=len,reverse=True))
        parts=re.split(f'({labels})',factual,flags=re.I)
        for index in range(1,len(parts)-1,2):
            label=next((name for name in PRODUCT_PAGE_FACT_LABELS if name.casefold()==parts[index].casefold()),None)
            value=parts[index+1].strip(' :')
            if label and value:
                recommendations[PRODUCT_PAGE_FACT_LABELS[label]]=value
    return {'url': url, 'slug': url.rstrip('/').rsplit('/', 1)[-1],
            'archive_id': parser.archive_id, 'material_id': parser.material_id,
            'profiles': parser.rows,'recommendations':recommendations}


def product_slug_candidates(material_name):
    """Return factual URL-slug candidates without fuzzy grade matching."""
    normalized = (material_name or '').replace('™', '').replace('®', '').casefold()
    normalized = re.sub(r'[^a-z0-9]+', '-', normalized).strip('-')
    candidates = {normalized}
    if normalized.startswith('fusflex-'):
        candidates.add(normalized[len('fusflex-'):])
    # The site spells the combined polymer family as both PC-ABS and PC/ABS.
    if normalized == 'pc-abs-fr':
        candidates.add('pc-abs-fr')
    return candidates


def build(checked_date: str):
    page = fetch(BOOTSTRAP_URL)
    parser = JsonScriptParser('datashow-bootstrap-json')
    parser.feed(page)
    raw = html.unescape(''.join(parser.parts)).strip()
    bootstrap = json.loads(raw)

    index = ProductIndexParser()
    index.feed(fetch(PRODUCT_INDEX_URL))
    with ThreadPoolExecutor(max_workers=8) as pool:
        pages = list(pool.map(parse_product_page, sorted(index.urls)))
    pages_by_id = {row['material_id']: row for row in pages if row.get('material_id')}

    # Some official product pages do not publish a downloadable slicer profile,
    # so they expose no material id. Link those pages by the site's exact slug;
    # this does not change the stricter runtime profile matcher.
    pages_by_slug = {row['slug']: row for row in pages}
    for material in bootstrap['comparisonMaterials']:
        if material['id'] in pages_by_id:
            continue
        matches = [pages_by_slug[slug] for slug in product_slug_candidates(material['material_name'])
                   if slug in pages_by_slug]
        if len(matches) == 1:
            pages_by_id[material['id']] = matches[0]

    products = [factual_product(row, pages_by_id.get(row['id']))
                for row in bootstrap['comparisonMaterials']]
    products.sort(key=lambda row: (row['material_name'].casefold(), row['id']))
    parameters = sorted(bootstrap['comparisonRows'], key=lambda row: (row['group'], row['key']))
    return {
        'schema_version': 'FUSROCK_OFFICIAL_CATALOG_V1',
        'source': {
            'url': DISPLAY_URL,
            'bootstrap_url': BOOTSTRAP_URL,
            'product_index_url': PRODUCT_INDEX_URL,
            'checked_date': checked_date,
            'bootstrap_sha256': hashlib.sha256(raw.encode('utf-8')).hexdigest(),
            'product_count': len(products),
            'parameter_count': len(parameters),
            'product_pages_linked': len(pages_by_id),
            'scope': 'Official factual comparison fields and official slicer-profile metadata; marketing prose and images excluded.',
        },
        'parameters': parameters,
        'products': products,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--checked-date', default=date.today().isoformat())
    parser.add_argument('--output', type=Path,
                        default=Path(__file__).resolve().parents[1] / 'print_strength_engine' / 'fusrock_material_catalog.json')
    args = parser.parse_args()
    payload = build(args.checked_date)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(payload['source'], ensure_ascii=False))


if __name__ == '__main__':
    main()
