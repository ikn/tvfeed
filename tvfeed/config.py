import os
import json

import pyepgdb.network.dvbtuk as dvbtuk

PROGRAM_ID = 'tvfeed'

CONFIG_ROOT_PATH = os.environ.get(
    'XDG_CONFIG_HOME',
    os.path.join(os.path.expanduser('~'), '.config'))
CONFIG_PATH = os.path.join(CONFIG_ROOT_PATH, PROGRAM_ID, 'config.json')
DATA_ROOT_PATH = os.environ.get(
    'XDG_DATA_HOME',
    os.path.join(os.path.expanduser('~'), '.local', 'share'))
DATA_PATH = os.path.join(DATA_ROOT_PATH, PROGRAM_ID)
CACHE_ROOT_PATH = os.environ.get(
    'XDG_CACHE_HOME',
    os.path.join(os.path.expanduser('~'), '.cache'))
CACHE_PATH = os.path.join(CACHE_ROOT_PATH, PROGRAM_ID)


class Config:
    MIN_FILM_YEAR = 1990
    MIN_IMDB_RATING = 5
    ALLOWED_SERIES_GENRES = set((
        dvbtuk.Genre.UNKNOWN,
        dvbtuk.Genre.FILM,
    ))

    MATCHES_STORE_PATH = os.path.join(DATA_PATH, 'matches.db')
    FEED_LINK = 'http://localhost:9981/extjs.html'
    DATASETS_STORE_PATH = os.path.join(CACHE_PATH, 'datasets')

    def load (self):
        try:
            with open(CONFIG_PATH, 'r') as f:
                config_data = json.load(f)
        except FileNotFoundError:
            return

        if 'min_film_year' in config_data:
            self.MIN_FILM_YEAR = int(config_data['min_film_year'])
        if 'min_film_imdb_rating' in config_data:
            self.MIN_FILM_IMDB_RATING = int(config_data['min_film_imdb_rating'])
        if 'allowed_series_genres' in config_data:
            self.ALLOWED_SERIES_GENRES = set(
                getattr(dvbtuk.Genre, genre)
                for genre in config_data['allowed_series_genres']
            )
        if 'matches_store_path' in config_data:
            self.MATCHES_STORE_PATH = str(config_data['matches_store_path'])
        if 'feed_link' in config_data:
            self.FEED_LINK = str(config_data['feed_link'])
        if 'datasets_store_path' in config_data:
            self.DATASETS_STORE_PATH = str(config_data['datasets_store_path'])


config = Config()
config.load()
