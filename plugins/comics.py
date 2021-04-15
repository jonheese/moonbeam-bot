from collections import OrderedDict
from . import plugin

import arrow
import requests


class MarvelComicsAPI(requests.Session):

    def __init__(self, url, public_key, private_key, **kwargs):

        from hashlib import md5

        self.url = url
        self.public_key = public_key
        self.private_key = private_key

        # Marvel requires an incremented 'ts' param on each call
        self.ts = 0

        self.hash = md5(
            f'{self.ts}{self.private_key}{self.public_key}'.encode()
        ).hexdigest()

        super().__init__()

    def request(self, method, endpoint, headers=None, params={}, data=None, json=None, check_response=False, **kwargs):

        url = f'{self.url}/{endpoint}'

        params.update(
            {
                'apikey': self.public_key,
                'hash': self.hash,
                'ts': self.ts,

            }
        )

        result = super().request(
            method,
            url,
            params,
            data=data,
            json=json,
            headers=headers,
            **kwargs
        )

        if check_response:
            result.raise_for_status()

        return result

    def comics_generator(self, range_begin, range_end):
        offset = 0
        complete = False
        while not complete:
            releases = self.get(
                '/comics',
                params={
                    'dateRange': f'{range_begin},{range_end}',
                    'orderBy': 'onsaleDate',
                    'offset': offset
                }
            )

            result = releases.json()
            offset += result['data']['count']

            if result['data']['count'] == 0:
                complete = True

            for issue in result['data']['results']:
                yield issue

    def get_releases_by_date(self, range_begin, range_end, variants=False):

        result = []

        for comic in self.comics_generator(range_begin, range_end):


            if variants is False and 'Variant' in comic['title']:
                continue

            onsale = next(x for x in comic['dates'] if x['type'] == 'onsaleDate')
            onsale = arrow.get(onsale['date']).format('dddd, MMMM DD, YYYY')
            thumbnail = comic['thumbnail']['path'] + '.' + comic['thumbnail']['extension']

            detail_url = next(x for x in comic['urls'] if x['type'] == 'detail')

            price = f'${comic["prices"][-1]["price"]}'
            result.append(
                {
                    'title': comic['title'],
                    'onsale': onsale,
                    'thumbnail': thumbnail,
                    'detail': detail_url['url'],
                    'price': price
                }
            )

        return result


class DCComicsAPI(requests.Session):
    # TODO
    def __init__(self, **kwargs):
        pass


class ComicsPlugin(plugin.Plugin):
    def receive(self, request):

        import re

        if super().receive(request) is False:
            return False

        if request['text'].lower().startswith("moonbeam comics"):
            self._log.debug(f"Got comics request: {request['text']}")

            # Pivot on DC/Marvel later
            comic_api = MarvelComicsAPI(
                self._config.get('MARVEL_API_URL'),
                public_key=self._config.get('MARVEL_API_PUBLIC_KEY'),
                private_key=self._config.get('MARVEL_API_PRIVATE_KEY')
            )

            # Get week boundaries
            now = arrow.now()
            date_start = now.floor('week').format('YYYY-MM-DD')
            date_end = now.ceil('week').format('YYYY-MM-DD')

            if re.search(r'new releases$', request['text'], re.IGNORECASE):
                new_releases = comic_api.get_releases_by_date(
                    date_start,
                    date_end
                )

                blocks = []
                for release in new_releases:
                    blocks.append({
                        'type': 'section',
                        'text': {
                            'type': 'mrkdwn',
                            'text': f'*<{release["detail"]}|{release["title"]}>*\n*{release["price"]}*\n{release["onsale"]}'
                        },
                        'accessory': {
                            'type': 'image',
                            'image_url': release['thumbnail'],
                            'alt_text': release['title']
                        }
                    })

                    blocks.append({'type': 'divider'})

                blocks.append(OrderedDict({
                    'type': 'header',
                    'text': {
                        'type': 'plain_text',
                        'text': 'Data provided by Marvel. © 2021 MARVEL'
                    }
                }))

                return {
                    'channel': request['channel'],
                    'blocks': blocks
                }
