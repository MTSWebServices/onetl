# Reading from Iceberg using `Iceberg.sql` { #DBR-onetl-connection-db-connection-iceberg-sql-reading-from-iceberg-using-iceberg-sql }

`Iceberg.sql` allows passing custom SQL query, but does not support incremental strategies.

!!! warning

    Unlike DBReader, in SQL queries **table names must include catalog prefix**.

## Syntax support { #DBR-onetl-connection-db-connection-iceberg-sql-syntax-support }

Only queries with the following syntax are supported:

- ✅︎ `SELECT ... FROM ...`
- ✅︎ `WITH alias AS (...) SELECT ...`
- ❌ `SET ...; SELECT ...;` - multiple statements not supported

## Examples { #DBR-onetl-connection-db-connection-iceberg-sql-examples }

``` python
from onetl.connection import Iceberg

iceberg = Iceberg(catalog_name="my_catalog", ...)
df = iceberg.sql(
    """
    SELECT
        id,
        key,
        CAST(value AS string) value,
        updated_at
    FROM
        my_catalog.my_schema.my_table
    WHERE
        key = 'something'
    """,
)
```

## Recommendations { #DBR-onetl-connection-db-connection-iceberg-sql-recommendations }

### Select only required columns { #DBR-onetl-connection-db-connection-iceberg-sql-select-only-required-columns }

Avoid `SELECT *`. List only required columns to minimize I/O and improve query performance.

### Use filters { #DBR-onetl-connection-db-connection-iceberg-sql-use-filters }

Include `WHERE` clauses on columns to allow Spark to prune unnecessary data, e.g. operators `=`, `>`, `<`, `BETWEEN`.
