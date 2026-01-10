import json
from pathlib import Path
from typing import Any

import jsonschema


def load_schema(name: str) -> dict[str, Any]:
    # Schemas are in ../story/schemas
    # But wait, utils is in vtx_app, story is in vtx_app.
    # Relative path: ../story/schemas/{name}.schema.json
    here = Path(__file__).parent
    schema_path = here.parent / "story" / "schemas" / f"{name}.schema.json"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")

    return json.loads(schema_path.read_text())


def validate_clip_spec(spec: dict[str, Any]) -> None:
    schema = load_schema("clip")
    jsonschema.validate(instance=spec, schema=schema)
