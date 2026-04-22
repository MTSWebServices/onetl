# Reading from Iceberg using `DBReader` { #DBR-onetl-connection-db-connection-iceberg-read-reading-from-iceberg-using-dbreader }

[DBReader][DBR-onetl-db-reader] supports [strategy][DBR-onetl-strategy-read-strategies] for incremental data reading, but does not support custom queries, like `JOIN`.

## Supported DBReader features { #DBR-onetl-connection-db-connection-iceberg-read-supported-dbreader-features }

- ✅︎ `columns`
- ✅︎ `where`
- ✅︎ `hwm`, supported strategies:
    - ✅︎ [`snapshot-strategy`][DBR-onetl-strategy-snapshot-strategy]
    - ✅︎ [`incremental-strategy`][DBR-onetl-connection-db-connection-clickhouse-read-incremental-strategy]
    - ✅︎ [`snapshot-batch-strategy`][DBR-onetl-strategy-snapshot-batch-strategy]
    - ✅︎ [`incremental-batch-strategy`][DBR-onetl-strategy-incremental-batch-strategy]
- ✅︎ `hint`
- ❌ `df_schema`
- ❌ `options` (only Spark config params are used)

!!! warning

    `columns`, `where` and `hwm.expression` should be written using [SparkSQL](https://spark.apache.org/docs/latest/sql-ref-syntax.html#data-retrieval-statements) syntax.

## Examples { #DBR-onetl-connection-db-connection-iceberg-read-examples }

Snapshot strategy:

``` python
from onetl.connection import Iceberg
from onetl.db import DBReader

iceberg = Iceberg(catalog_name="my_catalog", ...)

reader = DBReader(
    connection=iceberg,
    source="my_schema.table",  # catalog is already defined in connection
    columns=["id", "key", "value", "updated_dt"],
    where="key = 'something'",
)
df = reader.run()
```

Incremental strategy:

``` python
from onetl.connection import Iceberg
from onetl.db import DBReader
from onetl.strategy import IncrementalStrategy

iceberg = Iceberg(catalog_name="my_catalog", ...)

reader = DBReader(
    connection=iceberg,
    source="my_schema.table",  # catalog is already defined in connection
    columns=["id", "key", "value", "updated_dt"],
    where="key = 'something'",
    hwm=DBReader.AutoDetectHWM(name="iceberg_hwm", expression="updated_dt"),
)

with IncrementalStrategy():
    df = reader.run()
```

## Recommendations { #DBR-onetl-connection-db-connection-iceberg-read-recommendations }

### Select only required columns { #DBR-onetl-connection-db-connection-iceberg-read-select-only-required-columns }

Instead of passing `"*"` in `DBReader(columns=[...])` prefer passing exact column names. This drastically reduces the amount of data read by Spark.
