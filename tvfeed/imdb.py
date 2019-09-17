from enum import Enum
import io
import os
import urllib.request
import dbm
import gzip

import pyepgdb.network.dvbtuk as dvbtuk
from .config import config


class _Type (Enum):
    """Types of 'episodes' in IMDb datasets."""
    FILM = 'movie'
    SERIES = 'tvseries'


class _DataFile:
    """IMDb dataset opener.

name: Dataset ID

This is a context manager, and an iterator over TSV records (tuples of strings).

"""

    def __init__ (self, name):
        self._url = 'https://datasets.imdbws.com/{}.tsv.gz'.format(name)
        self._request = None
        self._tsv = None

    def __enter__ (self):
        self._request = urllib.request.urlopen(self._url)
        self._tsv = io.TextIOWrapper(gzip.GzipFile(fileobj=self._request))
        next(self) # hide header row
        return self

    def __exit__ (self, exc_type, exc_val, exc_tb):
        self._request.close()

    def __iter__ (self):
        return self

    def __next__ (self):
        return next(self._tsv).split('\t')


def _get_dataset ():
    with \
        _DataFile('title.basics') as basics, \
        _DataFile('title.ratings') as ratings \
    :

        while True:
            try:
                title_id, title_type, title, _, _, created_year, _, _, _ = \
                    next(basics)
                rating_id, rating, _ = next(ratings)
                while title_id < rating_id:
                    title_id, title_type, title, _, _, created_year, _, _, _ = \
                        next(basics)
                while rating_id < title_id:
                    rating_id, rating, _ = next(ratings)
            except StopIteration:
                break

            try:
                type_ = _Type(title_type.lower())
            except ValueError:
                continue
            yield (title, type_, created_year, rating)


def _get_db_path ():
    return os.path.join(config.DATASETS_STORE_PATH, 'imdb.db')


def _build_dataset_keys (title, type_, created_year):
    keys_parts = []
    if created_year is not None:
        keys_parts.append((title.lower(), type_.value, str(created_year)))
    keys_parts.append((title.lower(), type_.value, ''))
    return ['|'.join(part.replace('|', '') for part in parts).encode('utf8')
            for parts in keys_parts]


def update_dataset ():
    db_path = _get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with dbm.open(db_path, 'n') as dataset:
        for title, type_, created_year, rating in _get_dataset():
            for key in _build_dataset_keys(title, type_, created_year):
                if key in dataset and dataset[key] != rating:
                    dataset[key] = ''
                else:
                    dataset[key] = rating


def open_dataset ():
    return dbm.open(_get_db_path(), 'r')


def get_rating (dataset, programme, created_year):
    type_ = _Type.FILM if programme.genre == dvbtuk.Genre.FILM else _Type.SERIES
    for key in _build_dataset_keys(programme.title, type_, created_year):
        bytes_value = dataset.get()
        if bytes_value is not None and bytes_value != '':
            return float(bytes_value)
