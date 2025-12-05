.. _greenplum-prerequisites:

Prerequisites
=============

Version Compatibility
---------------------

* Greenplum server versions:
    * Officially declared: 5.x, 6.x, and 7.x (which requires ``Greenplum.get_packages(package_version="2.3.0")`` or higher)
    * Actually tested: 6.23, 7.0
* Spark versions: 3.2.x (Spark 3.3+ is not supported yet)
* Java versions: 8 - 11

See `official documentation <https://docs.vmware.com/en/VMware-Greenplum-Connector-for-Apache-Spark/2.2/greenplum-connector-spark/release_notes.html>`_.

Installing PySpark
------------------

To use Greenplum connector you should have PySpark installed (or injected to ``sys.path``)
BEFORE creating the connector instance.

See :ref:`install-spark` installation instruction for more details.

Download VMware package
-----------------------

To use Greenplum connector you should download connector ``.jar`` file from
`VMware website <https://network.tanzu.vmware.com/products/vmware-greenplum#/releases/1413479/file_groups/16966>`_
and then pass it to Spark session.

.. warning::

    Please pay attention to :ref:`Spark & Scala version compatibility <spark-compatibility-matrix>`.

.. warning::

    There are issues with using package of version 2.3.0/2.3.1 with Greenplum 6.x - connector can
    open transaction with ``SELECT * FROM table LIMIT 0`` query, but does not close it, which leads to deadlocks
    during write.

There are several ways to do that. See :ref:`java-packages` for details.

.. note::

    If you're uploading package to private package repo, use ``groupId=io.pivotal`` and ``artifactoryId=greenplum-spark_2.12``
    (``2.12`` is Scala version) to give uploaded package a proper name.

Interaction Spark ↔ Greenplum
-----------------------------

This connector is **very** different from regular Postgres connector.

Postgres connector connects directly to Postgres host via JDBC driver:

* Spark driver → Postgres host (get query column names and types, create target table)
* Spark executors → Postgres host (send/fetch actual data)

Data should **NEVER** be send via Greenplum master (coordinator) using regular Postgres connector, as it's very easy to overload coordinator
by sending hundreds and thousands of gigabytes of data.

Instead, Greenplum connector uses `gpfdist protocol <https://docs.vmware.com/en/VMware-Greenplum/7/greenplum-database/admin_guide-external-g-using-the-greenplum-parallel-file-server--gpfdist-.html#about-gpfdist-setup-and-performance-1>`_ with a bit complicated schema:

* Spark driver → Greenplum master (get query column names and types, create target table)
* Spark executors → Greenplum master (create `EXTERNAL TABLEs <https://docs.vmware.com/en/VMware-Greenplum/7/greenplum-database/ref_guide-sql_commands-CREATE_EXTERNAL_TABLE.html>`_)
* Greenplum segments → Spark executors (send/fetch actual data via ``EXTERNAL TABLE``)

More details can be found in `official documentation <https://docs.vmware.com/en/VMware-Greenplum-Connector-for-Apache-Spark/2.3/greenplum-connector-spark/overview.html>`_.

Configuring the connector
-------------------------

Each Spark executor starts a ``gpfdist`` server, and each Greeplum **segment** connect to this server.
Greenplum segment should know server's IP address/hostname and a port number.

This target IP and port range should be added to firewall ``ALLOW`` rule on Spark host/cluter with sourceIP = Greenplum network.
Otherwise connection cannot be established.

More details can be found in official documentation:
    * `port requirements <https://docs.vmware.com/en/VMware-Greenplum-Connector-for-Apache-Spark/2.3/greenplum-connector-spark/sys_reqs.html#network-port-requirements>`_
    * `format of server.port value <https://docs.vmware.com/en/VMware-Greenplum-Connector-for-Apache-Spark/2.3/greenplum-connector-spark/options.html#server.port>`_
    * `port troubleshooting <https://docs.vmware.com/en/VMware-Greenplum-Connector-for-Apache-Spark/2.3/greenplum-connector-spark/troubleshooting.html#port-errors>`_

spark.master=local
~~~~~~~~~~~~~~~~~~

Set ``gpfdist`` server host
^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, Greenplum connector tries to resolve current host IP, and then pass it to Greenplum segment.
On some hosts it works as-is, without any additional configuration. In others it's not.

The most common error is that Greenplum segment receives ``127.0.0.1`` IP address (loopback interface)
This is usually caused ``/etc/hosts`` content like this:

.. code:: text

    127.0.0.1 localhost real-host-name

.. code:: bash

    $ hostname -f
    localhost

    $ hostname -i
    127.0.0.1

Reading/writing data to Greenplum will fail with following exception:

.. code-block:: text

    org.postgresql.util.PSQLException: ERROR: connection with gpfdist failed for
    "gpfdist://127.0.0.1:49152/local-1709739764667/exec/driver",
    effective url: "http://127.0.0.1:49152/local-1709739764667/exec/driver":
    error code = 111 (Connection refused);  (seg3 slice1 12.34.56.78:10003 pid=123456)

There are 2 ways to fix that:

* Explicitly pass your host IP address to connector, like this

  .. code-block:: python

      import os

      # host IP, accessible from GP segments
      os.environ["SPARK_LOCAL_IP"] = "192.168.1.1"

      # !!!SET IP BEFORE CREATING SPARK SESSION!!!
      spark = ...

      greenplum = Greenplum(
          ...,
          extra={
              # connector will read IP from this environment variable
              "server.hostEnv": "env.SPARK_LOCAL_IP",
          },
          spark=spark,
      )

  More details can be found in `official documentation <https://docs.vmware.com/en/VMware-Greenplum-Connector-for-Apache-Spark/2.3/greenplum-connector-spark/options.html#server.hostenv>`_.

* Update ``/etc/hosts`` file to include real host IP:

  .. code:: text

      127.0.0.1 localhost
      # this IP should be accessible from GP segments
      192.168.1.1 real-host-name

  This requires root privileges on host, not everyone can do this.
  Also this doesn't work with dynamic IP addresses.

Set ``gpfdist`` server port
^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, Spark executors can start ``gpfdist`` server on *any* random port number.
You can limit port range using ``extra`` option:

.. code:: python

    greenplum = Greenplum(
        ...,
        extra={
            "server.port": "41000-42000",  # !!! JUST AN EXAMPLE !!!
        },
    )

Number of ports in this range should be at least ``number of parallel running Spark sessions on host`` * ``number of executors per session``.

spark.master=yarn
~~~~~~~~~~~~~~~~~

Set ``gpfdist`` server host
^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, Greenplum connector tries to resolve current host IP, and then pass it to Greenplum segment.
Usually there are no issues with that, connector just works as-is, without any adjustments.

The most common error is that Greenplum segment receives ``127.0.0.1`` IP address (loopback interface)
instead of external IP of Hadoop data/compute node. There are 3 ways to fix it:

* Pass node hostname instead of IP address to Greenplum segment:

  .. code-block:: python

      greenplum = Greenplum(
          ...,
          extra={
              "server.useHostname": "true",
          },
      )

  This may require configuring DNS on each Greenplum segment to properly resolve Hadoop node hostname → some IP.

  More details can be found in `official documentation <https://docs.vmware.com/en/VMware-Greenplum-Connector-for-Apache-Spark/2.3/greenplum-connector-spark/options.html#server.usehostname>`_.

* Set network interface name to get IP address from:

  .. code-block:: python

     greenplum = Greenplum(
         ...,
         extra={
             "server.nic": "eth0",
         },
     )

  You can get list of network interfaces using this command.

  .. note::

    This command should be executed on Hadoop cluster node, **not** Spark driver host!

  .. code-block:: bash

    $ ip address
    1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
        inet 127.0.0.1/8 scope host lo
        valid_lft forever preferred_lft forever
    2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
        inet 192.168.1.1/24 brd 192.168.1.255 scope global dynamic noprefixroute eth0
        valid_lft 83457sec preferred_lft 83457sec

  Note that in this case **each** Hadoop cluster node node should have network interface with name ``eth0``,
  which may not be the case.

  More details can be found in `official documentation <https://docs.vmware.com/en/VMware-Greenplum-Connector-for-Apache-Spark/2.3/greenplum-connector-spark/options.html#server.nic>`_.

* Update ``/etc/hosts`` on each Hadoop cluster node to include its IP address:

  .. code:: text

      127.0.0.1 localhost
      # this IP should be accessible from GP segments
      192.168.1.1 real-host-name

  This requires root privileges on host, not everyone can do this.
  Also this doesn't work with dynamic IP addresses.

Set ``gpfdist`` server port
^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, Spark executors can start ``gpfdist`` server on *any* random port number.
You can limit port range using ``extra`` option:

.. code:: python

    greenplum = Greenplum(
        ...,
        extra={
            "server.port": "41000-42000",  # !!! JUST AN EXAMPLE !!!
        },
    )

Number of ports in this range should be at least ``number of parallel running Spark sessions per node`` * ``number of executors per session`` / ``number of Hadoop nodes``.

spark.master=k8s
~~~~~~~~~~~~~~~~

Before starting Spark session, you should to create a Kubernetes `Ingress <https://kubernetes.io/docs/concepts/services-networking/ingress/>`_ object:

.. code-block:: yaml
    :caption: ingress.yaml

    apiVersion: networking.k8s.io/v1
    kind: Ingress
    metadata:
        name: gpfdist-ingress
        namespace: mynamespace
        annotations:
            nginx.ingress.kubernetes.io/ssl-redirect: "false"
            nginx.ingress.kubernetes.io/force-ssl-redirect: "false"
    spec:
        rules:
        - http:
            paths:
            - path: /
              pathType: Prefix
              backend:
                service:
                    name: gpfdist-default
                    port:
                    number: 50000

    ## RETURNED FROM K8S API RESPONSE ##
    # status:
    #     loadBalancer:
    #         ingress:
    #             - ip: 11.22.33.44

Then add special Spark listener to Spark session config, and specify ingress' load balancer IP or domain name with a port number:

.. code:: python

    spark = (
        SparkSession.builder.config("spark.master", "k8s://...")
        .config("spark.extraListeners", "org.greenplum.GpfdistIngressListener")
        .config("spark.kubernetes.namespace", "mynamespace")
        .config("spark.greenplum.k8s.ingress.name", "gpfdist-ingress")  # ingress name
        .config("spark.greenplum.gpfdist.host", "11.22.33.44")  # ingress IP/domain name
        .config("spark.greenplum.gpfdist.listen-port", "50000")  # ingress port
        .config(
            "spark.greenplum.gpfdist.is-ssl", "false"
        )  # true for ingress with TLS enabled
    ).getOrCreate()

Set fixed port for ``gpfdist`` server to listen on:

.. code:: python

    greenplum = Greenplum(
        ...,
        extra={
            "server.port": "50000",  # should match ingress port
        },
    )

Set number of connections
-------------------------

.. warning::

    This is very important!!!

    If you don't limit number of connections, you can exceed the `max_connections <https://docs.vmware.com/en/VMware-Greenplum/7/greenplum-database/admin_guide-client_auth.html#limiting-concurrent-connections#limiting-concurrent-connections-2>`_
    limit set on the Greenplum side. It's usually not so high, e.g. 500-1000 connections max,
    depending on your Greenplum instance settings and using connection balancers like ``pgbouncer``.

    Consuming all available connections means **nobody** (even admin users) can connect to Greenplum!

Each task running on the Spark executor makes its own connection to Greenplum master node.
To avoid opening too many connections to Greenplum master (coordinator), you should limit number of tasks.

* Reading about ``5-10Gb`` of data requires about ``3-5`` parallel connections.
* Reading about ``20-30Gb`` of data requires about ``5-10`` parallel connections.
* Reading about ``50Gb`` of data requires ~ ``10-20`` parallel connections.
* Reading about ``100+Gb`` of data requires ``20-30`` parallel connections.
* Opening more than ``30-50`` connections is not recommended.

Max number of parallel tasks is ``N executors * N cores-per-executor``, so this can be adjusted using Spark session configuration:

.. tabs::

    .. code-tab:: py Spark with master=local

        spark = (
            SparkSession.builder
            # Spark will run with 5 threads in local mode, allowing up to 5 parallel tasks
            .config("spark.master", "local[5]")
        ).getOrCreate()

        # Set connection pool size AT LEAST to number of executors + 1 for driver
        Greenplum(
            ...,
            extra={
                "pool.maxSize": 6,  # 5 executors + 1 driver
            },
        )

    .. code-tab:: py Spark with master=yarn or master=k8s, dynamic allocation

        spark = (
            SparkSession.builder
            .config("spark.master", "yarn")
            # Spark will start MAX 10 executors with 1 core each (dynamically), so max number of parallel jobs is 10
            .config("spark.dynamicAllocation.maxExecutors", 10)
            .config("spark.executor.cores", 1)
        ).getOrCreate()

    .. code-tab:: py Spark with master=yarn or master=k8s, static allocation

        spark = (
            SparkSession.builder
            .config("spark.master", "yarn")
            # Spark will start EXACTLY 10 executors with 1 core each, so max number of parallel jobs is 10
            .config("spark.executor.instances", 10)
            .config("spark.executor.cores", 1)
        ).getOrCreate()

See `connection pooling <https://docs.vmware.com/en/VMware-Greenplum-Connector-for-Apache-Spark/2.3/greenplum-connector-spark/using_the_connector.html#jdbcconnpool>`_
documentation.

Greenplum side adjustments
--------------------------

Allow connecting to Greenplum master
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ask your Greenplum cluster administrator to allow your user to connect to Greenplum master (coordinator),
e.g. by updating ``pg_hba.conf`` file.

More details can be found in `official documentation <https://docs.vmware.com/en/VMware-Greenplum/7/greenplum-database/admin_guide-client_auth.html#limiting-concurrent-connections#allowing-connections-to-greenplum-database-0>`_.

Provide required grants
~~~~~~~~~~~~~~~~~~~~~~~

Ask your Greenplum cluster administrator to set following grants for a user:

.. tabs::

    .. code-tab:: sql Read + Write

        -- get access to get tables metadata & cluster information
        GRANT SELECT ON information_schema.tables TO username;
        GRANT SELECT ON pg_attribute TO username;
        GRANT SELECT ON pg_class TO username;
        GRANT SELECT ON pg_namespace TO username;
        GRANT SELECT ON pg_settings TO username;
        GRANT SELECT ON pg_stats TO username;
        GRANT SELECT ON gp_distributed_xacts TO username;
        GRANT SELECT ON gp_segment_configuration TO username;
        -- Greenplum 5.x only
        GRANT SELECT ON gp_distribution_policy TO username;

        -- allow creating external tables in the same schema as source/target table
        GRANT USAGE ON SCHEMA myschema TO username;
        GRANT CREATE ON SCHEMA myschema TO username;
        ALTER USER username CREATEEXTTABLE(type = 'readable', protocol = 'gpfdist') CREATEEXTTABLE(type = 'writable', protocol = 'gpfdist');

        -- allow read access to specific table (to get column types)
        -- allow write access to specific table
        GRANT SELECT, INSERT ON myschema.mytable TO username;

    .. code-tab:: sql Read only

        -- get access to get tables metadata & cluster information
        GRANT SELECT ON information_schema.tables TO username;
        GRANT SELECT ON pg_attribute TO username;
        GRANT SELECT ON pg_class TO username;
        GRANT SELECT ON pg_namespace TO username;
        GRANT SELECT ON pg_settings TO username;
        GRANT SELECT ON pg_stats TO username;
        GRANT SELECT ON gp_distributed_xacts TO username;
        GRANT SELECT ON gp_segment_configuration TO username;
        -- Greenplum 5.x only
        GRANT SELECT ON gp_distribution_policy TO username;

        -- allow creating external tables in the same schema as source table
        GRANT USAGE ON SCHEMA schema_to_read TO username;
        GRANT CREATE ON SCHEMA schema_to_read TO username;
        -- yes, ``writable`` for reading from GP, because data is written from Greenplum to Spark executor.
        ALTER USER username CREATEEXTTABLE(type = 'writable', protocol = 'gpfdist');

        -- allow read access to specific table
        GRANT SELECT ON schema_to_read.table_to_read TO username;

More details can be found in `official documentation <https://docs.vmware.com/en/VMware-Greenplum-Connector-for-Apache-Spark/2.3/greenplum-connector-spark/install_cfg.html#role-privileges>`_.
