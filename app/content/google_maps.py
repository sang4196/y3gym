"""Google Maps share/embed input. Pure parsing: no fetch, geocoding or pb decoding."""
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit, parse_qsl, unquote
from django.core.exceptions import ValidationError

MAX_URL = 4096
MAX_INPUT = 8192
MESSAGE = 'Google 지도의 공유 → 지도 퍼가기 → HTML 복사 코드 또는 그 코드의 https://www.google.com/maps/embed?pb=… 주소를 입력하세요.'
ATTRIBUTES = {'src', 'width', 'height', 'style', 'loading', 'allowfullscreen', 'referrerpolicy', 'title', 'class', 'frameborder'}

def invalid():
    raise ValidationError(MESSAGE)

def validate_embed_url(value):
    if not isinstance(value, str) or not value or len(value) > MAX_URL:
        invalid()
    if re.search(r'[\s\x00-\x1f\x7f<>"\'`\\]', value) or re.search(r'%(?![0-9A-Fa-f]{2})', value):
        invalid()
    try:
        url = urlsplit(value)
        pairs = parse_qsl(url.query, keep_blank_values=True, strict_parsing=True, max_num_fields=2)
    except ValueError:
        invalid()
    if not value.startswith('https://www.google.com/maps/embed?pb=') or url.scheme != 'https' or url.netloc != 'www.google.com' or url.path != '/maps/embed' or url.fragment or '#' in value:
        invalid()
    if len(pairs) != 1 or pairs[0][0] != 'pb' or not url.query.startswith('pb=') or not pairs[0][1].startswith('!'):
        invalid()
    # pb remains opaque. Only unsafe URL characters/control bytes are rejected.
    if re.search(r'[\x00-\x1f\x7f<>"\'`\\]', unquote(url.query)):
        invalid()
    return value

class EmbedParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.state = 0
        self.src = None
    def handle_starttag(self, tag, attrs):
        if tag != 'iframe' or self.state != 0:
            invalid()
        names = [name for name, value in attrs]
        if len(names) != len(set(names)) or set(names) - ATTRIBUTES or names.count('src') != 1:
            invalid()
        self.src = dict(attrs)['src']
        self.state = 1
    def handle_endtag(self, tag):
        if tag != 'iframe' or self.state != 1:
            invalid()
        self.state = 2
    def handle_startendtag(self, tag, attrs):
        invalid()
    def handle_data(self, data):
        if data.strip(): invalid()
    def handle_comment(self, data): invalid()
    def handle_decl(self, decl): invalid()
    def handle_pi(self, data): invalid()
    def unknown_decl(self, data): invalid()

def parse_embed_input(value):
    if not isinstance(value, str) or len(value) > MAX_INPUT:
        invalid()
    if not value.lstrip().startswith('<') and re.search(r'[\x00-\x1f\x7f]', value):
        invalid()
    value = value.strip()
    if not value:
        return ''
    if value.startswith('<'):
        parser = EmbedParser()
        try:
            parser.feed(value)
            parser.close()
        except (ValueError, AssertionError):
            invalid()
        if parser.state != 2:
            invalid()
        value = parser.src
    return validate_embed_url(value)

def map_dto(branch):
    if not branch.is_public or not branch.google_map_confirmed or not branch.address or branch.google_map_address != branch.address:
        return None
    try:
        url = validate_embed_url(branch.google_embed_url)
    except ValidationError:
        return None
    return {'provider': 'google', 'mode': 'embed', 'embed_url': url}
