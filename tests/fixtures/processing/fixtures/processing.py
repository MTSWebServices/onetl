import secrets
from contextlib import suppress
from importlib import import_module
from typing import NamedTuple

import pytest


class PreparedDbInfo(NamedTuple):
    full_name: str
    schema: str
    table: str


@pytest.fixture()
def processing(request, spark):
    processing_classes = {
        "clickhouse": ("tests.fixtures.processing.clickhouse", "ClickhouseProcessing"),
        "greenplum": ("tests.fixtures.processing.greenplum", "GreenplumProcessing"),
        "hive": ("tests.fixtures.processing.hive", "HiveProcessing"),
        "iceberg": ("tests.fixtures.processing.iceberg", "IcebergProcessing"),
        "mongodb": ("tests.fixtures.processing.mongodb", "MongoDBProcessing"),
        "mssql": ("tests.fixtures.processing.mssql", "MSSQLProcessing"),
        "mysql": ("tests.fixtures.processing.mysql", "MySQLProcessing"),
        "oracle": ("tests.fixtures.processing.oracle", "OracleProcessing"),
        "postgres": ("tests.fixtures.processing.postgres", "PostgresProcessing"),
        "kafka": ("tests.fixtures.processing.kafka", "KafkaProcessing"),
    }

    test_name_parts = set(request.function.__name__.split("_"))
    matches = set(processing_classes.keys()) & test_name_parts
    if not matches or len(matches) > 1:
        msg = (
            f"Test name {request.function.__name__} should have one "
            "of these components: {list(processing_classes.keys())}"
        )
        raise ValueError(
            msg,
        )

    db_storage_name = matches.pop()
    module_name, class_name = processing_classes[db_storage_name]
    module = import_module(module_name)
    db_processing = getattr(module, class_name)

    if db_storage_name in ("hive", "iceberg"):
        yield db_processing(spark, request)
    else:
        with db_processing() as result:
            yield result


@pytest.fixture
def get_schema_table(processing, worker_id):
    schema = processing.schema
    processing.create_schema(schema=schema)

    table = f"test_{worker_id}_{secrets.token_hex(3)}"
    full_name = f"{schema}.{table}"

    yield PreparedDbInfo(full_name=full_name, schema=schema, table=table)

    with suppress(Exception):
        processing.drop_table(
            table=table,
            schema=schema,
        )


@pytest.fixture
def prepare_schema_table(processing, get_schema_table):
    fields = {column_name: processing.get_column_type(column_name) for column_name in processing.column_names}
    _, schema, table = get_schema_table

    processing.create_table(schema=schema, table=table, fields=fields)

    return get_schema_table


@pytest.fixture
def load_table_data(prepare_schema_table, processing):
    _, schema, table = prepare_schema_table

    processing.insert_data(
        schema=schema,
        table=table,
        values=processing.create_pandas_df(),
    )

    return prepare_schema_table
