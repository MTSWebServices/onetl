import shutil

import pytest
from pytest_lazyfixture import lazy_fixture


@pytest.fixture(
    params=[
        lazy_fixture("ftp_file_connection"),
        lazy_fixture("ftps_file_connection"),
        lazy_fixture("hdfs_file_connection"),
        lazy_fixture("s3_file_connection"),
        lazy_fixture("sftp_file_connection"),
        lazy_fixture("samba_file_connection"),
        lazy_fixture("webdav_file_connection"),
    ],
)
def file_connection(request):
    return request.param


@pytest.fixture(
    params=[
        lazy_fixture("ftp_file_connection_with_path"),
        lazy_fixture("ftps_file_connection_with_path"),
        lazy_fixture("hdfs_file_connection_with_path"),
        lazy_fixture("s3_file_connection_with_path"),
        lazy_fixture("sftp_file_connection_with_path"),
        lazy_fixture("samba_file_connection_with_path"),
        lazy_fixture("webdav_file_connection_with_path"),
    ],
)
def file_connection_with_path(request):
    return request.param


@pytest.fixture(
    params=[
        lazy_fixture("ftp_file_connection_with_path_and_files"),
        lazy_fixture("ftps_file_connection_with_path_and_files"),
        lazy_fixture("hdfs_file_connection_with_path_and_files"),
        lazy_fixture("s3_file_connection_with_path_and_files"),
        lazy_fixture("sftp_file_connection_with_path_and_files"),
        lazy_fixture("samba_file_connection_with_path_and_files"),
        lazy_fixture("webdav_file_connection_with_path_and_files"),
    ],
)
def file_connection_with_path_and_files(request):
    return request.param


@pytest.fixture()
def file_connection_resource_path(resource_path, tmp_path_factory, worker_id):
    temp_dir = tmp_path_factory.mktemp("test_files") / worker_id
    shutil.copytree(resource_path / "file_connection", temp_dir)
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture()
def file_connection_test_files(file_connection_resource_path):
    resource_path = file_connection_resource_path
    return [
        resource_path / "ascii.txt",
        resource_path / "utf-8.txt",
    ]
