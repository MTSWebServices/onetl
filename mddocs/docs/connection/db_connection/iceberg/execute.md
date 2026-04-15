# Executing statements in Iceberg { #DBR-onetl-connection-db-connection-iceberg-execute-executing-statements-in-iceberg }

Use `Iceberg.execute(...)` to execute DDL and DML operations.

!!! warning

    In DML/DDL queries **table names must include catalog prefix**.

## Syntax support { #DBR-onetl-connection-db-connection-iceberg-execute-syntax-support }

This method supports **any** query syntax supported by Iceberg (Spark
SQL), like:

-   ✅︎ `CREATE TABLE ...`, `CREATE VIEW ...`
-   ✅︎ `INSERT INTO ... SELECT ...`, `MERGE INTO ...`
-   ✅︎ `ALTER TABLE ... ADD COLUMN`, `ALTER TABLE ... DROP COLUMN`
-   ✅︎ `DROP TABLE ...`, `DROP VIEW ...`
-   ✅︎ `REPLACE TABLE ...`
-   ✅︎ other statements supported by Iceberg
-   ❌ `SET ...; SELECT ...;` - multiple statements not supported

## Examples { #DBR-onetl-connection-db-connection-iceberg-execute-examples }

``` python
from onetl.connection import Iceberg

iceberg = Iceberg(catalog_name="my_catalog", ...)

iceberg.execute("DROP TABLE my_catalog.my_schema.my_table")
iceberg.execute(
    """
    CREATE TABLE my_catalog.my_schema.my_table (
        id BIGINT,
        key STRING,
        value DOUBLE
    )
    USING iceberg
    """,
)
```

### Details { #DBR-onetl-connection-db-connection-iceberg-execute-details }

::: onetl.connection.db_connection.iceberg.connection.Iceberg.execute
