# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import os
import textwrap
import traceback
from contextlib import contextmanager
from math import inf
from pathlib import Path
from typing import TYPE_CHECKING, Any, NamedTuple

from pydantic import SecretStr

from onetl._util.version import Version

if TYPE_CHECKING:
    from pyspark.sql import DataFrame, SparkSession
    from pyspark.sql.conf import RuntimeConfig

ONETL_ROOT = Path(__file__).parent.parent.resolve()

SPARK_JOB_DESCRIPTION_PROPERTY = "spark.job.description"
SPARK_JOB_GROUP_PROPERTY = "spark.jobGroup.id"


def stringify(value: Any, *, quote: bool = False) -> Any:
    """
    Convert values to strings.

    Values `True`, `False` and `None` become `"true"`, `"false"` and `"null"`.

    If input is dict, return dict with stringified values and keys (recursive).

    If input is list, return list with stringified values (recursive).

    If `quote=True`, wrap string values with double quotes.

    Examples
    --------

    ```python
    >>> stringify(1)
    '1'
    >>> stringify(True)
    'true'
    >>> stringify(False)
    'false'
    >>> stringify(None)
    'null'
    >>> stringify("string")
    'string'
    >>> stringify("string", quote=True)
    '"string"'
    >>> stringify({"abc": 1})
    {'abc': '1'}
    >>> stringify([1, True, False, None, "string"])
    ['1', 'true', 'false', 'null', 'string']

    ```
    """

    if isinstance(value, dict):
        return {stringify(k): stringify(v, quote=quote) for k, v in value.items()}

    if isinstance(value, list):
        return [stringify(v, quote=quote) for v in value]

    if value is None:
        return "null"

    if isinstance(value, bool):
        return "true" if value else "false"

    if isinstance(value, SecretStr):
        value = value.get_secret_value()

    if isinstance(value, os.PathLike):
        value = os.fspath(value)

    if isinstance(value, str):
        return f'"{value}"' if quote else value

    return str(value)


@contextmanager
def inject_spark_param(conf: "RuntimeConfig", name: str, value: Any):
    """
    Inject a parameter into a Spark session, and return previous value after exit.

    If value is `None`, parameter will be reset to default.
    """
    original_value = conf.get(name, None)

    try:
        conf.unset(name)
        if value is not None:
            conf.set(name, value)

        yield
    finally:
        conf.unset(name)
        if original_value is not None:
            conf.set(name, original_value)


def try_import_pyspark():
    """
    Try to import PySpark, or raise exception if missing.
    """
    try:
        import pyspark
    except (ImportError, NameError) as e:
        raise ImportError(
            textwrap.dedent(
                """
                Cannot import module "pyspark".

                You should install package as follows:
                    pip install "onetl[spark]"

                or inject PySpark to sys.path in some other way BEFORE creating class instance.
                """,
            ).strip(),
        ) from e
    else:
        return pyspark


def get_pyspark_version() -> Version:
    """
    Get PySpark version
    """
    pyspark = try_import_pyspark()
    return Version(pyspark.__version__)


def get_spark_version(spark_session: "SparkSession") -> Version:
    """
    Get Spark version from active Spark session
    """
    return Version(spark_session.version)


def estimate_dataframe_size(df: "DataFrame") -> int:
    """
    Estimate in-memory DataFrame size in bytes. If cannot be estimated, return 0.

    Using Spark's [SizeEstimator](https://spark.apache.org/docs//api/java/org/apache/spark/util/SizeEstimator.html).
    """

    try:
        jvm = df._sc._jvm  # type: ignore[attr-defined]  # noqa: SLF001
        return jvm.org.apache.spark.util.SizeEstimator.estimate(df._jdf)  # type: ignore[union-attr] # noqa: SLF001
    except Exception:  # noqa: BLE001
        # SizeEstimator uses Java reflection which may behave differently in different Java versions,
        # and also may be prohibited.
        return 0


def is_dataframe_empty(df: "DataFrame") -> bool:
    with override_call_site(df.sparkSession):
        if hasattr(df, "isEmpty"):
            # spark 3.3+
            return df.isEmpty()
        return df._jdf.isEmpty()  # noqa: SLF001


def get_executor_total_cores(spark_session: "SparkSession", *, include_driver: bool = False) -> tuple[float, dict]:
    """
    Calculate maximum number of cores which can be used by Spark on all executors.

    Returns
    -------
    Tuple
        First item is an actual number of cores.
        Second is a dict with config options were used to calculate this value.
    """

    conf = spark_session.sparkContext.getConf()
    config = {}

    master = conf.get("spark.master", "local")

    expected_cores: float
    if master.startswith("local"):
        # no executors, only driver
        scheduler = spark_session._jsc.sc().schedulerBackend()  # type: ignore[attr-defined]  # noqa: SLF001
        expected_cores = scheduler.totalCores()
        config["spark.master"] = f"local[{expected_cores}]"
    else:
        cores = int(conf.get("spark.executor.cores", "1"))
        config["spark.executor.cores"] = str(cores)

        dynamic_allocation = conf.get("spark.dynamicAllocation.enabled", "false") == "true"
        if dynamic_allocation:
            # https://spark.apache.org/docs/latest/configuration.html#dynamic-allocation
            # We cannot rely on current executors count because this number depends on
            # current load - it increases while performing heavy calculations, and decreases if executors are idle.
            # If user haven't executed anything in current session, number of executors will be 0.
            #
            # Yes, scheduler can refuse to provide executors == maxExecutors:
            # On Yarn - queue size limit is reached, or other application has higher priority,
            # so executors were preempted. on K8S - namespace has not enough resources.
            # So pessimistic approach is preferred.

            dynamic_executors = conf.get("spark.dynamicAllocation.maxExecutors", "infinity")
            executors_ratio = int(conf.get("spark.dynamicAllocation.executorAllocationRatio", "1"))
            config["spark.dynamicAllocation.maxExecutors"] = dynamic_executors
            executors = inf if dynamic_executors == "infinity" else int(dynamic_executors * executors_ratio)
        else:
            fixed_executors = int(conf.get("spark.executor.instances", "1"))
            config["spark.executor.instances"] = str(fixed_executors)
            executors = fixed_executors

        expected_cores = executors * cores
        if include_driver:
            expected_cores += 1

    return expected_cores, config


@contextmanager
def override_job_description(spark_session: "SparkSession", job_description: str):
    """
    Override Spark job description.

    Unlike `spark_session.sparkContext.setJobDescription`, this method resets job description
    before exiting the context manager, instead of keeping it.

    If user set custom description, it will be left intact.
    """
    spark_context = spark_session.sparkContext
    original_description = spark_context.getLocalProperty(SPARK_JOB_DESCRIPTION_PROPERTY)

    try:
        spark_context.setLocalProperty(SPARK_JOB_DESCRIPTION_PROPERTY, original_description or job_description)
        yield
    finally:
        spark_context.setLocalProperty(SPARK_JOB_DESCRIPTION_PROPERTY, original_description)  # type: ignore[arg-type]


class CallSite(NamedTuple):
    function: str
    file: str
    linenum: int

    def __str__(self):
        return f"{self.function} at {self.file}:{self.linenum}"


def first_onetl_call():
    """
    Return a CallSite representing the first onETL call in the current call stack.
    """
    stack = traceback.extract_stack()
    stack_size = len(stack)
    if stack_size == 0:
        return None
    file, line, fun, _text = stack[stack_size - 1]
    first_onetl_frame = stack_size - 1
    for i in range(stack_size):
        file, line, fun, _text = stack[i]
        if ONETL_ROOT in Path(file).resolve().parents:
            first_onetl_frame = i
            break
    if first_onetl_frame == 0:
        file, line, fun, _text = stack[0]
        return CallSite(function=fun, file=file, linenum=line)

    ufile, uline, ufun, _utext = stack[first_onetl_frame - 1]
    return CallSite(function=ufun, file=ufile, linenum=uline)


@contextmanager
def override_call_site(spark_session: "SparkSession"):
    """
    Override Spark CallSite.
    """
    from pyspark.traceback_utils import SCCallSiteSync

    call_site_sync = SCCallSiteSync(spark_session)
    call_site = first_onetl_call()
    if call_site:
        call_site_sync._call_site = str(call_site)  # noqa: SLF001

    with call_site_sync:
        yield


def get_client_info(spark_session: "SparkSession", limit: int | None = None, unsupported: str = "") -> str:
    """Get client info string for DB connections"""
    from onetl import __version__ as onetl_version

    result = (
        # client info fields in some DB connections (like Oracle) are very limited.
        # applicationId allows to track the exact Spark session, so more it to the beginning.
        # less important fields are moved to the end
        f"{spark_session.sparkContext.applicationId} {spark_session.sparkContext.appName} "
        # using User-Agent format
        f"onETL/{onetl_version} "
        f"Spark/{spark_session.version}"
    )
    if unsupported:
        result = result.translate(str.maketrans(unsupported, "_" * len(unsupported)))
    if limit:
        result = result[:limit]
    return result
