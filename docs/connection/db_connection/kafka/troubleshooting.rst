.. _kafka-troubleshooting:

Kafka Troubleshooting
=====================

.. note::

    General guide: :ref:`troubleshooting`.

Cannot connect using ``SSL`` protocol
-------------------------------------

Please check that certificate files are not Base-64 encoded.

``Group authorization failed``
------------------------------

Before Spark 3.4.0, Kafka connector read topic offsets using Consumer API. To ensure that each time offsets fetched from Kafka are fresh,
Spark driver generates random ``groupId``, and passes it to Kafka. If Kafka ACL limits which groupIds can access specific topic, this will fail.

To prevent this, explicitly pass groupId ``Kafka(extra={"group.id": "something")``, matching the ACL rule.

Spark driver hangs while fetching offsets from Kafka
----------------------------------------------------

This may be the case on Spark 3.2.x - 3.3.x there Spark driver uses Consumer API to fetch offsets. Since `Spark 3.4.0 <https://issues.apache.org/jira/browse/SPARK-40844>`_ connector uses Admin API.
You can force Spark to use Admin API by setting Spark session config ``spark.sql.streaming.kafka.useDeprecatedOffsetFetching=false``.
