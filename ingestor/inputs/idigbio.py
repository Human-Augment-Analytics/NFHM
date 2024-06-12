import json
from logging import getLogger
from typing import Any

from dateutil.parser import parse
import httpx
import pytz
from timezonefinder import TimezoneFinder

from .schema import Specimen

tf = TimezoneFinder()

logger = getLogger('idigbio.gbif')

# iDigBio search wiki: https://github.com/iDigBio/idigbio-search-api/wiki
url = 'https://search.idigbio.org/v2/search/records'
media_url = 'https://search.idigbio.org/v2/view/media/{uuid}'

async def idigbio_search(args: str, opts: dict) -> dict[str, Any]:
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
                parsed_data = {}
                for record in data['items']:
                    logger.info(f'Parsing {record["uuid"]}')
                    index_terms = record['indexTerms']
                    i_data = record['data']
                    # TODO use media id
                    # TODO each media record will be added with the specimen information
                    for uuid in index_terms['mediarecords']:
                        mr = await client.get(media_url.format(uuid=uuid))
                        if mr.status_code == 200:
                            try:
                                media_data = mr.json()
                            except Exception:
                                logger.exception(f'Failed to get the media with UUID {uuid}, belonging to record {record["uuid"]}')
                                continue
                        key = f'specimens:{uuid}'
                        data_dict = {
                            'key': key,
                            'occurenceid': index_terms.get('occurrenceid'),
                            'collectiondate': '',
                            'highertaxon': '',
                            'commonname': '',
                            'scientificname': '',
                            'recordedby': '',
                            'location': '',
                            'kingdom': '',
                            'phylum': '',
                            'class_': '',
                            'order': '',
                            'family': '',
                            'catalognumber': '',
                            'earliest_epoch_or_lowest_series': '',
                            'earliest_age_or_lowest_stage': '',
                            'access_rights': '',
                            'raw': i_data,
                            'media': []
                        }
                        logger.info(f'Found media record for {uuid}')
                        data_dict['media'].append(media_data)

                        lon = index_terms['geopoint']['lon']
                        lat = index_terms['geopoint']['lat']
                        tz = pytz.timezone(tf.timezone_at(lng=lon, lat=lat))

                        try:
                            parsed = parse(index_terms['datecollected'])
                            aware = parsed.replace(tzinfo=tz)
                            data_dict['collectiondate'] = aware.timestamp()
                        except Exception:
                            print(f'Failed to parse {index_terms["datecollected"]}')
                            continue

                        data_dict['highertaxon'] = index_terms['highertaxon']
                        data_dict['commonname'] = index_terms['commonname']
                        data_dict['scientificname'] = index_terms['scientificname']
                        data_dict['recordedby'] = i_data.get('dwc:recordedBy')
                        data_dict['location'] = [lon, lat]
                        data_dict['kingdom'] = index_terms.get('kingdom')
                        data_dict['phylum'] = index_terms.get('phylum')
                        data_dict['class'] = index_terms.get('class')
                        data_dict['order'] = index_terms.get('order')
                        data_dict['family'] = index_terms.get('family')
                        data_dict['catalognumber'] = index_terms['catalognumber']
                        data_dict['earliest_age_or_lowest_stage'] = index_terms.get(
                            'earliestageorloweststage')
                        data_dict['earliest_epoch_or_lowest_series'] = index_terms.get(
                            'earliestepochorlowestseries')
                        data_dict['access_rights'] = i_data.get('dcterms:accessRights')
                        specimen = Specimen(**data_dict)
                        parsed_data[key] = specimen.model_dump()
                if (import_all):
                    # Push job for next page of results onto queue
                    queue = opts['queue']
                    offset = params.get('offset', 0) + pagesize
                    next_job = { 'search_dict': search_dict, 'import_all': True, 'offset': offset }
                    if (data['itemCount'] > offset):
                        logger.info(f'Enqueuing next job with offset {offset} out of {data["itemCount"]} records.')
                        await queue.enqueue('idigbio', json.dumps(next_job))

                return parsed_data
            except Exception:
                logger.exception('Failed to parse the response to json')
        else:
            logger.error(f'URL: {url} responded with something other then 200: {r.status_code}, {r.text}')
        return []
