import time
from xml.sax.saxutils import escape as escape_xml
import urllib.parse
import shutil

from .config import config

FEED_DATE_FORMAT = '%a, %d %b %Y %H:%M:%S %Z'
FEED_START_TEMPLATE = '''<?xml version="1.0"?>
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

    return _render_xml(FEED_ITEM_TEMPLATE, {
        'id': programme.id_,
        'title': programme.title,
        'link': 'https://www.imdb.com/find?q={}'.format(
            urllib.parse.quote(programme.title)),
        'description': '\n\n'.join(desc_parts),
        'published': start,
    })


def _feed_end ():
    return _render_xml(FEED_END_TEMPLATE, {})


def write_rss (programmes, out_file):
    out_file.write(_feed_start())
    for programme in programmes:
        out_file.write(_feed_item(programme))
    out_file.write(_feed_end())
    out_file.write('\n')
