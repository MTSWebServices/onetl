import pytest

from onetl.connection import MySQL
from onetl.db import DBWriter

pytestmark = pytest.mark.mysql


def test_mysql_writer_wrong_table_name(spark_mock):
    mysql_with_db = MySQL(host="some_host", user="user", database="database", password="passwd", spark=spark_mock)
    mysql_without_db = MySQL(host="some_host", user="user", password="passwd", spark=spark_mock)

    DBWriter(
        connection=mysql_with_db,
        target="table",
    )

    with pytest.raises(ValueError, match=r"Name should be passed in `schema\.name` format"):
        DBWriter(
            connection=mysql_without_db,
            target="table",  # Required format: target="schema.table"
        )
