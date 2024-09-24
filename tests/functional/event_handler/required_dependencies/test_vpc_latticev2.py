from aws_lambda_powertools.event_handler import (
    Response,
    VPCLatticeV2Resolver,
    content_types,
)
from aws_lambda_powertools.event_handler.api_gateway import CORSConfig
from aws_lambda_powertools.utilities.data_classes import VPCLatticeEventV2
from tests.functional.utils import load_event


def test_vpclatticev2_event():
    # GIVEN a VPC Lattice event
    app = VPCLatticeV2Resolver()

    @app.get("/newpath")
    def foo():
        assert isinstance(app.current_event, VPCLatticeEventV2)
        assert app.lambda_context == {}
        return Response(200, content_types.TEXT_HTML, "foo")

    # WHEN calling the event handler
    result = app(load_event("vpcLatticeV2Event.json"), {})

    # THEN process event correctly
    # AND set the current_event type as VPCLatticeEvent
    assert result["statusCode"] == 200
    assert result["headers"]["Content-Type"] == content_types.TEXT_HTML
    assert result["body"] == "foo"


def test_vpclatticev2_event_path_trailing_slash(json_dump):
    # GIVEN a VPC Lattice event
    app = VPCLatticeV2Resolver()

    @app.get("/newpath")
    def foo():
        assert isinstance(app.current_event, VPCLatticeEventV2)
        assert app.lambda_context == {}
        return Response(200, content_types.TEXT_HTML, "foo")

    # WHEN calling the event handler using path with trailing "/"
    result = app(load_event("vpcLatticeEventV2PathTrailingSlash.json"), {})

    # THEN
    assert result["statusCode"] == 404
    assert result["headers"]["Content-Type"] == content_types.APPLICATION_JSON
    expected = {"statusCode": 404, "message": "Not found"}
    assert result["body"] == json_dump(expected)


def test_cors_preflight_body_is_empty_not_null():
    # GIVEN CORS is configured
    app = VPCLatticeV2Resolver(cors=CORSConfig())

    event = {"path": "/my/request", "method": "OPTIONS", "headers": {}}

    # WHEN calling the event handler
    result = app(event, {})

    # THEN there body should be empty strings
    assert result["body"] == ""


def test_vpclatticev2_url_no_matches():
    # GIVEN a VPC Lattice event
    app = VPCLatticeV2Resolver()

    @app.post("/no_match")
    def foo():
        raise RuntimeError()

    # WHEN calling the event handler
    result = app(load_event("vpcLatticeV2Event.json"), {})

    # THEN process event correctly
    # AND return 404 because the event doesn't match any known route
    assert result["statusCode"] == 404
