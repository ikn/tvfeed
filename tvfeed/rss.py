import itertools
import re
import time
import os
import html
from xml.sax import saxutils
import urllib.parse
import shutil

from .config import config

# unicode characters which aren't valid in XML
# https://www.w3.org/TR/REC-xml/#charsets
XML_INVALID_CHARS = itertools.chain(
    range(0x0, 0x9), range(0xb, 0xd), range(0xe, 0x20))
XML_INVALID_PATTERN = re.compile(
    '[' + ''.join(chr(i) for i in XML_INVALID_CHARS) + ']')

FEED_DATE_FORMAT = '%a, %d %b %Y %H:%M:%S %Z'
FEED_START_TEMPLATE = '''<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
    <channel>
        <title>Upcoming television programmes</title>
        <link>{link}</link>
        <docs>http://blogs.law.harvard.edu/tech/rss</docs>
        <lastBuildDate>{date}</lastBuildDate>'''
FEED_ITEM_TEMPLATE = '''
        <item>
            <guid>{id}</guid>
            <title>{title}</title>
            <link>{link}</link>
            <description>{description}</description>
            <pubDate>{published}</pubDate>
            <published>{published}</published>
        </item>'''
FEED_END_TEMPLATE = '''
    </channel>
</rss>'''


def escape_xml (xml):
    return XML_INVALID_PATTERN.sub('', saxutils.escape(xml))


def _render_xml (template, params):
    return template.format(**{
        k: escape_xml(v) for k, v in params.items()
    })


def _feed_start ():
    return _render_xml(FEED_START_TEMPLATE, {
        'link': config.FEED_LINK,
        'date': time.strftime(FEED_DATE_FORMAT, time.gmtime()),
    })


def _feed_item (programme):
    start = time.strftime(FEED_DATE_FORMAT, programme.start)
    stop = time.strftime(FEED_DATE_FORMAT, programme.stop)

    desc_parts = [programme.subtitle, '{} - {}'.format(start, stop)]
    if programme.summary != programme.subtitle:
        desc_parts.append(programme.summary)
    desc = '\n'.join('<p>{}</p>'.format(html.escape(part))
                     for part in desc_parts)

    return _render_xml(FEED_ITEM_TEMPLATE, {
        'id': programme.id_,
        'title': programme.title,
        'link': 'https://www.imdb.com/find?q={}'.format(
            urllib.parse.quote(programme.title)),
        'description': desc,
        'published': start,
    })


def _feed_end ():
    return _render_xml(FEED_END_TEMPLATE, {})


def write_rss (programmes, out_file):
    os.makedirs(os.path.dirname(config.FEED_STORE_PATH), exist_ok=True)
    with open(config.FEED_STORE_PATH, 'a') as tmp_file:
        for programme in programmes:
            tmp_file.write(_feed_item(programme))

    out_file.write(_feed_start())
    with open(config.FEED_STORE_PATH, 'r') as tmp_file:
        shutil.copyfileobj(tmp_file, out_file)
    out_file.write(_feed_end())
    out_file.write('\n')
