# NOTE: Run the sql schema changes before running this script

import asyncpg
from typing import List, Any
from logging import getLogger
from schema.processed_search_record import ProcessedSearchRecord


logger = getLogger("outputs.postgres")


async def index_to_postgres(
    data: List[ProcessedSearchRecord],
    conn: asyncpg.Connection,
    table: str,
) -> None:
    """
    Inserts or updates data into a PostgreSQL table.

    Args:
        data (List[ProcessedRecord]): A list of ProcessedRecord objects to be inserted into the table.
        conn (asyncpg.Connection): The connection object to the PostgreSQL database.
        table (str): The name of the table to insert the data into.

    Raises:
        ValueError: If the data list is empty or if required fields are missing.
        asyncpg.PostgresError: If there's an error during the database operation.
    """
    if not data:
        logger.warning("No data to insert/update")
        return

    columns = [
        "media_uuid",
        "specimen_uuid",
        "collection_date",
        "higher_taxon",
        "common_name",
        "scientific_name",
        "recorded_by",
        "location",
        "tax_kingdom",
        "tax_phylum",
        "tax_class",
        "tax_order",
        "tax_family",
        "tax_genus",
        "catalog_number",
        "earliest_epoch_or_lowest_series",
        "earliest_age_or_lowest_stage",
        "external_media_uri",
        "embedding",
    ]

    values: List[tuple[Any, ...]] = []

    for record in data:
        if record.get("media_uuid") is None:
            logger.warning(f"Skipping record without media_uuid: {record}")
            continue
        values.append(tuple(record.get(col) for col in columns))

    if not values:
        logger.warning("No valid records to insert/update")
        return

    placeholders = ", ".join(f"${i}" for i in range(1, len(columns) + 1))
    update_set = ", ".join(
        f"{col} = EXCLUDED.{col}" for col in columns if col != "media_uuid"
    )

    query = f"""
    INSERT INTO {table} ({', '.join(columns)})
    VALUES ({placeholders})
    ON CONFLICT (media_uuid) DO UPDATE SET {update_set}
    """

    try:
        async with conn.transaction():
            await conn.executemany(query, values)
        logger.info(f"Successfully inserted/updated {len(values)} records into {table}")
    except asyncpg.PostgresError as e:
        logger.error(f"Error inserting/updating data into table {table}: {e}")
        raise
