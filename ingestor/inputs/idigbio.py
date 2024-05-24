import httpx
from logging import getLogger
from typing import Any
import asyncio
import json


logger = getLogger('endpoint.gbif')

# iDigBio search wiki: https://github.com/iDigBio/idigbio-search-api/wiki
url = 'https://search.idigbio.org/v2/search/records'
# media_url = 'https://api.gbif.org/v1/species/{gbif_id}/media'
media_url = 'https://search.idigbio.org/v2/view/media/{uuid}'


# Example: {'genus': 'Puma', hasMedia: True}
async def gbif_search(search_dict: dict) -> list[dict[Any, Any]]:
    """Fetches data from the iDigBio API based off of the search parameters provided, and populates the media field with media data.

    Parameters:
    argument1 (dict): The rq query search params for the iDigBio API.  If limiting to only records with media or images, include 'hasMedia': True and/or 'hasImages': True, respectively.

    Returns:
    int: Returns results of query as a list of dictionaries, with each dictionary populated with media fetched from the iDigBio media API.
    """

    async with httpx.AsyncClient() as client:
        query_params = {
            'rq': json.dumps(search_dict) # See https://github.com/iDigBio/idigbio-search-api/wiki/Query-Format#idigbio-query-format
        }
        r = await client.get(url, params=query_params)
        if r.status_code == 200:
            try:
                data = r.json()
                print(data)
                for record in data['items']:
                    logger.info(f'Parsing {record['uuid']}')
                    # media_query_params = {
                    #     'limit': 20,
                    #     'offset': 0
                    # }
                    record['media'] = []
                    for uuid in record['indexTerms']['mediarecords']:
                        mr = await client.get(media_url.format(uuid=uuid))
                        if mr.status_code == 200:
                            try:
                                media_data = mr.json()
                                print(media_data)
                            except Exception:
                                logger.exception(f'Failed to get the media with UUID {uuid}, belonging to record {record['uuid']}')
                        logger.info(f'Found media record for {uuid}')

                        record['media'].extend(media_data)
                return data
            except Exception:
                logger.exception('Failed to parse the response to json')
        else:
            logger.error(f'URL: {url} responded with something other then 200: {r.status_code}, {r.text}')
        return []


async def main():
    data = await gbif_search({'genus': 'Puma', 'hasMedia': True})
    with open('/workspaces/NFHM/ingestor/inputs/tmp.json', 'w') as file:
        json.dump(data, file)

asyncio.run(main())
