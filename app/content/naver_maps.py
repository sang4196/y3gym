"""DEV-05-A preparation only: no endpoint, persistence or environment key reader.

Callers must explicitly enable GeocodingConfig. No current product caller does.
DEV-05-B forbids persisting or reusing provider results. This adapter remains unused.
"""
from dataclasses import dataclass, field
import http.client
import json
import math
import re
import socket
import time
from urllib.parse import urlencode

HOST = 'maps.apigw.ntruss.com'
PATH = '/map-geocode/v2/geocode'
MAX_BYTES = 64 * 1024
TIMEOUT = 4
KEY_ID = re.compile(r'[A-Za-z0-9_-]{1,128}\Z')


@dataclass(frozen=True)
class GeocodingConfig:
    enabled: bool = False
    key_id: str = field(default='', repr=False)
    secret: str = field(default='', repr=False)


@dataclass(frozen=True)
class Candidate:
    latitude: float
    longitude: float
    road_address: str = field(repr=False)
    jibun_address: str = field(repr=False)


@dataclass(frozen=True)
class LookupResult:
    code: str
    candidates: tuple[Candidate, ...] = field(default=(), repr=False)


def valid_location(value):
    return isinstance(value, dict) and set(value) == {'latitude', 'longitude'} and all(
        type(value[k]) in (int, float) and math.isfinite(value[k]) and -bound <= value[k] <= bound
        for k, bound in [('latitude', 90), ('longitude', 180)]
    )


def _parse(raw):
    try:
        data = json.loads(raw)
        if not isinstance(data, dict) or data.get('status') != 'OK':
            return LookupResult('invalid_response')
        rows, meta = data.get('addresses'), data.get('meta')
        if not isinstance(rows, list) or len(rows) > 10 or not isinstance(meta, dict):
            return LookupResult('invalid_response')
        total = meta.get('totalCount')
        if type(total) is not int or total < len(rows) or (total > 0 and not rows):
            return LookupResult('invalid_response')
        candidates = []
        for row in rows:
            if not isinstance(row, dict) or any(not isinstance(row.get(k), str) or not row[k] or len(row[k]) > 32 for k in ('x', 'y')):
                return LookupResult('invalid_response')
            location = {'latitude': float(row['y']), 'longitude': float(row['x'])}
            if not valid_location(location):
                return LookupResult('invalid_response')
            labels = [row.get(k, '') for k in ('roadAddress', 'jibunAddress')]
            if not any(labels) or any(not isinstance(v, str) or len(v) > 512 or any(ord(c) < 32 for c in v) for v in labels):
                return LookupResult('invalid_response')
            candidates.append(Candidate(**location, road_address=labels[0], jibun_address=labels[1]))
        return LookupResult('empty' if total == 0 else 'single' if total == 1 else 'multiple', tuple(candidates))
    except (ValueError, TypeError, OverflowError, RecursionError):
        return LookupResult('invalid_response')


def geocode(address, config=None):
    """One bounded HTTPS request; secret only in headers, never in returned errors.

    The provider's official GET contract necessarily sends query=address upstream.
    No redirects/proxies/retries, provider error bodies or exception text exposed.
    There is deliberately no public proxy, admin action or production activation.
    """
    config = config or GeocodingConfig()
    if config.enabled is not True:
        return LookupResult('disabled')
    if not isinstance(config.key_id, str) or not KEY_ID.fullmatch(config.key_id) or not isinstance(config.secret, str) or not re.fullmatch(r'[!-~]{1,256}', config.secret):
        return LookupResult('not_configured')
    if not isinstance(address, str) or not address.strip() or len(address) > 255 or any(ord(c) < 32 for c in address):
        return LookupResult('invalid_address')
    connection = None
    try:
        # Direct HTTPSConnection does not use ambient proxy configuration or log URLs.
        deadline = time.monotonic() + TIMEOUT
        connection = http.client.HTTPSConnection(HOST, timeout=TIMEOUT)
        connection.request('GET', PATH + '?' + urlencode({'query': address.strip(), 'count': 10}),
                           headers={'Accept': 'application/json', 'X-NCP-APIGW-API-KEY-ID': config.key_id,
                                    'X-NCP-APIGW-API-KEY': config.secret})
        response = connection.getresponse()
        if response.status in (401, 403): return LookupResult('authentication')
        if response.status == 429: return LookupResult('quota')
        if response.status != 200: return LookupResult('upstream_error')
        if response.getheader('Content-Type', '').split(';')[0].strip().lower() != 'application/json':
            return LookupResult('invalid_response')
        length = response.getheader('Content-Length')
        if length is not None and (len(length) > 10 or not length.isdecimal() or int(length) > MAX_BYTES):
            return LookupResult('response_too_large')
        chunks, size = [], 0
        while True:
            if time.monotonic() >= deadline: return LookupResult('timeout')
            chunk = response.read1(min(8192, MAX_BYTES + 1 - size))
            if not chunk: break
            chunks.append(chunk)
            size += len(chunk)
            if size > MAX_BYTES: return LookupResult('response_too_large')
        return _parse(b''.join(chunks))
    except (TimeoutError, socket.timeout):
        return LookupResult('timeout')
    except (OSError, http.client.HTTPException):
        return LookupResult('connection_error')
    except UnicodeError:
        return LookupResult('invalid_address')
    finally:
        if connection is not None:
            connection.close()


def display_key():
    """Public SDK ID only. No environment/credential reader or REST secret."""
    from django.conf import settings
    value = settings.NAVER_MAPS_PUBLIC_KEY_ID
    return value if settings.NAVER_MAPS_ENABLED is True and isinstance(value, str) and KEY_ID.fullmatch(value) else ''


def page_config(branches, *, enabled=False, key_id=''):
    """Only own confirmed public address content, never provider results."""
    if enabled is not True or not isinstance(key_id, str) or not KEY_ID.fullmatch(key_id):
        return None
    items = []
    for branch in branches:
        pk, spec = branch.get('id'), branch.get('map')
        if (isinstance(pk, str) and re.fullmatch(r'[1-9][0-9]*', pk)
                and isinstance(spec, dict) and spec.get('provider') == 'naver'
                and isinstance(spec.get('query'), str) and spec['query'] == branch.get('address')
                and 0 < len(spec['query']) <= 255 and not any(ord(c) < 32 for c in spec['query'])):
            items.append({'id': pk, 'query': spec['query']})
    return {'keyId': key_id, 'items': items} if items else None
