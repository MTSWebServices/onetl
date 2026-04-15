import pytest

from onetl.connection import Clickhouse
from onetl.db import DBWriter

pytestmark = pytest.mark.clickhouse


def test_clickhouse_writer_wrong_table_name(spark_mock):
    clickhouse_with_db = Clickhouse(
        host="some_host", user="user", database="database", password="passwd", spark=spark_mock
    )
    clickhouse_without_db = Clickhouse(host="some_host", user="user", password="passwd", spark=spark_mock)

    DBWriter(
        connection=clickhouse_with_db,
        target="table",
    )

    with pytest.raises(ValueError, match=r"Name should be passed in `schema\.name` format"):
        DBWriter(
            connection=clickhouse_without_db,
            target="table",  # Required format: target="schema.table"
        )
