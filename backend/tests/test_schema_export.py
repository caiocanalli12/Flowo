from scripts.export_schema import SCHEMA_PATH, render_schema


def test_committed_schema_matches_models() -> None:
    """O JSON Schema versionado precisa refletir os modelos Pydantic atuais."""
    assert SCHEMA_PATH.read_text(encoding="utf-8") == render_schema(), (
        f"{SCHEMA_PATH.name} is out of date with the Pydantic models: run `make types` "
        "and commit the regenerated schema and TypeScript types."
    )
