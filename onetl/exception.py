# SPDX-FileCopyrightText: 2021-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import textwrap

from evacuator import NeedEvacuation

MISSING_JVM_CLASS_MSG = textwrap.dedent(
    """
    Cannot import Java class {java_class!r}.

        It looks like you've created Spark session without this option:
            maven_packages = {package_source}.get_packages({args})
            SparkSession.builder.config("spark.jars.packages", ",".join(maven_packages))

        Please call `spark.stop()`, restart the interpreter,
        and then create new SparkSession with proper options.
    """,
).lstrip()


class DirectoryNotFoundError(OSError):
    """
    Like `FileNotFoundError`, but for directory.

    Cannot be replaced with `NotAFileError` because on some operating systems
    (e.g. Linux) there are other file types than regular file and directory - symlink, device, etc.

    !!! success "Added in 0.3.0"
    """


class NotAFileError(OSError):
    """
    Like `NotADirectoryError`, but for files.

    Cannot be replaced with `FileNotFoundError`, it has different meaning.

    !!! success "Added in 0.3.0"
    """


class FileSizeMismatchError(OSError):
    """
    File size mismatch.

    !!! success "Added in 0.8.0"
    """


class DirectoryExistsError(OSError):
    """
    Like `FileExistsError`, but for directories.

    !!! success "Added in 0.8.0"
    """


class DirectoryNotEmptyError(OSError):
    """
    Raised when trying to remove directory contains some files or other directories..

    !!! success "Added in 0.3.0"
    """


class NoDataError(NeedEvacuation):
    """
    Raised when there is no data in FileResult or DataFrame.

    !!! success "Added in 0.4.0"
    """


class FilesError(RuntimeError):
    """
    Raised when something went wrong while working with file collection.

    !!! success "Added in 0.4.0"
    """


class SkippedFilesError(FilesError):
    """
    Raised when file collection contains skipped files.

    !!! success "Added in 0.4.0"
    """


class FailedFilesError(FilesError):
    """
    Raised when file collection contains failed files.

    !!! success "Added in 0.4.0"
    """


class MissingFilesError(FilesError):
    """
    Raised when file collection contains missing files.

    !!! success "Added in 0.4.0"
    """


class ZeroFileSizeError(FilesError):
    """
    Raised when file collection contains some zero-sized file.

    !!! success "Added in 0.4.0"
    """


class EmptyFilesError(FilesError, NoDataError):
    """
    Raised when file collection is empty.

    !!! success "Added in 0.4.0"
    """


class SparkError(RuntimeError):
    """
    Raised when something went wrong while working with Spark.

    !!! success "Added in 0.5.0"
    """


class TooManyParallelJobsError(SparkError):
    """
    Raised when number parallel jobs is too high.

    !!! success "Added in 0.5.0"
    """


class SignatureError(TypeError):
    """
    Raised when hook signature is not consistent with slot.

    !!! success "Added in 0.7.0"
    """


class TargetAlreadyExistsError(Exception):
    """Raised if the target already exists in source.

    !!! success "Added in 0.9.0"
    """
