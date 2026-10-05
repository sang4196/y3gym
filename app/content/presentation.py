"""HTML presentation only. Callers pass materialized public DTOs, never draft rows."""
from bs4 import BeautifulSoup


def excerpt(value, limit=160, *, html=False):
    if html:
        soup = BeautifulSoup(value or '', 'html.parser')
        for tag in soup(['script', 'style']):
            tag.decompose()
        # Block boundaries need spaces; inline emphasis must not split a word.
        for tag in soup(['p', 'h2', 'li', 'br']):
            tag.insert_before(' ')
            tag.insert_after(' ')
        value = soup.get_text()
    text = ' '.join((value or '').split())
    return text if len(text) <= limit else text[:limit-1].rstrip() + '…'


def page_meta(title, shell, description='', *, section='', noindex=False):
    brand = shell.get('brand_name') or ''
    return {'title': f'{title} | {brand}' if brand and title != brand else title,
            'description': excerpt(description), 'section': section, 'noindex': noindex}


def post_meta(post, shell, *, preview=False):
    return page_meta(post['title'] or '제목 없는 초안', shell,
                     excerpt(post['body_html'], html=True) or post['title'],
                     section='posts', noindex=preview)
