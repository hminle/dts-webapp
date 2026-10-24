"""The API catalog the MCP tools read from the app's OpenAPI spec."""

import pytest

from app.main import app
from app.mcp_server import openapi_catalog
from app.mcp_server.openapi_catalog import (
    CatalogError,
    build_request_path,
    describe_operation,
    list_operations,
)

spec = app.openapi()


def test_lists_every_v1_get_operation() -> None:
    ops = list_operations(spec)
    assert len(ops) == 20
    assert {op.method for op in ops} == {"GET"}
    assert all(op.path.startswith("/api/v1/") for op in ops)
    assert [op.path for op in ops] == sorted(op.path for op in ops)


def test_query_filters_case_insensitively() -> None:
    ids = {op.operation_id for op in list_operations(spec, "NET-TRANSFERS")}
    assert ids == {"net_transfers_get_for_date", "net_transfers_get_for_fiscal_year"}


def test_query_matches_summary() -> None:
    op = spec["paths"]["/api/v1/weekly/comparison"]["get"]
    word = op["summary"].split()[-1]
    ids = {o.operation_id for o in list_operations(spec, word)}
    assert op["operationId"] in ids


def test_describe_path_parameter() -> None:
    detail = describe_operation(spec, "net_transfers_get_for_date")
    [param] = detail.parameters
    assert (param.name, param.location, param.required) == ("date", "path", True)


def _refs(node: object) -> set[str]:
    if isinstance(node, dict):
        found = {node["$ref"].rsplit("/", 1)[-1]} if "$ref" in node else set()
        return found.union(*(_refs(v) for v in node.values()))
    if isinstance(node, list):
        return set().union(*(_refs(v) for v in node))
    return set()


def test_describe_inlines_refs() -> None:
    detail = describe_operation(spec, "net_transfers_get_for_date")
    assert "DailyNetTransfer" in detail.components
    assert _refs(detail.model_dump()) <= set(detail.components)


def test_describe_unknown_operation() -> None:
    with pytest.raises(CatalogError, match="list_api"):
        describe_operation(spec, "nope")


def test_build_path_substitutes_path_params() -> None:
    path = build_request_path(
        spec, "net_transfers_get_for_date", {"date": "2025-10-10"}
    )
    assert path == "/api/v1/net-transfers/date/2025-10-10"


def test_build_path_encodes_query() -> None:
    path = build_request_path(
        spec,
        "data_list_data",
        {"page_size": 5, "data_source": "deposits_withdrawals", "fiscal_year": None},
    )
    assert path == "/api/v1/data?page_size=5&data_source=deposits_withdrawals"


def test_build_path_repeats_list_values() -> None:
    path = build_request_path(
        spec,
        "yoy_get_category_comparison",
        {
            "current_fiscal_year": 2026,
            "previous_fiscal_year": 2025,
            "category_descriptions": ["A", "B"],
        },
    )
    assert "category_descriptions=A&category_descriptions=B" in path


def test_build_path_lowercases_bools() -> None:
    # No operation takes a boolean today, so test the encoder directly.
    assert openapi_catalog._encode_value(True) == "true"
    assert openapi_catalog._encode_value([False]) == ["false"]
    assert openapi_catalog._encode_value(1) == 1


def test_build_path_rejects_unknown_param() -> None:
    with pytest.raises(CatalogError, match="It takes: \\['account_type'"):
        build_request_path(spec, "data_list_data", {"nope": 1})


def test_build_path_requires_path_param() -> None:
    with pytest.raises(CatalogError, match="date"):
        build_request_path(spec, "net_transfers_get_for_date", {})
