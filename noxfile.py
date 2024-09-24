# Run nox tests
#
# usage:
#   poetry run nox --error-on-external-run --reuse-venv=yes --non-interactive
#
# If you want to target a specific Python version, add -p parameter
from __future__ import annotations

import nox

PREFIX_TESTS_FUNCTIONAL = "tests/functional"
PREFIX_TESTS_UNIT = "tests/unit"


def build_and_run_test(session: nox.Session, folders: list, extras: str = "") -> None:
    """
    This function is responsible for setting up the testing environment and running the test suite for specific feature.

    The function performs the following tasks:
    1. Installs the required dependencies for executing any test
    2. If the `extras` parameter is provided, the function installs the additional dependencies
    3. the function runs the pytest command with the specified folders as arguments, executing the test suite.

    Parameters
    ----------
    session: nox.Session
        The current Nox session object, which is used to manage the virtual environment and execute commands.
    folders: List
        A list of folder paths that contain the test files to be executed.
    extras: Optional[str]
        A string representing additional dependencies that should be installed for the test environment.
        If not provided, the function will install the project with basic dependencies
    """

    # Required install to execute any test
    session.install("poetry", "pytest", "pytest-mock", "pytest_socket")

    # Powertools project folder is in the root
    if extras:
        session.install(f"./[{extras}]")
    else:
        session.install("./")

    # Execute test in specific folders
    session.run("pytest", *folders)


@nox.session()
def test_with_only_required_packages(session: nox.Session):
    """Tests that only depends for required libraries"""
    # Logger
    # Metrics - Amazon CloudWatch EMF
    # Metrics - Base provider
    # Middleware factory without tracer
    # Typing
    # Data Class - without codepipeline dataclass
    # Event Handler without OpenAPI
    # Batch processor - without pydantic integration
    build_and_run_test(
        session,
        folders=[
            f"{PREFIX_TESTS_FUNCTIONAL}/logger/required_dependencies/",
            f"{PREFIX_TESTS_FUNCTIONAL}/metrics/required_dependencies/",
            f"{PREFIX_TESTS_FUNCTIONAL}/middleware_factory/required_dependencies/",
            f"{PREFIX_TESTS_FUNCTIONAL}/typing/required_dependencies/",
            f"{PREFIX_TESTS_UNIT}/data_classes/required_dependencies/",
            f"{PREFIX_TESTS_FUNCTIONAL}/event_handler/required_dependencies/",
            f"{PREFIX_TESTS_FUNCTIONAL}/batch/required_dependencies/",
        ],
    )


@nox.session()
def test_with_datadog_as_required_package(session: nox.Session):
    """Tests that depends on Datadog library"""
    # Metrics - Datadog
    build_and_run_test(
        session,
        folders=[
            f"{PREFIX_TESTS_FUNCTIONAL}/metrics/datadog/",
        ],
        extras="datadog",
    )


@nox.session()
def test_with_xray_sdk_as_required_package(session: nox.Session):
    """Tests that depends on AWS XRAY SDK library"""
    # Tracer
    # Middleware factory with tracer
    build_and_run_test(
        session,
        folders=[
            f"{PREFIX_TESTS_FUNCTIONAL}/tracer/_aws_xray_sdk/",
            f"{PREFIX_TESTS_FUNCTIONAL}/middleware_factory/_aws_xray_sdk/",
        ],
        extras="tracer",
    )


@nox.session()
def test_with_boto3_sdk_as_required_package(session: nox.Session):
    """Tests that depends on boto3/botocore library"""
    # Parameters
    # Feature Flags
    # Data Class - only codepipeline dataclass
    # Streaming
    # Idempotency - DynamoDB persistent layer
    build_and_run_test(
        session,
        folders=[
            f"{PREFIX_TESTS_FUNCTIONAL}/parameters/_boto3/",
            f"{PREFIX_TESTS_FUNCTIONAL}/feature_flags/_boto3/",
            f"{PREFIX_TESTS_UNIT}/data_classes/_boto3/",
            f"{PREFIX_TESTS_FUNCTIONAL}/streaming/_boto3/",
            f"{PREFIX_TESTS_FUNCTIONAL}/idempotency/_boto3/",
        ],
        extras="aws-sdk",
    )


@nox.session()
def test_with_fastjsonschema_as_required_package(session: nox.Session):
    """Tests that depends on fastjsonschema library"""
    # Validation
    build_and_run_test(
        session,
        folders=[
            f"{PREFIX_TESTS_FUNCTIONAL}/validator/_fastjsonschema/",
        ],
        extras="validation",
    )


@nox.session()
def test_with_aws_encryption_sdk_as_required_package(session: nox.Session):
    """Tests that depends on aws_encryption_sdk library"""
    # Data Masking
    build_and_run_test(
        session,
        folders=[
            f"{PREFIX_TESTS_FUNCTIONAL}/data_masking/_aws_encryption_sdk/",
            f"{PREFIX_TESTS_UNIT}/data_masking/_aws_encryption_sdk/",
        ],
        extras="datamasking",
    )


@nox.session()
def test_with_pydantic_required_package(session: nox.Session):
    """Tests that only depends for Pydantic library v2"""
    # Event Handler OpenAPI
    # Parser
    # Batch Processor with pydantic integration
    build_and_run_test(
        session,
        folders=[
            f"{PREFIX_TESTS_FUNCTIONAL}/event_handler/_pydantic/",
            f"{PREFIX_TESTS_FUNCTIONAL}/batch/_pydantic/",
            f"{PREFIX_TESTS_UNIT}/parser/_pydantic/",
            f"{PREFIX_TESTS_UNIT}/event_handler/_pydantic/",
        ],
        extras="parser",
    )


@nox.session()
def test_with_boto3_and_pydantic_required_package(session: nox.Session):
    """Tests that only depends for Boto3 + Pydantic library v2"""
    # Idempotency with custom serializer

    build_and_run_test(
        session,
        folders=[
            f"{PREFIX_TESTS_FUNCTIONAL}/idempotency/_pydantic/",
        ],
        extras="aws-sdk,parser",
    )


@nox.session()
def test_with_redis_and_boto3_sdk_as_required_package(session: nox.Session):
    """Tests that depends on Redis library"""
    # Idempotency - Redis backend

    # Our Redis tests requires multiprocess library to simulate Race Condition
    session.run("pip", "install", "multiprocess")

    build_and_run_test(
        session,
        folders=[
            f"{PREFIX_TESTS_FUNCTIONAL}/idempotency/_redis/",
        ],
        extras="redis,aws-sdk",
    )
