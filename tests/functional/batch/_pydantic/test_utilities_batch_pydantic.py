import json
import uuid
from random import randint
from typing import Any, Awaitable, Callable, Dict, Optional

import pytest
from pydantic import BaseModel, field_validator

from aws_lambda_powertools.utilities.batch import (
    AsyncBatchProcessor,
    BatchProcessor,
    EventType,
    SqsFifoPartialProcessor,
    batch_processor,
)
from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import (
    DynamoDBRecord,
)
from aws_lambda_powertools.utilities.data_classes.kinesis_stream_event import (
    KinesisStreamRecord,
)
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.parser.models import (
    DynamoDBStreamChangedRecordModel,
    DynamoDBStreamRecordModel,
    SqsRecordModel,
)
from aws_lambda_powertools.utilities.parser.types import Literal
from tests.functional.batch._pydantic.sample_models import (
    OrderDynamoDBRecord,
    OrderKinesisRecord,
    OrderSqs,
)
from tests.functional.utils import b64_to_str, str_to_b64


@pytest.fixture(scope="module")
def sqs_event_fifo_factory() -> Callable:
    def factory(body: str, message_group_id: str = ""):
        return {
            "messageId": f"{uuid.uuid4()}",
            "receiptHandle": "AQEBwJnKyrHigUMZj6rYigCgxlaS3SLy0a",
            "body": body,
            "attributes": {
                "ApproximateReceiveCount": "1",
                "SentTimestamp": "1703675223472",
                "SequenceNumber": "18882884930918384133",
                "MessageGroupId": message_group_id,
                "SenderId": "SenderId",
                "MessageDeduplicationId": "1eea03c3f7e782c7bdc2f2a917f40389314733ff39f5ab16219580c0109ade98",
                "ApproximateFirstReceiveTimestamp": "1703675223484",
            },
            "messageAttributes": {},
            "md5OfBody": "e4e68fb7bd0e697a0ae8f1bb342846b3",
            "eventSource": "aws:sqs",
            "eventSourceARN": "arn:aws:sqs:us-east-2:123456789012:my-queue",
            "awsRegion": "us-east-1",
        }

    return factory


@pytest.fixture(scope="module")
def sqs_event_factory() -> Callable:
    def factory(body: str):
        return {
            "messageId": f"{uuid.uuid4()}",
            "receiptHandle": "AQEBwJnKyrHigUMZj6rYigCgxlaS3SLy0a",
            "body": body,
            "attributes": {
                "ApproximateReceiveCount": "1",
                "SentTimestamp": "1545082649183",
                "SenderId": "SenderId",
                "ApproximateFirstReceiveTimestamp": "1545082649185",
            },
            "messageAttributes": {},
            "md5OfBody": "e4e68fb7bd0e697a0ae8f1bb342846b3",
            "eventSource": "aws:sqs",
            "eventSourceARN": "arn:aws:sqs:us-east-2:123456789012:my-queue",
            "awsRegion": "us-east-1",
        }

    return factory


@pytest.fixture(scope="module")
def kinesis_event_factory() -> Callable:
    def factory(body: str):
        seq = "".join(str(randint(0, 9)) for _ in range(52))
        return {
            "kinesis": {
                "kinesisSchemaVersion": "1.0",
                "partitionKey": "1",
                "sequenceNumber": seq,
                "data": str_to_b64(body),
                "approximateArrivalTimestamp": 1545084650.987,
            },
            "eventSource": "aws:kinesis",
            "eventVersion": "1.0",
            "eventID": f"shardId-000000000006:{seq}",
            "eventName": "aws:kinesis:record",
            "invokeIdentityArn": "arn:aws:iam::123456789012:role/lambda-role",
            "awsRegion": "us-east-2",
            "eventSourceARN": "arn:aws:kinesis:us-east-2:123456789012:stream/lambda-stream",
        }

    return factory


@pytest.fixture(scope="module")
def dynamodb_event_factory() -> Callable:
    def factory(body: str):
        seq = "".join(str(randint(0, 9)) for _ in range(10))
        return {
            "eventID": "1",
            "eventVersion": "1.0",
            "dynamodb": {
                "Keys": {"Id": {"N": "101"}},
                "NewImage": {"Message": {"S": body}},
                "StreamViewType": "NEW_AND_OLD_IMAGES",
                "SequenceNumber": seq,
                "SizeBytes": 26,
            },
            "awsRegion": "us-west-2",
            "eventName": "INSERT",
            "eventSourceARN": "eventsource_arn",
            "eventSource": "aws:dynamodb",
        }

    return factory


@pytest.fixture(scope="module")
def record_handler() -> Callable:
    def handler(record):
        body = record["body"]
        if "fail" in body:
            raise Exception("Failed to process record.")
        return body

    return handler


@pytest.fixture(scope="module")
def record_handler_model() -> Callable:
    def record_handler(record: OrderSqs):
        if "fail" in record.body.item["type"]:
            raise Exception("Failed to process record.")
        return record.body.item

    return record_handler


@pytest.fixture(scope="module")
def async_record_handler() -> Callable[..., Awaitable[Any]]:
    async def handler(record):
        body = record["body"]
        if "fail" in body:
            raise Exception("Failed to process record.")
        return body

    return handler


@pytest.fixture(scope="module")
def async_record_handler_model() -> Callable[..., Awaitable[Any]]:
    async def async_record_handler(record: OrderSqs):
        if "fail" in record.body.item["type"]:
            raise ValueError("Failed to process record.")
        return record.body.item

    return async_record_handler


@pytest.fixture(scope="module")
def kinesis_record_handler() -> Callable:
    def handler(record: KinesisStreamRecord):
        body = b64_to_str(record.kinesis.data)
        if "fail" in body:
            raise Exception("Failed to process record.")
        return body

    return handler


@pytest.fixture(scope="module")
def kinesis_record_handler_model() -> Callable:
    def record_handler(record: OrderKinesisRecord):
        if "fail" in record.kinesis.data.item["type"]:
            raise ValueError("Failed to process record.")
        return record.kinesis.data.item

    return record_handler


@pytest.fixture(scope="module")
def async_kinesis_record_handler_model() -> Callable[..., Awaitable[Any]]:
    async def record_handler(record: OrderKinesisRecord):
        if "fail" in record.kinesis.data.item["type"]:
            raise Exception("Failed to process record.")
        return record.kinesis.data.item

    return record_handler


@pytest.fixture(scope="module")
def dynamodb_record_handler() -> Callable:
    def handler(record: DynamoDBRecord):
        body = record.dynamodb.new_image.get("Message")
        if "fail" in body:
            raise ValueError("Failed to process record.")
        return body

    return handler


@pytest.fixture(scope="module")
def dynamodb_record_handler_model() -> Callable:
    def record_handler(record: OrderDynamoDBRecord):
        if "fail" in record.dynamodb.NewImage.Message.item["type"]:
            raise ValueError("Failed to process record.")
        return record.dynamodb.NewImage.Message.item

    return record_handler


@pytest.fixture(scope="module")
def async_dynamodb_record_handler() -> Callable[..., Awaitable[Any]]:
    async def record_handler(record: OrderDynamoDBRecord):
        if "fail" in record.dynamodb.NewImage.Message.item["type"]:
            raise ValueError("Failed to process record.")
        return record.dynamodb.NewImage.Message.item

    return record_handler


@pytest.fixture(scope="module")
def order_event_factory() -> Callable:
    def factory(item: Dict) -> str:
        return json.dumps({"item": item})

    return factory


def test_batch_processor_context_model(sqs_event_factory, order_event_factory):
    # GIVEN
    def record_handler(record: OrderSqs):
        return record.body.item

    order_event = order_event_factory({"type": "success"})
    first_record = sqs_event_factory(order_event)
    second_record = sqs_event_factory(order_event)
    records = [first_record, second_record]

    # WHEN
    processor = BatchProcessor(event_type=EventType.SQS, model=OrderSqs)
    with processor(records, record_handler) as batch:
        processed_messages = batch.process()

    # THEN
    order_item = json.loads(order_event)["item"]
    assert processed_messages == [
        ("success", order_item, first_record),
        ("success", order_item, second_record),
    ]

    assert batch.response() == {"batchItemFailures": []}


def test_batch_processor_context_model_with_failure(sqs_event_factory, order_event_factory):
    # GIVEN
    def record_handler(record: OrderSqs):
        if "fail" in record.body.item["type"]:
            raise Exception("Failed to process record.")
        return record.body.item

    order_event = order_event_factory({"type": "success"})
    order_event_fail = order_event_factory({"type": "fail"})
    first_record = sqs_event_factory(order_event_fail)
    third_record = sqs_event_factory(order_event_fail)
    second_record = sqs_event_factory(order_event)
    records = [first_record, second_record, third_record]

    # WHEN
    processor = BatchProcessor(event_type=EventType.SQS, model=OrderSqs)
    with processor(records, record_handler) as batch:
        batch.process()

    # THEN
    assert len(batch.fail_messages) == 2
    assert batch.response() == {
        "batchItemFailures": [
            {"itemIdentifier": first_record["messageId"]},
            {"itemIdentifier": third_record["messageId"]},
        ],
    }


def test_batch_processor_dynamodb_context_model(dynamodb_event_factory, order_event_factory):
    # GIVEN
    class Order(BaseModel):
        item: dict

    class OrderDynamoDB(BaseModel):
        Message: Order

        # auto transform json string
        # so Pydantic can auto-initialize nested Order model
        @field_validator("Message", mode="before")
        def transform_message_to_dict(cls, value: Dict[Literal["S"], str]):
            return json.loads(value)

    class OrderDynamoDBChangeRecord(DynamoDBStreamChangedRecordModel):
        NewImage: Optional[OrderDynamoDB] = None
        OldImage: Optional[OrderDynamoDB] = None

    class OrderDynamoDBRecord(DynamoDBStreamRecordModel):
        dynamodb: OrderDynamoDBChangeRecord

    def record_handler(record: OrderDynamoDBRecord):
        return record.dynamodb.NewImage.Message.item

    order_event = order_event_factory({"type": "success"})
    first_record = dynamodb_event_factory(order_event)
    second_record = dynamodb_event_factory(order_event)
    records = [first_record, second_record]

    # WHEN
    processor = BatchProcessor(event_type=EventType.DynamoDBStreams, model=OrderDynamoDBRecord)
    with processor(records, record_handler) as batch:
        processed_messages = batch.process()

    # THEN
    order_item = json.loads(order_event)["item"]
    assert processed_messages == [
        ("success", order_item, first_record),
        ("success", order_item, second_record),
    ]

    assert batch.response() == {"batchItemFailures": []}


def test_batch_processor_dynamodb_context_model_with_failure(dynamodb_event_factory, order_event_factory):
    # GIVEN
    class Order(BaseModel):
        item: dict

    class OrderDynamoDB(BaseModel):
        Message: Order

        # auto transform json string
        # so Pydantic can auto-initialize nested Order model
        @field_validator("Message", mode="before")
        def transform_message_to_dict(cls, value: Dict[Literal["S"], str]):
            return json.loads(value)

    class OrderDynamoDBChangeRecord(DynamoDBStreamChangedRecordModel):
        NewImage: Optional[OrderDynamoDB] = None
        OldImage: Optional[OrderDynamoDB] = None

    class OrderDynamoDBRecord(DynamoDBStreamRecordModel):
        dynamodb: OrderDynamoDBChangeRecord

    def record_handler(record: OrderDynamoDBRecord):
        if "fail" in record.dynamodb.NewImage.Message.item["type"]:
            raise Exception("Failed to process record.")
        return record.dynamodb.NewImage.Message.item

    order_event = order_event_factory({"type": "success"})
    order_event_fail = order_event_factory({"type": "fail"})
    first_record = dynamodb_event_factory(order_event_fail)
    second_record = dynamodb_event_factory(order_event)
    third_record = dynamodb_event_factory(order_event_fail)
    records = [first_record, second_record, third_record]

    # WHEN
    processor = BatchProcessor(event_type=EventType.DynamoDBStreams, model=OrderDynamoDBRecord)
    with processor(records, record_handler) as batch:
        batch.process()

    # THEN
    assert len(batch.fail_messages) == 2
    assert batch.response() == {
        "batchItemFailures": [
            {"itemIdentifier": first_record["dynamodb"]["SequenceNumber"]},
            {"itemIdentifier": third_record["dynamodb"]["SequenceNumber"]},
        ],
    }


def test_batch_processor_kinesis_context_parser_model(
    kinesis_record_handler_model: Callable,
    kinesis_event_factory,
    order_event_factory,
):
    # GIVEN
    order_event = order_event_factory({"type": "success"})
    first_record = kinesis_event_factory(order_event)
    second_record = kinesis_event_factory(order_event)
    records = [first_record, second_record]

    # WHEN
    processor = BatchProcessor(event_type=EventType.KinesisDataStreams, model=OrderKinesisRecord)
    with processor(records, kinesis_record_handler_model) as batch:
        processed_messages = batch.process()

    # THEN
    order_item = json.loads(order_event)["item"]
    assert processed_messages == [
        ("success", order_item, first_record),
        ("success", order_item, second_record),
    ]

    assert batch.response() == {"batchItemFailures": []}


def test_batch_processor_kinesis_context_parser_model_with_failure(
    kinesis_record_handler_model: Callable,
    kinesis_event_factory,
    order_event_factory,
):
    # GIVEN
    order_event = order_event_factory({"type": "success"})
    order_event_fail = order_event_factory({"type": "fail"})

    first_record = kinesis_event_factory(order_event_fail)
    second_record = kinesis_event_factory(order_event)
    third_record = kinesis_event_factory(order_event_fail)
    records = [first_record, second_record, third_record]

    # WHEN
    processor = BatchProcessor(event_type=EventType.KinesisDataStreams, model=OrderKinesisRecord)
    with processor(records, kinesis_record_handler_model) as batch:
        batch.process()

    # THEN
    assert len(batch.fail_messages) == 2
    assert batch.response() == {
        "batchItemFailures": [
            {"itemIdentifier": first_record["kinesis"]["sequenceNumber"]},
            {"itemIdentifier": third_record["kinesis"]["sequenceNumber"]},
        ],
    }


def test_sqs_fifo_batch_processor_middleware_with_skip_group_on_error_and_model(sqs_event_fifo_factory, record_handler):
    # GIVEN a batch of 5 records with 3 different MessageGroupID
    first_record = SQSRecord(sqs_event_fifo_factory("success", "1"))
    second_record = SQSRecord(sqs_event_fifo_factory("success", "1"))
    third_record = SQSRecord(sqs_event_fifo_factory("fail", "2"))
    fourth_record = SQSRecord(sqs_event_fifo_factory("success", "2"))
    fifth_record = SQSRecord(sqs_event_fifo_factory("fail", "3"))
    event = {
        "Records": [
            first_record.raw_event,
            second_record.raw_event,
            third_record.raw_event,
            fourth_record.raw_event,
            fifth_record.raw_event,
        ],
    }

    class OrderSqsRecord(SqsRecordModel):
        receiptHandle: str

    # WHEN the FIFO processor is set to continue processing even after encountering errors in specific MessageGroupID
    # WHEN processor is using a Pydantic Model we must be able to access MessageGroupID property
    processor = SqsFifoPartialProcessor(skip_group_on_error=True, model=OrderSqsRecord)

    def record_handler(record: OrderSqsRecord):
        if record.body == "fail":
            raise ValueError("blah")

    @batch_processor(record_handler=record_handler, processor=processor)
    def lambda_handler(event, context):
        return processor.response()

    # WHEN
    result = lambda_handler(event, {})

    # THEN only failed messages should originate from MessageGroupID 3
    assert len(result["batchItemFailures"]) == 3
    assert result["batchItemFailures"][0]["itemIdentifier"] == third_record.message_id
    assert result["batchItemFailures"][1]["itemIdentifier"] == fourth_record.message_id
    assert result["batchItemFailures"][2]["itemIdentifier"] == fifth_record.message_id


def test_batch_processor_model_with_partial_validation_error(
    record_handler_model: Callable,
    sqs_event_factory,
    order_event_factory,
):
    # GIVEN
    order_event = order_event_factory({"type": "success"})
    first_record = sqs_event_factory(order_event)
    second_record = sqs_event_factory(order_event)
    malformed_record = sqs_event_factory({"poison": "pill"})
    records = [first_record, malformed_record, second_record]

    # WHEN
    processor = BatchProcessor(event_type=EventType.SQS, model=OrderSqs)
    with processor(records, record_handler_model) as batch:
        batch.process()

    # THEN
    assert len(batch.fail_messages) == 1
    assert batch.response() == {
        "batchItemFailures": [
            {"itemIdentifier": malformed_record["messageId"]},
        ],
    }


def test_batch_processor_dynamodb_context_model_with_partial_validation_error(
    dynamodb_record_handler_model: Callable,
    dynamodb_event_factory,
    order_event_factory,
):
    # GIVEN
    order_event = order_event_factory({"type": "success"})
    first_record = dynamodb_event_factory(order_event)
    second_record = dynamodb_event_factory(order_event)
    malformed_record = dynamodb_event_factory({"poison": "pill"})
    records = [first_record, malformed_record, second_record]

    # WHEN
    processor = BatchProcessor(event_type=EventType.DynamoDBStreams, model=OrderDynamoDBRecord)
    with processor(records, dynamodb_record_handler_model) as batch:
        batch.process()

    # THEN
    assert len(batch.fail_messages) == 1
    assert batch.response() == {
        "batchItemFailures": [
            {"itemIdentifier": malformed_record["dynamodb"]["SequenceNumber"]},
        ],
    }


def test_batch_processor_kinesis_context_parser_model_with_partial_validation_error(
    kinesis_record_handler_model: Callable,
    kinesis_event_factory,
    order_event_factory,
):
    # GIVEN
    order_event = order_event_factory({"type": "success"})
    first_record = kinesis_event_factory(order_event)
    second_record = kinesis_event_factory(order_event)
    malformed_record = kinesis_event_factory('{"poison": "pill"}')
    records = [first_record, malformed_record, second_record]

    # WHEN
    processor = BatchProcessor(event_type=EventType.KinesisDataStreams, model=OrderKinesisRecord)
    with processor(records, kinesis_record_handler_model) as batch:
        batch.process()

    # THEN
    assert len(batch.fail_messages) == 1
    assert batch.response() == {
        "batchItemFailures": [
            {"itemIdentifier": malformed_record["kinesis"]["sequenceNumber"]},
        ],
    }


def test_async_batch_processor_model_with_partial_validation_error(
    async_record_handler_model: Callable,
    sqs_event_factory,
    order_event_factory,
):
    # GIVEN
    order_event = order_event_factory({"type": "success"})
    first_record = sqs_event_factory(order_event)
    second_record = sqs_event_factory(order_event)
    malformed_record = sqs_event_factory({"poison": "pill"})
    records = [first_record, malformed_record, second_record]

    # WHEN
    processor = AsyncBatchProcessor(event_type=EventType.SQS, model=OrderSqs)
    with processor(records, async_record_handler_model) as batch:
        batch.async_process()

    # THEN
    assert len(batch.fail_messages) == 1
    assert batch.response() == {
        "batchItemFailures": [
            {"itemIdentifier": malformed_record["messageId"]},
        ],
    }


def test_async_batch_processor_dynamodb_context_model_with_partial_validation_error(
    async_dynamodb_record_handler: Callable,
    dynamodb_event_factory,
    order_event_factory,
):
    # GIVEN
    order_event = order_event_factory({"type": "success"})
    first_record = dynamodb_event_factory(order_event)
    second_record = dynamodb_event_factory(order_event)
    malformed_record = dynamodb_event_factory({"poison": "pill"})
    records = [first_record, malformed_record, second_record]

    # WHEN
    processor = AsyncBatchProcessor(event_type=EventType.DynamoDBStreams, model=OrderDynamoDBRecord)
    with processor(records, async_dynamodb_record_handler) as batch:
        batch.async_process()

    # THEN
    assert len(batch.fail_messages) == 1
    assert batch.response() == {
        "batchItemFailures": [
            {"itemIdentifier": malformed_record["dynamodb"]["SequenceNumber"]},
        ],
    }


def test_async_batch_processor_kinesis_context_parser_model_with_partial_validation_error(
    async_kinesis_record_handler_model: Callable,
    kinesis_event_factory,
    order_event_factory,
):
    # GIVEN
    order_event = order_event_factory({"type": "success"})
    first_record = kinesis_event_factory(order_event)
    second_record = kinesis_event_factory(order_event)
    malformed_record = kinesis_event_factory('{"poison": "pill"}')
    records = [first_record, malformed_record, second_record]

    # WHEN
    processor = AsyncBatchProcessor(event_type=EventType.KinesisDataStreams, model=OrderKinesisRecord)
    with processor(records, async_kinesis_record_handler_model) as batch:
        batch.async_process()

    # THEN
    assert len(batch.fail_messages) == 1
    assert batch.response() == {
        "batchItemFailures": [
            {"itemIdentifier": malformed_record["kinesis"]["sequenceNumber"]},
        ],
    }
