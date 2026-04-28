# Writing to Iceberg using `DBWriter` { #DBR-onetl-connection-db-connection-iceberg-write-writing-to-iceberg-using-dbwriter }

For writing data to Iceberg, use [DBWriter][DBR-onetl-db-writer].

## Examples { #DBR-onetl-connection-db-connection-iceberg-write-examples }

``` python
from onetl.connection import Iceberg
from onetl.db import DBWriter

iceberg = Iceberg(catalog_name="my_catalog", ...)

df = ...  # data is here

writer = DBWriter(
    connection=iceberg,
    target="my_schema.my_table",  # catalog name is already defined in connection
    options=Iceberg.WriteOptions(
        if_exists="append",
    ),
)

writer.run(df)
```

## Options { #DBR-onetl-connection-db-connection-iceberg-write-options }

::: onetl.connection.db_connection.iceberg.options.IcebergWriteOptions
    options:
        members: [if_exists, table_properties]
