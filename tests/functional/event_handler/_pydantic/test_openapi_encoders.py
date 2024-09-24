import math
from collections import deque
from dataclasses import dataclass

import pytest
from pydantic import BaseModel

from aws_lambda_powertools.event_handler.openapi.encoders import jsonable_encoder
from aws_lambda_powertools.event_handler.openapi.exceptions import SerializationError


def test_openapi_encode_include():
    class User(BaseModel):
        name: str
        age: int

    result = jsonable_encoder(User(name="John", age=20), include=["name"])
    assert result == {"name": "John"}


def test_openapi_encode_exclude():
    class User(BaseModel):
        name: str
        age: int

    result = jsonable_encoder(User(name="John", age=20), exclude=["age"])
    assert result == {"name": "John"}


def test_openapi_encode_pydantic():
    class Order(BaseModel):
        quantity: int

    class User(BaseModel):
        name: str
        order: Order

    result = jsonable_encoder(User(name="John", order=Order(quantity=2)))
    assert result == {"name": "John", "order": {"quantity": 2}}


def test_openapi_encode_dataclass():
    @dataclass
    class Order:
        quantity: int

    @dataclass
    class User:
        name: str
        order: Order

    result = jsonable_encoder(User(name="John", order=Order(quantity=2)))
    assert result == {"name": "John", "order": {"quantity": 2}}


def test_openapi_encode_enum():
    from enum import Enum

    class Color(Enum):
        RED = "red"
        GREEN = "green"
        BLUE = "blue"

    result = jsonable_encoder(Color.RED)
    assert result == "red"


def test_openapi_encode_purepath():
    from pathlib import PurePath

    result = jsonable_encoder(PurePath("/foo/bar"))
    assert result == "/foo/bar"


def test_openapi_encode_scalars():
    result = jsonable_encoder("foo")
    assert result == "foo"

    result = jsonable_encoder(1)
    assert result == 1

    result = jsonable_encoder(1.0)
    assert math.isclose(result, 1.0)

    result = jsonable_encoder(True)
    assert result is True

    result = jsonable_encoder(None)
    assert result is None


def test_openapi_encode_dict():
    result = jsonable_encoder({"foo": "bar"})
    assert result == {"foo": "bar"}


def test_openapi_encode_dict_with_include():
    result = jsonable_encoder({"foo": "bar", "bar": "foo"}, include=["foo"])
    assert result == {"foo": "bar"}


def test_openapi_encode_dict_with_exclude():
    result = jsonable_encoder({"foo": "bar", "bar": "foo"}, exclude=["bar"])
    assert result == {"foo": "bar"}


def test_openapi_encode_sequences():
    result = jsonable_encoder(["foo", "bar"])
    assert result == ["foo", "bar"]

    result = jsonable_encoder(("foo", "bar"))
    assert result == ["foo", "bar"]

    result = jsonable_encoder({"foo", "bar"})
    assert set(result) == {"foo", "bar"}

    result = jsonable_encoder(frozenset(("foo", "bar")))
    assert set(result) == {"foo", "bar"}


def test_openapi_encode_bytes():
    result = jsonable_encoder(b"foo")
    assert result == "foo"


def test_openapi_encode_timedelta():
    from datetime import timedelta

    result = jsonable_encoder(timedelta(seconds=1))
    assert result == 1


def test_openapi_encode_decimal():
    from decimal import Decimal

    result = jsonable_encoder(Decimal("1.0"))
    assert math.isclose(result, 1.0)

    result = jsonable_encoder(Decimal("1"))
    assert result == 1


def test_openapi_encode_uuid():
    from uuid import UUID

    result = jsonable_encoder(UUID("123e4567-e89b-12d3-a456-426614174000"))
    assert result == "123e4567-e89b-12d3-a456-426614174000"


def test_openapi_encode_encodable():
    from datetime import date, datetime, time

    result = jsonable_encoder(date(2021, 1, 1))
    assert result == "2021-01-01"

    result = jsonable_encoder(datetime(2021, 1, 1, 0, 0, 0))
    assert result == "2021-01-01T00:00:00"

    result = jsonable_encoder(time(0, 0, 0))
    assert result == "00:00:00"


def test_openapi_encode_subclasses():
    class MyCustomSubclass(deque):
        pass

    result = jsonable_encoder(MyCustomSubclass(["red"]))
    assert result == ["red"]


def test_openapi_encode_other():
    class User:
        def __init__(self, name: str):
            self.name = name

    result = jsonable_encoder(User(name="John"))
    assert result == {"name": "John"}


def test_openapi_encode_with_error():
    class MyClass:
        __slots__ = []

    with pytest.raises(SerializationError, match="Unable to serialize the object*"):
        jsonable_encoder(MyClass())


def test_openapi_encode_custom_serializer_nested_dict():
    # GIVEN a nested dictionary with a custom class
    class CustomClass: ...

    nested_dict = {"a": {"b": CustomClass()}}

    # AND a custom serializer
    def serializer(value):
        return "serialized"

    # WHEN we call jsonable_encoder with the nested dictionary and unserializable value
    result = jsonable_encoder(nested_dict, custom_serializer=serializer)

    # THEN we should get the custom serializer output
    assert result == {"a": {"b": "serialized"}}


def test_openapi_encode_custom_serializer_sequences():
    # GIVEN a sequence with a custom class
    class CustomClass:
        __slots__ = []

    seq = [CustomClass()]

    # AND a custom serializer
    def serializer(value):
        return "serialized"

    # WHEN we call jsonable_encoder with the nested dictionary and unserializable value
    result = jsonable_encoder(seq, custom_serializer=serializer)

    # THEN we should get the custom serializer output
    assert result == ["serialized"]


def test_openapi_encode_custom_serializer_dataclasses():
    # GIVEN a sequence with a custom class
    class CustomClass:
        __slots__ = []

    @dataclass
    class Order:
        kind: CustomClass

    order = Order(kind=CustomClass())

    # AND a custom serializer
    def serializer(value):
        return "serialized"

    # WHEN we call jsonable_encoder with the nested dictionary and unserializable value
    result = jsonable_encoder(order, custom_serializer=serializer)

    # THEN we should get the custom serializer output
    assert result == {"kind": "serialized"}
