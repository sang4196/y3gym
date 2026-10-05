"""Synthetic provider responses only. No network credentials or real API calls."""
import io
import json
import socket
from unittest.mock import patch, MagicMock
from urllib.parse import urlsplit, parse_qs
from django.test import SimpleTestCase, TestCase, override_settings
from django.db import connection
from bs4 import BeautifulSoup
from .naver_maps import geocode, GeocodingConfig, HOST, PATH, MAX_BYTES, page_config
from .models import Branch, SiteContent

CONFIG = GeocodingConfig(True, 'TEST_ID', 'TEST_SECRET')
ROW = {'x': '127.1', 'y': '37.2', 'roadAddress': 'TEST road', 'jibunAddress': ''}


def payload(rows=None, total=None):
    rows = [dict(ROW)] if rows is None else rows
    return {'status': 'OK', 'meta': {'totalCount': len(rows) if total is None else total}, 'addresses': rows}


class GeocodingTests(SimpleTestCase):
    def setUp(self):
        self.transport = patch('content.naver_maps.http.client.HTTPSConnection').start()
        self.addCleanup(patch.stopall)
        self.conn = self.transport.return_value
        self.response = self.conn.getresponse.return_value
        self.response.status = 200
        self.body(payload())

    def body(self, value, raw=False, headers=None):
        data = value if raw else json.dumps(value).encode()
        stream = io.BytesIO(data)
        self.response.read1.side_effect = stream.read1
        headers = {'Content-Type': 'application/json; charset=utf-8', **(headers or {})}
        self.response.getheader.side_effect = lambda name, default=None: headers.get(name, default)

    def test_disabled_missing_invalid_configuration_and_address_make_zero_requests(self):
        for config in [None, GeocodingConfig(False, 'TEST', 'SECRET'), GeocodingConfig(True),
                       GeocodingConfig(True, 'bad?query', 'SECRET'), GeocodingConfig(True, 'TEST', 'bad\nheader')]:
            self.assertIn(geocode('TEST address', config).code, ['disabled', 'not_configured'])
        for address in ['', ' ', None, 'x'*256, 'TEST\r\nheader']:
            self.assertEqual(geocode(address, CONFIG).code, 'invalid_address')
        self.transport.assert_not_called()
        self.assertNotIn('TEST_SECRET', repr(CONFIG))
        self.assertNotIn('TEST_ID', repr(CONFIG))

    def test_official_endpoint_headers_and_xy_no_exception_or_raw_data_exposure(self):
        result = geocode('TEST 주소 & 비밀?', CONFIG)
        self.assertEqual(result.code, 'single')
        self.assertEqual((result.candidates[0].latitude, result.candidates[0].longitude), (37.2,127.1))
        self.transport.assert_called_once_with(HOST, timeout=4)
        args, kwargs = self.conn.request.call_args
        self.assertEqual(args[0], 'GET')
        self.assertEqual(urlsplit(args[1]).path, PATH)
        self.assertEqual(parse_qs(urlsplit(args[1]).query), {'query':['TEST 주소 & 비밀?'], 'count':['10']})
        self.assertNotIn('TEST_SECRET',args[1])
        self.assertEqual(kwargs['headers']['X-NCP-APIGW-API-KEY'], 'TEST_SECRET')
        self.assertNotIn('TEST road', repr(result))
        self.conn.close.assert_called_once()

    def test_empty_multiple_and_truncated_candidates_never_auto_confirm(self):
        for rows,total,code in [([],0,'empty'),([ROW,ROW],2,'multiple'),([ROW],2,'multiple')]:
            self.body(payload(rows,total))
            self.assertEqual(geocode('TEST',CONFIG).code,code)

    def test_malformed_and_nonfinite_coordinate_responses(self):
        bad = [None, [], {}, {'status':'INVALID_REQUEST'}, payload([],1), payload([ROW],0), payload([ROW]*11)]
        for field in ['x','y']:
            for value in [None,True,127.0,'nan','Infinity','1e999','x', '181' if field=='x' else '91']:
                bad.append(payload([{**ROW,field:value}]))
        bad.extend([payload([{**ROW,'roadAddress':{'private':'error'}}]), payload([{**ROW,'roadAddress':'x'*513}])])
        for value in bad:
            with self.subTest(value=value):
                self.body(value)
                self.assertEqual(geocode('TEST',CONFIG).code,'invalid_response')
        for raw in [b'not JSON secret', b'\xff', b'{', b'['*2000]:
            self.body(raw,raw=True)
            self.assertEqual(geocode('TEST',CONFIG).code,'invalid_response')

    def test_auth_quota_redirect_and_server_errors_do_not_read_or_follow_body(self):
        for status,code in [(401,'authentication'),(403,'authentication'),(429,'quota'),(301,'upstream_error'),(500,'upstream_error'),(400,'upstream_error')]:
            self.response.status=status; self.response.read1.reset_mock()
            self.assertEqual(geocode('TEST',CONFIG).code,code)
            self.response.read1.assert_not_called()

    def test_content_type_size_and_declared_length_guards(self):
        for headers,code in [({'Content-Type':'text/html'},'invalid_response'),({'Content-Length':str(MAX_BYTES+1)},'response_too_large'),({'Content-Length':'9'*5000},'response_too_large')]:
            self.body(payload(),headers=headers)
            self.assertEqual(geocode('TEST',CONFIG).code,code)
        self.body(b'x'*(MAX_BYTES+1),raw=True)
        self.assertEqual(geocode('TEST',CONFIG).code,'response_too_large')

    def test_network_timeout_and_read_deadline_suppress_exception_text(self):
        for exc,code in [(socket.timeout('SECRET URL TEST'),'timeout'),(OSError('SECRET URL TEST'),'connection_error')]:
            self.conn.request.side_effect=exc
            with patch('sys.stderr',new_callable=io.StringIO) as err, patch('sys.stdout',new_callable=io.StringIO) as out:
                result=geocode('TEST',CONFIG)
            self.assertEqual(result.code,code)
            self.assertEqual(err.getvalue()+out.getvalue(),'')
            self.assertNotIn('SECRET',repr(result))
        self.conn.request.side_effect=None
        with patch('content.naver_maps.time.monotonic',side_effect=[0,5]):
            self.assertEqual(geocode('TEST',CONFIG).code,'timeout')


class MapPageTests(TestCase):
    def setUp(self):
        SiteContent(brand_name='TEST MAP').save()
        self.branch=Branch(name='TEST BRANCH',address='TEST address',phone='010-0000-0000',is_public=True)
        self.branch.save()

    @override_settings(NAVER_MAPS_ENABLED=True,NAVER_MAPS_PUBLIC_KEY_ID='TEST_PUBLIC')
    def test_current_null_contract_and_address_save_do_not_activate_maps(self):
        self.assertEqual(connection.vendor,'postgresql')
        with patch('content.naver_maps.http.client.HTTPSConnection') as transport:
            for address in ['TEST address','TEST changed address']:
                self.branch.address=address;self.branch.save()
                data=self.client.get('/api/v1/branches/').json()['items'][0]
                self.assertIsNone(data['location']);self.assertEqual(data['address'],address)
                response=self.client.get('/branches/')
                self.assertContains(response,address)
                self.assertNotContains(response,'naver-map-config')
                self.assertNotContains(response,'naver-maps.js')
            transport.assert_not_called()

    def test_configuration_and_map_spec_fail_closed(self):
        dto=[{'id':'1','address':'TEST address','map':{'provider':'naver','query':'TEST address'}}]
        self.assertIsNone(page_config(dto))
        self.assertIsNone(page_config(dto,enabled=True,key_id=''))
        self.assertEqual(page_config(dto,enabled=True,key_id='TEST'),{'keyId':'TEST','items':[{'id':'1','query':'TEST address'}]})
        for spec in [None, {}, {'provider':'other','query':'TEST address'}, {'provider':'naver','query':'OLD'}, {'provider':'naver','query':True}]:
            self.assertIsNone(page_config([{'id':'1','address':'TEST address','map':spec}],enabled=True,key_id='TEST'))

    @override_settings(NAVER_MAPS_ENABLED=True,NAVER_MAPS_PUBLIC_KEY_ID='TEST_PUBLIC')
    def test_legacy_confirmed_address_never_activates_naver_or_google(self):
        Branch.objects.filter(pk=self.branch.pk).update(address_confirmed=True)
        response=self.client.get('/branches/')
        self.assertNotContains(response,'naver-maps.js')
        self.assertNotContains(response,'google-maps.js')
        self.assertIsNone(self.client.get('/api/v1/branches/').json()['items'][0]['map'])
