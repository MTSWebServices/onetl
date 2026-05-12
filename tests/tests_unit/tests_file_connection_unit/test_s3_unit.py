import os
import re

import pytest
from urllib3 import Retry, Timeout

pytestmark = [pytest.mark.s3, pytest.mark.file_connection, pytest.mark.connection]


def test_s3_connection():
    from onetl.connection import S3

    conn = S3(
        host="some_host",
        access_key="access key",
        secret_key="some key",
        bucket="bucket",
    )

    assert conn.host == "some_host"
    assert conn.access_key == "access key"
    assert conn.secret_key != "some key"
    assert conn.secret_key.get_secret_value() == "some key"
    assert conn.protocol == "https"
    assert conn.port == 443
    assert conn.instance_url == "s3://some_host:443/bucket"
    assert str(conn) == "S3[some_host:443/bucket]"

    assert "some key" not in repr(conn)


def test_s3_connection_with_session_token():
    from onetl.connection import S3

    conn = S3(
        host="some_host",
        access_key="access_key",
        secret_key="some key",
        session_token="some token",
        bucket="bucket",
    )

    assert conn.session_token != "some token"
    assert conn.session_token.get_secret_value() == "some token"

    assert "some token" not in repr(conn)


def test_s3_connection_https():
    from onetl.connection import S3

    conn = S3(
        host="some_host",
        access_key="access_key",
        secret_key="secret_key",
        bucket="bucket",
        protocol="https",
    )

    assert conn.protocol == "https"
    assert conn.port == 443
    assert conn.instance_url == "s3://some_host:443/bucket"
    assert str(conn) == "S3[some_host:443/bucket]"


def test_s3_connection_http():
    from onetl.connection import S3

    conn = S3(
        host="some_host",
        access_key="access_key",
        secret_key="secret_key",
        bucket="bucket",
        protocol="http",
    )

    assert conn.protocol == "http"
    assert conn.port == 80
    assert conn.instance_url == "s3://some_host:80/bucket"
    assert str(conn) == "S3[some_host:80/bucket]"


@pytest.mark.parametrize("protocol", ["http", "https"])
def test_s3_connection_with_port(protocol):
    from onetl.connection import S3

    conn = S3(
        host="some_host",
        port=9000,
        access_key="access_key",
        secret_key="secret_key",
        bucket="bucket",
        protocol=protocol,
    )

    assert conn.protocol == protocol
    assert conn.port == 9000
    assert conn.instance_url == "s3://some_host:9000/bucket"
    assert str(conn) == "S3[some_host:9000/bucket]"


def test_s3_connection_with_ssl_verify(tmp_path, monkeypatch):
    from onetl.connection import S3

    msg = "Option `ssl_verify` is deprecated since v0.16.0 and will be removed in v1.0.0. "
    with pytest.warns(UserWarning, match=re.escape(msg)):
        conn = S3(
            host="some_host",
            access_key="access key",
            secret_key="some key",
            bucket="bucket",
            ssl_verify=False,
        )
    assert conn.extra.ssl_verify is False

    dir_path = tmp_path.joinpath("certs")
    dir_path.mkdir(exist_ok=True, parents=True)

    file_path = dir_path.joinpath("cert.pem")
    file_path.touch()

    for path in [dir_path, file_path]:
        for env in ["REQUESTS_CA_BUNDLE", "SSL_CERT_FILE", "SSL_CERT_DIR"]:
            monkeypatch.setenv(env, os.fspath(path))
            with pytest.warns(UserWarning, match=re.escape(msg)):
                conn = S3(
                    host="some_host",
                    access_key="access key",
                    secret_key="some key",
                    bucket="bucket",
                    ssl_verify=True,
                )
            monkeypatch.delenv(env)
            assert conn.extra.ssl_verify == path

    for path in [dir_path, file_path]:
        with pytest.warns(UserWarning, match=re.escape(msg)):
            conn = S3(
                host="some_host",
                access_key="access key",
                secret_key="some key",
                bucket="bucket",
                ssl_verify=path,
                extra={"something": "abc"},
            )
        assert conn.extra.ssl_verify == path
        assert conn.extra.something == "abc"


def test_s3_connection_with_extra():
    from onetl.connection import S3

    conn = S3(
        host="some_host",
        access_key="access key",
        secret_key="some key",
        bucket="bucket",
    )
    assert conn.extra.timeout._connect == 10
    assert conn.extra.timeout._read == 60
    assert conn.extra.retry.total == 5
    assert conn.extra.retry.backoff_factor == 0.2
    assert conn.extra.retry.status_forcelist == frozenset({500, 502, 503, 504})
    assert conn.extra.retry.allowed_methods == frozenset({"HEAD", "DELETE", "TRACE", "PUT", "GET", "OPTIONS"})

    conn = S3(
        host="some_host",
        access_key="access key",
        secret_key="some key",
        bucket="bucket",
        extra=S3.Extra(
            timeout=Timeout(connect=1, read=1),
            retry=Retry(
                total=1,
                backoff_factor=1,
                status_forcelist=[500, 502, 503, 504],
                allowed_methods=frozenset({"HEAD", "GET", "PUT", "OPTIONS"}),
            ),
            ssl_verify=False,
            something="abc",
        ),
    )
    assert conn.extra.timeout._connect == 1
    assert conn.extra.timeout._read == 1
    assert conn.extra.retry.total == 1
    assert conn.extra.retry.backoff_factor == 1
    assert conn.extra.retry.status_forcelist == [500, 502, 503, 504]
    assert conn.extra.retry.allowed_methods == frozenset({"HEAD", "GET", "PUT", "OPTIONS"})
    assert conn.extra.ssl_verify is False
    assert conn.extra.something == "abc"

    conn = S3(
        host="some_host",
        access_key="access key",
        secret_key="some key",
        bucket="bucket",
        extra={
            "timeout": Timeout(connect=1, read=1),
            "retry": Retry(
                total=1,
                backoff_factor=1,
                status_forcelist=[500, 502, 503, 504],
                allowed_methods=frozenset({"HEAD", "GET", "PUT", "OPTIONS"}),
            ),
            "ssl_verify": False,
            "something": "abc",
        },
    )
    assert conn.extra.timeout._connect == 1
    assert conn.extra.timeout._read == 1
    assert conn.extra.retry.total == 1
    assert conn.extra.retry.backoff_factor == 1
    assert conn.extra.retry.status_forcelist == [500, 502, 503, 504]
    assert conn.extra.retry.allowed_methods == frozenset({"HEAD", "GET", "PUT", "OPTIONS"})
    assert conn.extra.ssl_verify is False
    assert conn.extra.something == "abc"
