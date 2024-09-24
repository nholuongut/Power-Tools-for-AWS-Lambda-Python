import json
import warnings
from typing import Literal, Optional

import pytest
from pydantic import BaseModel, Field
from typing_extensions import Annotated

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.models import Contact, License, Server
from aws_lambda_powertools.event_handler.openapi.params import Query
from aws_lambda_powertools.event_handler.openapi.types import OpenAPIResponse


@pytest.mark.usefixtures("pydanticv2_only")
def test_openapi_3_1_simple_handler(openapi31_schema):
    # GIVEN APIGatewayRestResolver is initialized with enable_validation=True
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN we have a simple handler
    @app.get("/")
    def handler():
        pass

    # WHEN we get the schema
    schema = json.loads(app.get_openapi_json_schema())

    # THEN the schema should be valid
    assert openapi31_schema(schema)


@pytest.mark.usefixtures("pydanticv2_only")
def test_openapi_3_0_with_pydantic_v2():
    # GIVEN APIGatewayRestResolver is initialized with enable_validation=True
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN we get the schema
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("default")
        app.get_openapi_json_schema(openapi_version="3.0.0")
        assert len(w) == 1
        assert str(w[-1].message) == (
            "You are using Pydantic v2, which is incompatible with OpenAPI schema 3.0. Forcing OpenAPI 3.1"
        )


@pytest.mark.usefixtures("pydanticv2_only")
def test_openapi_3_1_complex_handler(openapi31_schema):
    # GIVEN APIGatewayRestResolver is initialized with enable_validation=True
    app = APIGatewayRestResolver(enable_validation=True)

    # GIVEN a complex pydantic model
    class TodoAttributes(BaseModel):
        userId: int
        id_: Optional[int] = Field(alias="id", default=None)
        title: str
        completed: bool

    class Todo(BaseModel):
        type: Literal["ingest"]
        attributes: TodoAttributes

    class TodoEnvelope(BaseModel):
        data: Annotated[Todo, Field(description="The todo")]

    # WHEN we have a complex handler
    @app.get(
        "/",
        summary="This is a summary",
        description="Gets todos",
        tags=["users", "operations", "todos"],
        responses={
            204: OpenAPIResponse(
                description="Successful creation",
                content={"": {"schema": {}}},
            ),
        },
    )
    def handler(
        name: Annotated[str, Query(description="The name", min_length=10, max_length=20)] = "John Doe Junior",
    ) -> TodoEnvelope: ...

    @app.post(
        "/todos",
        tags=["todo"],
        responses={
            204: OpenAPIResponse(
                description="Successful creation",
                content={"": {"schema": {}}},
            ),
        },
    )
    def create_todo(todo: TodoEnvelope): ...

    # WHEN we get the schema
    schema = json.loads(
        app.get_openapi_json_schema(
            title="My little API",
            version="69",
            openapi_version="3.1.0",
            summary="API Summary",
            description="API description",
            tags=["api"],
            servers=[Server(url="http://localhost")],
            terms_of_service="Yes",
            contact=Contact(name="John Smith"),
            license_info=License(name="MIT"),
        ),
    )

    # THEN the schema should be valid
    assert openapi31_schema(schema)
