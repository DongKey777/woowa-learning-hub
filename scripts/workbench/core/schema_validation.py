from __future__ import annotations

import json
from pathlib import Path

from .paths import ROOT

SCHEMA_DIR = ROOT / "schemas"


class SchemaValidationError(RuntimeError):
    pass


def _schema_path(name: str) -> Path:
    return SCHEMA_DIR / f"{name}.schema.json"


def _load_schema(name: str) -> dict:
    return json.loads(_schema_path(name).read_text(encoding="utf-8"))


def _check_type(value, expected) -> bool:
    if isinstance(expected, list):
        return any(_check_type(value, item) for item in expected)

    mapping = {
        "string": str,
        "integer": int,
        "boolean": bool,
        "array": list,
        "object": dict,
        "null": type(None),
    }
    if expected not in mapping:
        return True
    return isinstance(value, mapping[expected])


def _validate(schema: dict, value, path: str = "$") -> None:
    expected_type = schema.get("type")
    if expected_type is not None and not _check_type(value, expected_type):
        raise SchemaValidationError(f"{path}: expected type {expected_type}, got {type(value).__name__}")

    if "const" in schema and value != schema["const"]:
        raise SchemaValidationError(f"{path}: expected const {schema['const']}, got {value}")

    if "enum" in schema and value not in schema["enum"]:
        raise SchemaValidationError(f"{path}: value {value!r} not in enum {schema['enum']}")

    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            raise SchemaValidationError(f"{path}: string length {len(value)} < minLength {schema['minLength']}")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            raise SchemaValidationError(f"{path}: string length {len(value)} > maxLength {schema['maxLength']}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise SchemaValidationError(f"{path}: value {value} < minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            raise SchemaValidationError(f"{path}: value {value} > maximum {schema['maximum']}")

    if isinstance(value, dict):
        required = schema.get("required", [])
        for field in required:
            if field not in value:
                raise SchemaValidationError(f"{path}: missing required field '{field}'")

        properties = schema.get("properties", {})
        for field, field_schema in properties.items():
            if field in value:
                _validate(field_schema, value[field], f"{path}.{field}")

    if isinstance(value, list):
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                _validate(item_schema, item, f"{path}[{index}]")


def validate_payload(schema_name: str, payload: dict) -> None:
    schema = _load_schema(schema_name)
    _validate(schema, payload)


def validate_file(schema_name: str, path: Path) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    validate_payload(schema_name, payload)
