import httpx
from logging import getLogger
from typing import Any
import json

logger = getLogger('idigbio.gbif')

# iDigBio search wiki: https://github.com/iDigBio/idigbio-search-api/wiki
url = 'https://search.idigbio.org/v2/search/records'
media_url = 'https://search.idigbio.org/v2/view/media/{uuid}'

async def idigbio_search(args: str, opts: dict) -> list[dict[Any, Any]]:
    """Fetches data from the iDigBio API based off of the search parameters provided, and populates the media field with media data.  Supports pagination via looping with jobs.

    Parameters in Stringified Dictionary Format:
    search_dict (dict): The rq query search params for the iDigBio API.  A stringified dictionary.  If limiting to only records with media or images,
        include 'hasMedia': True and/or 'hasImages': True, respectively.

    import_all (bool): If true, function will fetch all pages of results until the end of the search results. This is done by sequentially adding new jobs to idigbio redis queue.
        Results size could be millions of records, and hundreds of gigibytes of data.  If false, will only fetch the first page of results. Default is false.  Default page size is 100 records.

    Example Usage:
        idigbio_search(json.dumps({ search_dict: {'genus': 'Puma', 'hasMedia': True}, import_all: True, offset: 100 }), { 'queue': queue }))

    Returns:
    List: Returns results of query as a list of dictionaries, with each dictionary populated with media fetched from the iDigBio media API.
    """

    async with httpx.AsyncClient() as client:
        params = json.loads(args)
        search_dict = params.get('search_dict', {})
        import_all = params.get('import_all', False)
        pagesize = 100
        query_params = {
            'rq': json.dumps(search_dict) # See https://github.com/iDigBio/idigbio-search-api/wiki/Query-Format#idigbio-query-format
        }
        if (import_all):
            query_params['limit'] = pagesize
            query_params['offset'] = params.get('offset', 0)
        
        r = await client.get(url, params=query_params)
        if r.status_code == 200:
            try:
                data = r.json()
                for record in data['items']:
                    logger.info(f'Parsing {record['uuid']}')
                    record['media'] = []
                    for uuid in record['indexTerms']['mediarecords']:
                        mr = await client.get(media_url.format(uuid=uuid))
                        if mr.status_code == 200:
                            try:
                                media_data = mr.json()
                            except Exception:
                                logger.exception(f'Failed to get the media with UUID {uuid}, belonging to record {record['uuid']}')
                        logger.info(f'Found media record for {uuid}')
                        record['media'].append(media_data)
                if (import_all):
                    # Push job for next page of results onto queue
                    queue = opts['queue']
                    offset = params.get('offset', 0) + pagesize
                    next_job = { 'search_dict': search_dict, 'import_all': True, 'offset': offset }
                    if (data['itemCount'] > offset):
                        logger.info(f'Enqueuing next job with offset {offset} out of {data['itemCount']} records.')
                        await queue.enqueue('idigbio', json.dumps(next_job))

                return data['items']
            except Exception:
                logger.exception('Failed to parse the response to json')
        else:
            logger.error(f'URL: {url} responded with something other then 200: {r.status_code}, {r.text}')
        return []
