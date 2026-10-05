from django.test import SimpleTestCase
from django.core.exceptions import ValidationError
from .google_maps import parse_embed_input, validate_embed_url

URL='https://www.google.com/maps/embed?pb=!1m18!2m3!1d123!2d456!3d789!2sTEST%20ONLY'

class EmbedParserTests(SimpleTestCase):
    def test_url_and_official_copy_shape_preserve_opaque_pb(self):
        self.assertEqual(parse_embed_input(URL),URL)
        self.assertEqual(parse_embed_input(''), '')
        self.assertEqual(parse_embed_input(f' <iframe src="{URL}" width="600" height="450" style="border:0;" allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe> '),URL)
        self.assertEqual(parse_embed_input(f'<iframe title="TEST" src="{URL.replace("!", "&#33;")}"></iframe>'),URL)
    def test_url_boundaries(self):
        bad=[URL.replace('https:','http:'),URL.replace('www.google.com','www.google.com.evil.test'),URL.replace('www.google.com','evil@www.google.com'),URL.replace('www.google.com','www.google.com:8443'),URL.replace('/maps/embed','/maps/embed/v1/place'),URL+'#x',URL+'#',URL+'&pb=!2',URL+'&key=TEST',URL+'&x=1',URL.replace('pb=','q='),URL.replace('pb=','%70b='),URL.replace('!1','%0A!1'),URL+'%ZZ',URL+'%3Cscript%3E',URL+'\\x',URL+'\t',URL+'x'*4096,'https://maps.app.goo.gl/TEST','https://www.google.com/maps?q=TEST&output=embed']
        for value in bad:
            with self.subTest(value=value[:100]),self.assertRaises(ValidationError):validate_embed_url(value)
    def test_markup_boundaries_and_no_recovery_of_executable_input(self):
        bad=[f'<iframe src="{URL}" src="{URL}"></iframe>',f'<iframe src="{URL}" onload="alert(1)"></iframe>',f'<iframe src="{URL}" srcdoc="x"></iframe>',f'<iframe src="{URL}"></iframe><script>alert(1)</script>',f'<div><iframe src="{URL}"></iframe></div>',f'<iframe src="{URL}">text</iframe>',f'<iframe src="{URL}"/>',f'<iframe src="{URL}">',f'<!--x--><iframe src="{URL}"></iframe>',f'<!DOCTYPE html><iframe src="{URL}"></iframe>',f'<iframe src="{URL}"></iframe><iframe src="{URL}"></iframe>','x'*8193]
        for value in bad:
            with self.subTest(value=value[:100]),self.assertRaises(ValidationError):parse_embed_input(value)

    def test_url_controls_before_trimming_and_trailing_query_separator(self):
        for value in ['\n'+URL,URL+'\n',URL+'&']:
            with self.assertRaises(ValidationError):parse_embed_input(value)
