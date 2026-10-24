"""The callable API, read from the app's own OpenAPI spec.

The spec is the one list of endpoints and their parameters, so the MCP tools
read it instead of keeping a second registry. Only ``GET`` operations under
``/api/v1/`` are exposed; health says nothing about the data.
"""

from collections.abc import Iterator, Mapping
from typing import Any
from urllib.parse import quote, urlencode

from app.mcp_server.models import OperationDetail, OperationSummary, ParameterInfo

_REF_PREFIX = "#/components/schemas/"

Spec = Mapping[str, Any]


class CatalogError(ValueError):
    """An unknown operation, or parameters that don't fit it."""


def _operations(spec: Spec) -> Iterator[tuple[str, dict[str, Any]]]:
    for path in sorted(spec["paths"]):
        op = spec["paths"][path].get("get")
        if op is not None and path.startswith("/api/v1/"):
            yield path, op


def _summary(path: str, op: dict[str, Any]) -> OperationSummary:
    return OperationSummary(
        operation_id=op["operationId"],
        method="GET",
        path=path,
        tag=op["tags"][0],
        summary=op.get("summary", ""),
    )


def _find(spec: Spec, operation_id: str) -> tuple[str, dict[str, Any]]:
    for path, op in _operations(spec):
        if op["operationId"] == operation_id:
            return path, op
    raise CatalogError(
        f"Unknown operation {operation_id!r}. Call list_api to see the operation ids."
    )


def list_operations(spec: Spec, query: str | None = None) -> list[OperationSummary]:
    """Callable operations whose id, path or summary contain ``query`` (or all)."""
    summaries = [_summary(path, op) for path, op in _operations(spec)]
    if not query:
        return summaries
    needle = query.lower()
    return [
        s
        for s in summaries
        if needle in s.operation_id.lower()
        or needle in s.path.lower()
        or needle in s.summary.lower()
    ]


def _refs(node: Any) -> Iterator[str]:
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith(_REF_PREFIX):
            yield ref.removeprefix(_REF_PREFIX)
        for value in node.values():
            yield from _refs(value)
    elif isinstance(node, list):
        for value in node:
            yield from _refs(value)


def describe_operation(spec: Spec, operation_id: str) -> OperationDetail:
    """One operation's parameters and response schema, with every ``$ref`` resolved.

    Raises:
        CatalogError: ``operation_id`` is not a callable operation.
    """
    path, op = _find(spec, operation_id)
    parameters = [
        ParameterInfo(
            name=p["name"],
            location=p["in"],
            required=p.get("required", False),
            description=p.get("description"),
            json_schema=p["schema"],
        )
        for p in op.get("parameters", [])
    ]
    response_schema = op["responses"]["200"]["content"]["application/json"]["schema"]

    schemas = spec.get("components", {}).get("schemas", {})
    components: dict[str, dict[str, Any]] = {}
    pending = list(_refs([response_schema, [p.json_schema for p in parameters]]))
    while pending:
        name = pending.pop()
        if name in components:
            continue
        components[name] = schemas[name]
        pending.extend(_refs(schemas[name]))

    return OperationDetail(
        **_summary(path, op).model_dump(),
        description=op.get("description"),
        parameters=parameters,
        response_schema=response_schema,
        components=components,
    )


def _encode_value(value: Any) -> Any:
    # bool first: it is an int subclass, and FastAPI expects "true", not "True".
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list | tuple):
        return [_encode_value(v) for v in value]
    return value


def build_request_path(spec: Spec, operation_id: str, params: Mapping[str, Any]) -> str:
    """The path and query string that call ``operation_id`` with ``params``.

    Raises:
        CatalogError: The operation is unknown, a parameter name is not one it
            takes, or a required parameter is missing.
    """
    path, op = _find(spec, operation_id)
    declared = {p["name"]: p for p in op.get("parameters", [])}
    # FastAPI ignores unknown query parameters, so a misspelt filter would
    # silently return unfiltered data.
    unknown = set(params) - set(declared)
    if unknown:
        raise CatalogError(
            f"{operation_id} does not take {sorted(unknown)}. "
            f"It takes: {sorted(declared)}."
        )
    missing = {
        name
        for name, p in declared.items()
        if p.get("required") and params.get(name) is None
    }
    if missing:
        raise CatalogError(f"{operation_id} requires {sorted(missing)}.")

    query: dict[str, Any] = {}
    for name, value in params.items():
        if value is None:
            continue
        if declared[name]["in"] == "path":
            path = path.replace(
                f"{{{name}}}", quote(str(_encode_value(value)), safe="")
            )
        else:
            query[name] = _encode_value(value)
    return f"{path}?{urlencode(query, doseq=True)}" if query else path
