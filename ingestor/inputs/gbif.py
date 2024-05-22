import httpx
from logging import getLogger
from typing import Any

logger = getLogger('endpoint.gbif')

url = 'https://api.gbif.org/v1/species/suggest'
media_url = 'https://api.gbif.org/v1/species/{gbif_id}/media'


async def gbif_search(search_string) -> list[dict[Any, Any]]:
    async with httpx.AsyncClient() as client:
        query_params = {
            'q': search_string
        }
        r = await client.get(url, params=query_params)
        if r.status_code == 200:
            try:
                data = r.json()
                for species in data:
                    logger.info(f'Parsing {species["key"]}')
                    end_of_records = False
                    media_query_params = {
                        'limit': 20,
                        'offset': 0
                    }
                    species['media'] = []
                    while not end_of_records:
                        mr = await client.get(media_url.format(gbif_id=species['key']), params=media_query_params)
                        if mr.status_code == 200:
                            try:
                                media_data = mr.json()
                            except Exception:
                                logger.exception(f'Failed to get the media for {species["key"]}')
                                end_of_records = True
                        else:
                            end_of_records = True
                        logger.info(f'Found {len(media_data["results"])} media results')

                        end_of_records = media_data['endOfRecords']
                        media_query_params['offset'] += media_query_params['limit']
                        species['media'].extend(media_data['results'])
                return data
            except Exception:
                logger.exception('Failed to parse the response to json')
        else:
            logger.error(f'URL: {url} responded with something other then 200: {r.status_code}, {r.text}')
        return []
