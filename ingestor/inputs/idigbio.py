import httpx
from logging import getLogger
from typing import Any, Dict, List, Optional, Coroutine
import json
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

logger = getLogger("idigbio.gbif")

# iDigBio search wiki: https://github.com/iDigBio/idigbio-search-api/wiki
BASE_URL = "https://search.idigbio.org/v2"
SEARCH_URL = f"{BASE_URL}/search/records"
MEDIA_URL = f"{BASE_URL}/view/media/"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def fetch_with_retry(
    client: httpx.AsyncClient, url: str, params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    response = await client.get(url, params=params)
    response.raise_for_status()
    return response.json()


async def fetch_media_data(client: httpx.AsyncClient, uuid: str) -> Dict[str, Any]:
    try:
        return await fetch_with_retry(client, f"{MEDIA_URL}{uuid}")
    except httpx.HTTPStatusError as e:
        logger.error(
            f"HTTP error occurred while fetching media data for UUID {uuid}: {e}"
        )
    except Exception as e:
        logger.exception(
            f"An error occurred while fetching media data for UUID {uuid}: {e}"
        )
    return {}


async def idigbio_search(args: str, opts: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Fetches data from the iDigBio API based on the search parameters provided, and populates the media field with media data.
    Supports pagination via looping with jobs.

    Args:
        args (str): A JSON string containing search parameters and options.
        opts (Dict[str, Any]): A dictionary containing additional options, including the queue for pagination.

    Returns:
        List[Dict[str, Any]]: A list of records with populated media data.
    """
    params = json.loads(args)
    search_dict = params.get("search_dict", {})
    import_all = params.get("import_all", False)
    offset = params.get("offset", 0)
    page_size = 100

    query_params = {"rq": json.dumps(search_dict), "limit": page_size, "offset": offset}

    async with httpx.AsyncClient() as client:
        try:
            data = await fetch_with_retry(client, SEARCH_URL, query_params)

            if import_all and data["itemCount"] > offset + page_size:
                queue = opts.get("queue")
                if queue:
                    next_offset = offset + page_size
                    next_job = {
                        "search_dict": search_dict,
                        "import_all": True,
                        "offset": next_offset,
                    }
                    logger.info(
                        f'Enqueuing next job with offset {next_offset} out of {data["itemCount"]} records.'
                    )
                    await queue.enqueue("idigbio", json.dumps(next_job))
                else:
                    logger.warning("Queue not provided in opts, skipping pagination.")

            media_tasks: List[Coroutine[Any, Any, Dict[str, Any]]] = []
            for record in data["items"]:
                record["media"] = []
                for media_uuid in record["indexTerms"].get("mediarecords", []):
                    media_tasks.append(fetch_media_data(client, media_uuid))

            media_results = await asyncio.gather(*media_tasks)

            for record, media_data in zip(data["items"], media_results):
                if media_data:
                    record["media"].append(media_data)

            return data["items"]

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}")
        except Exception as e:
            logger.exception(f"An unexpected error occurred: {e}")

        return []
