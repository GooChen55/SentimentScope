"""All seven platform ingestion mappings must remain compatible with preserved tables."""
from app.db.content_schema import Base
from app.deep_sentiment.ingest import TABLES


def test_all_ingestion_id_fields_exist_in_content_schema():
    for mappings in TABLES.values():
        for table_name, id_column in mappings:
            table = Base.metadata.tables[table_name]
            assert 'id' in table.c and id_column in table.c
