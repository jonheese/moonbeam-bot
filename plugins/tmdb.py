from collections import OrderedDict
from urllib.parse import quote_plus
from . import plugin

import requests


class TMDBPlugin(plugin.Plugin):
    def __init__(self):
        super().__init__()
        self._TMDB_API_URL = self._config.get("TMDB_API_URL")
        self._TMDB_API_KEY = self._config.get("TMDB_API_KEY")
        self._TMDB_MAX_RESULTS = self._config.get("TMDB_MAX_RESULTS", 3)

    def receive(self, request):
        if super().receive(request) is False:
            return False

        if request['text'].lower().startswith("moonbeam movies"):
            self._log.debug(f"Got movie request: {request['text']}")
            command = request['text'].split()

            movie = ' '.join(command.split()[2:])

            if not movie:
                return {
                    'channel': request['channel'],
                    'text': 'A movie title must be specified.'

                }

            # Todo check for status -CC
            api_config = requests.get(
                f'{self._TMDB_API_URL}/configuration',
                params={
                    'api_key': self._TMDB_API_KEY
                }
            ).json()

            lookup = requests.get(
                f'{self._TMDB_API_URL}/search/movie',
                params={
                    'api_key': self._TMDB_API_KEY,
                    'query': quote_plus(movie)
                }
            ).json()

            movie_base = 'https://www.themoviedb.org/movie'
            media_base = api_config['images']['secure_base_url']

            # Get the smallest image, slack will still crop it
            # maybe add in flight resizing at some point -CC
            image_size = api_config['images']['poster_sizes'][0]

            result_num = 0

            if lookup['total_result'] == 0:
                return {
                    'channel': request['channel'],
                    'text': f"Sorry, couldn't find any results for {movie}."
                }

            blocks = []
            for result in lookup['results']:
                movie_uri = '/'.join([
                    movie_base,
                    str(result['id'])
                ])

                image_uri = '/'.join([
                    media_base,
                    image_size,
                    result['poster_path'] if result['poster_path'] else ''
                ])

                release_year = result['release_date'].split('-')[0]

                blocks.append({
                    'type': 'section',
                    'text': {
                        'type': 'mrkdwn',
                        'text': f'*<{movie_uri}|{result["title"]}>* ({release_year})\n{result["overview"]}'
                    },
                    'accessory': {
                        'type': 'image',
                        'image_url': image_uri,
                        'alt_text': result['title']
                    }
                })

                blocks.append({'type': 'divider'})

                result_num += 1
                if result_num == self._TMDB_MAX_RESULTS:
                    break

            blocks.append(OrderedDict({
                'type': 'header',
                'text': {
                    'type': 'plain_text',
                    'text': 'Powered by https://www.themoviedb.org'
                }
            }))

            return {
                'channel': request['channel'],
                'blocks': blocks
            }
