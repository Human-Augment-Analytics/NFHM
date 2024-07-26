# NOTE: Run the sql schema changes before running this script

import asyncpg
from logging import getLogger

logger = getLogger('outputs.mongo')

async def index_to_postgres(data: list[dict], conn: asyncpg.Connection, table: str, **kwargs):
    """
    Inserts data into a PostgreSQL table.

    Args:
        conn (asyncpg.Connection): The connection object to the PostgreSQL database.
        table (str): The name of the table to insert the data into.
        data (List[Any]): A list of maps to be inserted into the table.

    Returns:
        None
    """
    try:
        print(f'Inserting/updating data into table {table}')
        columns = ['media_uuid', 'specimen_uuid', 'collection_date', 'higher_taxon', 'common_name',
                   'scientific_name', 'recorded_by', 'location', 'tax_kingdom', 'tax_phylum',
                   'tax_class', 'tax_order', 'tax_family', 'tax_genus', 'catalog_number',
                   'earliest_epoch_or_lowest_series', 'earliest_age_or_lowest_stage',
                   'external_media_uri', 'embedding']

        values = []
        for record in data:
            values.append(tuple(record.get(col, None) for col in columns))

        # Construct the SQL query
        query = f'''
        INSERT INTO {table} ({', '.join(columns)})
        VALUES ({', '.join(f'${i+1}' for i in range(len(columns)))})
        ON CONFLICT (media_uuid) DO UPDATE SET
        {', '.join(f"{col} = EXCLUDED.{col}" for col in columns if col != 'media_uuid')}
        '''

        async with conn.transaction():
            await conn.executemany(query, values)

    except Exception as e:
        logger.error(f'Error inserting/updating data into table {table}: {e}')
        raise e
