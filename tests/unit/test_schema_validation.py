"""Validator-level tests for ``scripts.workbench.core.schema_validation``.

Locks in the PR#3 hardenings:

- ``"number"`` accepts ``int`` and ``float`` but **not** ``bool``.
- ``"integer"`` rejects ``bool`` (Python treats ``True`` as ``int``, schema must not).
- Unknown types raise instead of silently passing.
- ``additionalProperties: false`` rejects unexpected keys when explicitly set.
- Nested items objects honor required + enum constraints.
"""

from __future__ import annotations

import unittest

from scripts.workbench.core.schema_validation import (
    SchemaValidationError,
    _validate,
)


class CheckTypeTest(unittest.TestCase):
    def test_number_accepts_int_and_float(self) -> None:
        _validate({"type": "number"}, 1)
        _validate({"type": "number"}, 1.5)

    def test_number_rejects_bool(self) -> None:
        with self.assertRaises(SchemaValidationError):
            _validate({"type": "number"}, True)

    def test_integer_rejects_bool(self) -> None:
        with self.assertRaises(SchemaValidationError):
            _validate({"type": "integer"}, False)

    def test_integer_rejects_float(self) -> None:
        with self.assertRaises(SchemaValidationError):
            _validate({"type": "integer"}, 1.5)

    def test_unknown_type_raises_instead_of_silent_pass(self) -> None:
        # Pre-PR#3 behavior was a silent True. Lock in the new contract.
        with self.assertRaises(SchemaValidationError) as ctx:
            _validate({"type": "decimal"}, 1.0)
        self.assertIn("unknown schema type", str(ctx.exception))

    def test_type_union_still_works(self) -> None:
        _validate({"type": ["string", "null"]}, None)
        _validate({"type": ["string", "null"]}, "hi")
        with self.assertRaises(SchemaValidationError):
            _validate({"type": ["string", "null"]}, 1)


class AdditionalPropertiesTest(unittest.TestCase):
    def test_extras_rejected_when_closed(self) -> None:
        schema = {
            "type": "object",
            "properties": {"a": {"type": "string"}},
            "additionalProperties": False,
        }
        _validate(schema, {"a": "ok"})
        with self.assertRaises(SchemaValidationError) as ctx:
            _validate(schema, {"a": "ok", "extra": 1})
        self.assertIn("unexpected properties", str(ctx.exception))

    def test_extras_allowed_when_unset(self) -> None:
        # Open-world default: top-level coach-run-result must keep this so
        # forward-compat optional fields don't break old consumers.
        schema = {"type": "object", "properties": {"a": {"type": "string"}}}
        _validate(schema, {"a": "ok", "anything": 42})


class NestedItemsTest(unittest.TestCase):
    def test_items_required_field_enforced(self) -> None:
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name"],
                "properties": {"name": {"type": "string"}},
            },
        }
        _validate(schema, [{"name": "ok"}])
        with self.assertRaises(SchemaValidationError) as ctx:
            _validate(schema, [{"other": 1}])
        self.assertIn("missing required field 'name'", str(ctx.exception))

    def test_items_enum_enforced(self) -> None:
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"status": {"enum": ["a", "b"]}},
            },
        }
        _validate(schema, [{"status": "a"}])
        with self.assertRaises(SchemaValidationError):
            _validate(schema, [{"status": "c"}])


if __name__ == "__main__":
    unittest.main()
