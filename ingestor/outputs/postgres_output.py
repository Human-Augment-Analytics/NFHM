# NOTE: Run the sql schema changes before running this script

import asyncpg
from logging import getLogger
from typing import List

logger = getLogger('outputs.mongo')


async def index_to_postgres(conn: asyncpg.Connection, table: str, data: List[map]):
    """
    Inserts data into a PostgreSQL table.

    Args:
        conn (asyncpg.Connection): The connection object to the PostgreSQL database.
        table (str): The name of the table to insert the data into.
        data (List[Any]): A list of maps to be inserted into the table.

    Returns:
        None
    """
    async with conn.transaction():
        for record in data:
            await conn.execute(
                f'''
                INSERT INTO {table} (collection_date, higher_taxon, common_name, scientific_name, recorded_by, location, tax_kingdom, tax_phylum, tax_class, tax_order, tax_family, tax_genus, catalog_number, earliest_epoch_or_lowest_series, earliest_age_or_lowest_stage, external_media_uri, embedding)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                ''',
                record['collection_date'], record['higher_taxon'], record['common_name'], record['scientific_name'], record['recorded_by'], record['location'], record['tax_kingdom'], record['tax_phylum'], record['tax_class'], record['tax_order'], record['tax_family'], record['tax_genus'], record['catalog_number'], record['earliest_epoch_or_lowest_series'], record['earliest_age_or_lowest_stage'], record['external_media_uri'], record['embedding']
            )