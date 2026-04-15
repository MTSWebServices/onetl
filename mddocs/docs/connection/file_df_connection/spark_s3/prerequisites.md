# Prerequisites { #DBR-onetl-connection-file-df-connection-spark-s3-prerequisites }

## Version Compatibility { #DBR-onetl-connection-file-df-connection-spark-s3-prerequisites-version-compatibility }

- Spark versions: 3.2.x - 3.5.x
- Java versions: 8 - 20

## Installing PySpark { #DBR-onetl-connection-file-df-connection-spark-s3-prerequisites-installing-pyspark }

To use SparkS3 connector you should have PySpark installed (or injected to `sys.path`)
BEFORE creating the connector instance.

See [installation instruction][DBR-onetl-install-spark] for more details.

## Connecting to S3 { #DBR-onetl-connection-file-df-connection-spark-s3-prerequisites-connecting-to-s3 }

### Bucket access style { #DBR-onetl-connection-file-df-connection-spark-s3-prerequisites-bucket-access-style }

AWS and some other S3 cloud providers allows bucket access using domain style only, e.g. `https://mybucket.s3provider.com`.

Other implementations, like Minio, by default allows path style access only, e.g. `https://s3provider.com/mybucket`
(see [MINIO_DOMAIN](https://min.io/docs/minio/linux/reference/minio-server/minio-server.html#envvar.MINIO_DOMAIN)).

You should set `path_style_access` to `True` or `False`, to choose the preferred style.

### Authentication { #DBR-onetl-connection-file-df-connection-spark-s3-prerequisites-authentication }

Different S3 instances can use different authentication methods, like:

- `access_key + secret_key` (or username + password)
- `access_key + secret_key + session_token`

Usually these are just passed to SparkS3 constructor:

```python
SparkS3(
    access_key=...,
    secret_key=...,
    session_token=...,
)
```

But some S3 cloud providers, like AWS, may require custom credential providers. You can pass them like:

```python
SparkS3(
    extra={
        # provider class
        "aws.credentials.provider": "org.apache.hadoop.fs.s3a.auth.AssumedRoleCredentialProvider",
        # other options, if needed
        "assumed.role.arn": "arn:aws:iam::90066806600238:role/s3-restricted",
    },
)
```

See [Hadoop-AWS](https://hadoop.apache.org/docs/stable/hadoop-aws/tools/hadoop-aws/index.html#Changing_Authentication_Providers) documentation.

## Troubleshooting { #DBR-onetl-connection-file-df-connection-spark-s3-prerequisites-troubleshooting }

See [troubleshooting guide][DBR-onetl-connection-file-df-connection-spark-s3-troubleshooting].
