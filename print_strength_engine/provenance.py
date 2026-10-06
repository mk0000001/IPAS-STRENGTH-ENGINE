"""Observation identity metadata, never source authentication or a fitted model.

A supplied map is checked for internal consistency only. Equal numbers, DOI,
author and laboratory names never establish an experimental campaign identity.
"""
from copy import deepcopy
from hashlib import sha256
import json
import re

SCHEMA = 'PROVENANCE_OBSERVATION_MAP_V1'
KINDS = ('RAW_SPECIMEN', 'PUBLISHED_AGGREGATE', 'DERIVED_SUMMARY', 'UNKNOWN')
REVIEW_STATUSES = ('CURATED_IDENTITY', 'UNRESOLVED_IDENTITY', 'UNRESOLVED_OVERLAP')
# Review flags only: no confirmed campaign/specimen identities or numeric data.
UNRESOLVED_PUBLICATIONS = {
    '10.3390/polym15092011': 'ABS_AGGREGATE_OVERLAP_M05_M06_M07',
    '10.3390/polym16081106': 'ABS_AGGREGATE_OVERLAP_M05_M06_M07',
    '10.1016/j.prostr.2024.06.029': 'ABS_AGGREGATE_OVERLAP_M05_M06_M07',
}


def _text(value):
    return isinstance(value, str) and value.strip().casefold() not in (
        '', 'unknown', 'not reported', 'unreported', 'n/a', 'unspecified')


def normalize_doi(value):
    if not _text(value):
        return None
    value = value.strip().casefold()
    for prefix in ('https://doi.org/', 'http://doi.org/', 'https://dx.doi.org/',
                   'http://dx.doi.org/', 'doi:'):
        if value.startswith(prefix):
            value = value[len(prefix):].strip()
            break
    return value if re.fullmatch(r'10\.\d{4,9}/\S+', value) else None


def prepare_provenance_map(source_map):
    """Return a detached lookup and auditable metadata; fail closed if malformed."""
    metadata = {'schema': SCHEMA, 'map_id': None, 'sha256': None,
                'status': 'NOT_PROVIDED', 'source_authenticity_verified': False,
                'independent_validation_established': False, 'errors': []}
    if source_map is None:
        return metadata, None
    metadata['status'] = 'INVALID_PROVENANCE_MAP'
    source_map = deepcopy(source_map)
    try:
        metadata['sha256'] = sha256(json.dumps(source_map, sort_keys=True,
            separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    except (TypeError, ValueError):
        metadata['errors'].append({'reason': 'MAP_NOT_JSON_SERIALIZABLE'})
        return metadata, {}
    if not isinstance(source_map, dict) or source_map.get('schema') != SCHEMA:
        metadata['errors'].append({'reason': 'INVALID_MAP_SCHEMA'})
        return metadata, {}
    if not _text(source_map.get('map_id')):
        metadata['errors'].append({'reason': 'INVALID_MAP_ID'})
    else:
        metadata['map_id'] = source_map['map_id']
    observations = source_map.get('observations')
    if not isinstance(observations, list):
        metadata['errors'].append({'reason': 'INVALID_MAP_OBSERVATIONS'})
        return metadata, {}
    index, original_campaigns = {}, {}
    for position, entry in enumerate(observations):
        reasons = []
        if not isinstance(entry, dict):
            metadata['errors'].append({'entry': position, 'reason': 'INVALID_MAP_OBSERVATION'})
            continue
        for field in ('source_id', 'source_locator', 'review_locator'):
            if not _text(entry.get(field)):
                reasons.append('INVALID_MAP_' + field.upper())
        doi = normalize_doi(entry.get('source_doi'))
        if doi is None:
            reasons.append('INVALID_MAP_SOURCE_DOI')
        if entry.get('review_status') not in REVIEW_STATUSES:
            reasons.append('INVALID_MAP_REVIEW_STATUS')
        if entry.get('observation_kind') not in KINDS:
            reasons.append('INVALID_MAP_OBSERVATION_KIND')
        n = entry.get('n')
        if n is not None and (not isinstance(n, int) or isinstance(n, bool) or n <= 0):
            reasons.append('INVALID_MAP_N')
        if entry.get('observation_kind') == 'RAW_SPECIMEN' and n not in (None, 1):
            reasons.append('RAW_SPECIMEN_N_NOT_ONE')
        if entry.get('review_status') == 'CURATED_IDENTITY':
            for field in ('canonical_campaign_id', 'original_outcome_id'):
                if not _text(entry.get(field)):
                    reasons.append('INVALID_MAP_' + field.upper())
        else:
            if entry.get('canonical_campaign_id') is not None or entry.get('original_outcome_id') is not None:
                reasons.append('UNRESOLVED_MAP_HAS_ASSERTED_IDENTITY')
            if entry.get('review_status') == 'UNRESOLVED_OVERLAP' and not _text(entry.get('overlap_group_id')):
                reasons.append('MISSING_MAP_OVERLAP_GROUP_ID')
        if not reasons:
            key = (entry['source_id'], entry['source_locator'])
            if key in index:
                reasons.append('AMBIGUOUS_SOURCE_OBSERVATION')
            if entry['review_status'] == 'CURATED_IDENTITY':
                # Map IDs are globally scoped curator-assigned origins, not
                # source-local labels such as specimen S1 in unrelated labs.
                prior = original_campaigns.setdefault(entry['original_outcome_id'], entry['canonical_campaign_id'])
                if prior != entry['canonical_campaign_id']:
                    reasons.append('ORIGINAL_OUTCOME_SPLIT_ACROSS_CAMPAIGNS')
            index[key] = dict(entry, source_doi=doi)
        metadata['errors'].extend({'entry': position, 'reason': reason} for reason in reasons)
    if metadata['errors']:
        return metadata, {}
    metadata['status'] = 'INTERNALLY_VALIDATED_METADATA'
    return metadata, index


def observation_provenance(row, prepared_map):
    """Resolve one fully located observation; all supplied metadata is retained."""
    metadata, index = prepared_map
    supplied = deepcopy({k: v for k, v in row.items() if k not in ('context', 'value_mpa')})
    result = {'provided': supplied, 'identity_status': 'CALLER_DECLARED_UNVERIFIED',
              'publication_id': normalize_doi(row.get('source_doi', row.get('doi', row.get('study_id')))),
              'canonical_campaign_id': None, 'original_outcome_id': None,
              'observation_kind': row.get('observation_kind', 'UNKNOWN'),
              'overlap_group_id': None, 'errors': [], 'source_authenticity_verified': False}
    for field in ('source_id', 'source_doi', 'original_outcome_id', 'canonical_campaign_id'):
        if field in row and not _text(row[field]):
            result['errors'].append('INVALID_' + field.upper())
    if 'source_doi' in row and result['publication_id'] is None:
        result['errors'].append('INVALID_SOURCE_DOI')
    if result['observation_kind'] not in KINDS:
        result['errors'].append('INVALID_OBSERVATION_KIND')
    n = row.get('n')
    if n is not None and (not isinstance(n, int) or isinstance(n, bool) or n <= 0):
        result['errors'].append('INVALID_OBSERVATION_N')
    if result['publication_id'] in UNRESOLVED_PUBLICATIONS:
        result.update(identity_status='UNRESOLVED_OVERLAP',
                      overlap_group_id='ABS_AGGREGATE_OVERLAP_M05_M06_M07')
        result['errors'].append('UNRESOLVED_EXPERIMENTAL_OVERLAP')
        return result
    if index is None:
        # Preserve caller origin labels in provided metadata, but do not infer
        # a global specimen identity from a potentially local label.
        return result
    if metadata['status'] != 'INTERNALLY_VALIDATED_METADATA':
        result['identity_status'] = 'INVALID_PROVENANCE_MAP'
        result['errors'].append('INVALID_PROVENANCE_MAP')
        return result
    # No lookup/fallback using strength, sample labels, authors, or DOI alone.
    entry = index.get((row.get('source_id'), row.get('source_locator'))) if (
        _text(row.get('source_id')) and _text(row.get('source_locator'))) else None
    if entry is None:
        result['identity_status'] = 'UNMAPPED_SOURCE_OBSERVATION'
        result['errors'].append('SOURCE_OBSERVATION_NOT_MAPPED')
        return result
    if result['publication_id'] != entry['source_doi']:
        result['errors'].append('SOURCE_PUBLICATION_MISMATCH')
        return result
    result.update(identity_status=entry['review_status'],
                  observation_kind=entry['observation_kind'],
                  review_locator=entry['review_locator'],
                  overlap_group_id=entry.get('overlap_group_id'))
    if entry['review_status'] != 'CURATED_IDENTITY':
        result['errors'].append('UNRESOLVED_EXPERIMENTAL_OVERLAP' if entry['review_status'] == 'UNRESOLVED_OVERLAP'
                                else 'UNRESOLVED_EXPERIMENTAL_IDENTITY')
        return result
    result.update(canonical_campaign_id=entry['canonical_campaign_id'],
                  original_outcome_id=entry['original_outcome_id'])
    for field in ('canonical_campaign_id', 'original_outcome_id', 'observation_kind'):
        if field in row and row[field] != entry[field]:
            result['errors'].append(field.upper() + '_CONFLICT')
    if 'observation_kind' in row:
        result['observation_kind'] = row['observation_kind']
    return result


def specimen_locator(record):
    """A zip/archive may contain equal sheet/cell names in different files."""
    return record['file'] + '#' + record['sheet'] + '!' + record['peak_cell']


def catalog_provenance(entry, prepared_map):
    """Summarize observation identities without copying/changing numeric values."""
    references = []
    declared = set()
    explicit = entry.get('experimental_lineage_id')
    if _text(explicit):
        declared.add(explicit)
    specimens = entry.get('specimen_records')
    if isinstance(specimens, list) and specimens:
        for specimen in specimens:
            if _text(specimen.get('lineage')):
                declared.add(specimen['lineage'])
            references.append(dict(source_id=entry['source_id'], source_doi=entry['doi'],
                                   source_locator=specimen_locator(specimen), observation_kind='RAW_SPECIMEN'))
    else:
        for observation in entry.get('observations', []):
            reference = dict(source_id=entry['source_id'], source_doi=entry['doi'],
                             source_locator=observation.get('source_locator', entry.get('locator')))
            reference['observation_kind'] = observation.get('observation_kind',
                'DERIVED_SUMMARY' if str(observation.get('value_kind', '')).startswith('DERIVED')
                else 'PUBLISHED_AGGREGATE')
            references.append(reference)
    identities = [observation_provenance(row, prepared_map) for row in references]
    canonical = sorted({r['canonical_campaign_id'] for r in identities
                        if r['canonical_campaign_id'] and not r['errors']})
    if any(r['identity_status'] == 'UNRESOLVED_OVERLAP' for r in identities):
        declared.clear()
    effective = canonical if prepared_map[1] is not None else sorted(declared)
    return {'publication_ids': [normalize_doi(entry['doi'])] if normalize_doi(entry['doi']) else [],
            'declared_campaigns': sorted(declared), 'canonical_campaigns': canonical,
            'experimental_lineages': effective,
            'campaign_identity_status': 'CURATED_METADATA_SOURCE_AUTHENTICITY_UNVERIFIED' if canonical
                else 'CATALOG_DECLARED_UNVERIFIED' if effective else 'UNRESOLVED_CAMPAIGN_IDENTITY',
            'independent_validation_established': False,
            'observation_provenance': identities}
