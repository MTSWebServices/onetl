# Executing statements in Hive { #DBR-onetl-connection-db-connection-hive-execute-executing-statements-in-hive }

Use `Hive.execute(...)` to execute DDL and DML operations.

## Syntax support { #DBR-onetl-connection-db-connection-hive-execute-syntax-support }

This method supports **any** query syntax supported by Hive, like:

- ✅︎ `CREATE TABLE ...`, `CREATE VIEW ...`, and so on
- ✅︎ `LOAD DATA ...`, and so on
- ✅︎ `ALTER ...`
- ✅︎ `INSERT INTO ... SELECT ...`, and so on
- ✅︎ `DROP TABLE ...`, `DROP VIEW ...`, and so on
- ✅︎ `MSCK REPAIR TABLE ...`, and so on
- ✅︎ other statements not mentioned here
- ❌ `SET ...; SELECT ...;` - multiple statements not supported

!!! warning

    Actually, query should be written using [SparkSQL](https://spark.apache.org/docs/latest/sql-ref-syntax.html#ddl-statements) syntax, not HiveQL.

## Examples { #DBR-onetl-connection-db-connection-hive-execute-examples }

    ```python
        from onetl.connection import Hive

        hive = Hive(...)

        hive.execute("DROP TABLE schema.table")
        hive.execute(
            """
            CREATE TABLE schema.table (
                id NUMBER,
                key VARCHAR,
                value DOUBLE
            )
            PARTITION BY (business_date DATE)
            STORED AS orc
            """
        )
    ```

### Details { #DBR-onetl-connection-db-connection-hive-execute-details }

<!-- 
    ```{eval-rst}
    .. currentmodule:: onetl.connection.db_connection.hive.connection
    ```

    ```{eval-rst}
    .. automethod:: Hive.execute
    ```
 -->

::: onetl.connection.db_connection.hive.connection.Hive.execute
    options:
        members:
            - execute
