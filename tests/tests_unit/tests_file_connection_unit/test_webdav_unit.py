import os
import re

import pytest
from urllib3 import Retry, Timeout

from onetl.connection import FileConnection

pytestmark = [pytest.mark.webdav, pytest.mark.file_connection, pytest.mark.connection]


def test_webdav_connection():
    from onetl.connection import WebDAV

    conn = WebDAV(host="some_host", user="some_user", password="pwd")
    assert isinstance(conn, FileConnection)
    assert conn.host == "some_host"
    assert conn.protocol == "https"
    assert conn.port == 443
    assert conn.user == "some_user"
    assert conn.password != "pwd"
    assert conn.password.get_secret_value() == "pwd"
    assert conn.instance_url == "webdav://some_host:443"
    assert str(conn) == "WebDAV[some_host:443]"

    assert "pwd" not in repr(conn)


def test_webdav_connection_with_http():
    from onetl.connection import WebDAV

    conn = WebDAV(host="some_host", user="some_user", password="pwd", protocol="http")
    assert conn.protocol == "http"
    assert conn.port == 80
    assert conn.instance_url == "webdav://some_host:80"
    assert str(conn) == "WebDAV[some_host:80]"


@pytest.mark.parametrize("protocol", ["http", "https"])
def test_webdav_connection_with_custom_port(protocol):
    from onetl.connection import WebDAV

    conn = WebDAV(host="some_host", user="some_user", password="pwd", port=500, protocol=protocol)
    assert conn.protocol == protocol
    assert conn.port == 500
    assert conn.instance_url == "webdav://some_host:500"
    assert str(conn) == "WebDAV[some_host:500]"


def test_webdav_connection_without_mandatory_args():
    from onetl.connection import WebDAV

    with pytest.raises(ValueError):
        WebDAV()


def test_webdav_connection_with_ssl_verify(tmp_path, monkeypatch):
    from onetl.connection import WebDAV

    msg = "Option `ssl_verify` is deprecated since v0.16.0 and will be removed in v1.0.0. "
    with pytest.warns(UserWarning, match=re.escape(msg)):
        conn = WebDAV(
            host="some_host",
            user="some_user",
            password="pwd",
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
                conn = WebDAV(
                    host="some_host",
                    user="some_user",
                    password="pwd",
                    ssl_verify=True,
                )
            monkeypatch.delenv(env)
            assert conn.extra.ssl_verify == path

    for path in [dir_path, file_path]:
        with pytest.warns(UserWarning, match=re.escape(msg)):
            conn = WebDAV(
                host="some_host",
                user="some_user",
                password="pwd",
                ssl_verify=path,
                extra={"something": "abc"},
            )
        assert conn.extra.ssl_verify == path
        assert conn.extra.something == "abc"


def test_webdav_connection_with_extra():
    from onetl.connection import WebDAV

    conn = WebDAV(
        host="some_host",
        user="some_user",
        password="pwd",
    )
    assert conn.extra.timeout._connect == 10
    assert conn.extra.timeout._read == 60
    assert conn.extra.retry.total == 3
    assert conn.extra.retry.backoff_factor == 0
    assert conn.extra.retry.status_forcelist == frozenset()
    assert conn.extra.retry.allowed_methods == frozenset({"HEAD", "DELETE", "TRACE", "PUT", "GET", "OPTIONS"})

    conn = WebDAV(
        host="some_host",
        user="some_user",
        password="pwd",
        extra=WebDAV.Extra(
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

    conn = WebDAV(
        host="some_host",
        user="some_user",
        password="pwd",
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
