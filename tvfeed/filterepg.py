import itertools
import re
import sys
import os
import dbm

import pyepgdb
import pyepgdb.network.dvbtuk as dvbtuk

from . import rss, imdb
from .config import config

# regexes matching episode numbers in programme description strings
# group 's': series number
# group 'e': episode number
EPISODE_NUMBER_PATTERNS = [re.compile(r, re.I) for r in (
    r'(^|\W)(s ?(?P<s>\d+)( |/|, )?)?ep? ?(?P<e>\d+)($|\W)',
    r'(^|\W)(?P<s>\d+)/(?P<e>\d+)($|\W)',
    r'(^|\W)(?P<s>\d+) of (?P<e>\d+)($|\W)',
    r'(^|\W)episode (?P<e>\d+)($|\W)',
)]
# regexes matching release years in programme description strings
# group 'n': year
CREATED_YEAR_PATTERNS = [re.compile(r, re.I) for r in (
    r'\((?P<n>\d\d\d\d)\)',
    r'\[(?P<n>\d\d\d\d)\]',
    r'(^|[.,)] +)(?P<n>\d\d\d\d)\.',
)]


def get_episode_number (desc):
    for pattern in EPISODE_NUMBER_PATTERNS:
        match = pattern.search(desc)
        if match is not None:
            res = match.groupdict()
            series = res.get('s')
            return (None if series is None else int(series), int(res['e']))
    return (None, None)


def get_created_year (desc):
    for pattern in CREATED_YEAR_PATTERNS:
        match = pattern.search(desc)
        if match is not None:
            return int(match.groupdict()['n'])


def check_rating (imdb_programme):
    return (imdb_programme is None or
            imdb_programme['rating'] >= config.MIN_IMDB_RATING)


def check_previously_matched (programme, series, episode, created_year,
                              previous_matches):
    """Find programme in dict previous_matches, or add it and return true."""
    key = '{}|{}|{}|{}'.format(programme.title.replace('|', ''),
                               series, episode, created_year)
    if key in previous_matches:
        return False
    else:
        previous_matches[key] = ''
        return True


def filter_programmes (programmes):
    os.makedirs(os.path.dirname(config.MATCHES_STORE_PATH), exist_ok=True)
    with \
        dbm.open(config.MATCHES_STORE_PATH, 'c') as previous_matches, \
        imdb.open_dataset() as imdb_dataset \
    :

        matched_programme_ids = set()
        for programme in programmes:
            desc = ' '.join((
                '' if programme.subtitle is None else programme.subtitle,
                '' if programme.summary is None else programme.summary,
            ))
            series, episode = get_episode_number(desc)
            created_year = get_created_year(desc)
            # filter to films, and series first-episodes
            filters_match = (
                programme.genre == dvbtuk.Genre.FILM and
                created_year is not None and
                created_year >= config.MIN_FILM_YEAR
            ) or (
                programme.genre in config.ALLOWED_SERIES_GENRES and
                episode == 1
            )

            imdb_programme = imdb.get_programme(
                imdb_dataset, programme, created_year)

            if (filters_match and
                check_rating(imdb_programme) and
                # skip programmes seen this execution
                programme.id_ not in matched_programme_ids and
                # skip programmes seen in previous executions
                check_previously_matched(programme, series, episode,
                                         created_year, previous_matches)
            ):
                matched_programme_ids.add(programme.id_)
                yield (programme, imdb_programme)


def run ():
    rss.write_rss(
        filter_programmes(dvbtuk.parse(pyepgdb.parse(sys.stdin.buffer))),
        sys.stdout)
