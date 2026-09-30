Remove default value for `Hive.WriteOptions(format="orc")`.
Now default file format is configured using Spark `spark.sql.sources.default` which is usually `parquet`.
