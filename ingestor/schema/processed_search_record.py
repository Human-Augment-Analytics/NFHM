from typing import Optional, TypedDict
from datetime import date
import torch


class ProcessedSearchRecord(TypedDict):
    specimen_uuid: str
    scientific_name: Optional[str]
    external_media_uri: Optional[str]
    media_uuid: Optional[str]
    catalog_number: Optional[str]
    recorded_by: Optional[str]
    tax_kingdom: Optional[str]
    tax_phylum: Optional[str]
    tax_class: Optional[str]
    tax_order: Optional[str]
    tax_family: Optional[str]
    tax_genus: Optional[str]
    common_name: Optional[str]
    higher_taxon: Optional[str]
    earliest_epoch_or_lowest_series: Optional[str]
    earliest_age_or_lowest_stage: Optional[str]
    collection_date: Optional[date]
    location: Optional[str]
    embedding: Optional[str]
    tensor_embedding: Optional[torch.Tensor]
    model: str
    pretrained: str
    embed_version: str
