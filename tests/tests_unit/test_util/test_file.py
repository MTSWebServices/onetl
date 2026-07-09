import hashlib
import io
import stat
from pathlib import Path

import pytest

from onetl._util.file import generate_temp_path, get_file_hash, is_file_readable
from onetl.exception import NotAFileError


def test_get_file_hash_empty_file(tmp_path):
    file = tmp_path / "empty.txt"
    file.write_bytes(b"")
    expected = hashlib.md5(b"").digest()
    assert get_file_hash(file, "md5").digest() == expected


def test_get_file_hash_small_file(tmp_path):
    file = tmp_path / "small.txt"
    content = b"hello world"
    file.write_bytes(content)
    expected = hashlib.md5(content).digest()
    assert get_file_hash(file, "md5").digest() == expected


def test_get_file_hash_large_file(tmp_path):
    file = tmp_path / "large.bin"
    content = b"a" * (io.DEFAULT_BUFFER_SIZE * 3 + 1)
    file.write_bytes(content)
    expected = hashlib.sha256(content).digest()
    assert get_file_hash(file, "sha256").digest() == expected


def test_get_file_hash_different_algorithms(tmp_path):
    file = tmp_path / "data.bin"
    content = b"test data for hashing"
    file.write_bytes(content)
    for algo in ("md5", "sha1", "sha256"):
        expected = hashlib.new(algo, content).digest()
        assert get_file_hash(file, algo).digest() == expected


def test_is_file_readable_nonexistent_file(tmp_path):
    file = tmp_path / "nonexistent.txt"
    with pytest.raises(FileNotFoundError):
        get_file_hash(file, "md5")


def test_is_file_readable_not_found(tmp_path):
    file = tmp_path / "nonexistent.txt"
    with pytest.raises(FileNotFoundError, match="does not exist"):
        is_file_readable(file)


def test_is_file_readable_is_not_a_file(tmp_path):
    file = tmp_path
    with pytest.raises(NotAFileError, match="is not a file"):
        is_file_readable(file)


def test_is_file_readable_no_access(tmp_path):
    file = tmp_path / "secret.txt"
    file.write_bytes(b"secret")
    file.chmod(stat.S_IWUSR | stat.S_IXUSR)

    with pytest.raises(OSError, match="No read access"):
        is_file_readable(file)


def test_is_file_readable_success(tmp_path):
    file = tmp_path / "secret.txt"
    file.write_bytes(b"secret")
    assert is_file_readable(file) == Path(file)


def test_generate_temp_path_returns_same_type():
    from pathlib import Path, PurePath

    pure_result = generate_temp_path(PurePath("/tmp"))
    assert isinstance(pure_result, PurePath)

    path_result = generate_temp_path(Path("/tmp"))
    assert isinstance(path_result, Path)
