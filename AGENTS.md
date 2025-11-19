# Agent Notes for django-json-schema-editor

This document contains information for AI agents working on this project.

## Project Structure

- **Python/Django Backend**: Django app in `django_json_schema_editor/`
- **Tests**: Python tests in `tests/testapp/`, uses Playwright for E2E tests
- **Documentation**: ReStructuredText (`.rst`) files in `docs/` directory (if present)

## Running Tests

Use `tox` to run tests:

```bash
# Run tests with Python 3.12 and Django 5.2
tox -e py312-dj52

# Run tests with Python 3.13 and Django 5.2
tox -e py313-dj52

# Pass pytest arguments after "--"
tox -e py312-dj52 -- -v -k test_json_editor
tox -e py312-dj52 -- tests/testapp/test_json_editor.py::test_validation
```

Tests include both unit tests and Playwright E2E tests. The test suite will automatically install Chromium if needed.

## Project Overview

This project provides a Django widget that integrates `@json-editor/json-editor` with Django forms and admin interfaces. It enables schema-based editing of JSON data with features like:

- JSON Schema validation
- Rich text editing via optional django-prose-editor integration
- Foreign key references with Django admin lookups
- Referential integrity for JSON data containing model references

## Key Components

### JSONField (django_json_schema_editor/fields.py)

The main field class that extends Django's JSONField with:
- Schema validation support
- Foreign key description resolution
- Data reference tracking for referential integrity
- Form field generation with JSONEditorField

### JSONPluginBase (django_json_schema_editor/plugins.py)

Base class for feincms3 JSON plugins with features like:
- Self-describing plugins using JMESPath for `__str__` values
- Foreign key path specifications for nested data
- Proxy plugin creation with `JSONPluginBase.proxy()`

### JSONEditorField (django_json_schema_editor/forms.py)

Form field that provides:
- JSON Schema editor widget in Django admin
- Foreign key lookup integration
- Rich text (prose) editor support

## Testing Workflow

1. Make code changes to Python files
2. Run linting/formatting: `prek run --all-files` (uses ruff for Python, biome for JS/CSS)
3. Run tests: `tox -e py312-dj52` (tests must be run through tox)
4. Verify all tests pass
5. Update documentation if needed

## Common Patterns

### Foreign Key References

The project supports two approaches for handling foreign key references in JSON data:

#### 1. Manual registration with JSONField

```python
from django_json_schema_editor.fields import JSONField

class Article(models.Model):
    data = JSONField(schema={...})

def get_image_ids(article):
    if image_id := article.data.get("featured_image"):
        return [int(image_id)]
    return []

Article.register_data_reference(Image, name="featured_images", getter=get_image_ids)
```

**Important**: Getter functions must be defensive - don't assume the model is valid, as Django validation hasn't cleared the model before the getter is first invoked.

#### 2. Declarative approach with JSON plugins

```python
from django_json_schema_editor.plugins import JSONPluginBase

VocabularyPlugin = JSONPluginBase.proxy(
    "vocabulary_table",
    verbose_name="Vocabulary Table",
    schema=SCHEMA,
    foreign_key_paths={
        "files.file": ["items[*].audiofile", "items[*].example_audiofile"],
    },
)
```

Uses JMESPath expressions to locate foreign keys in nested JSON structures.

### Referential Integrity

The project provides referential integrity by creating many-to-many relationships through intermediate models:

- Foreign key references in JSON data are tracked
- Referenced models are protected from deletion (PROTECT constraint)
- References are automatically updated when JSON data changes
- Invalid references are validated during model validation

### Rich Text Editing

Fields can use the `"format": "prose"` option in their JSON schema to enable django-prose-editor:

```python
{
    "type": "string",
    "format": "prose",
    "options": {
        "extensions": {
            "Bold": True,
            "Italic": True,
        }
    }
}
```

Core extensions (Document, Paragraph, HardBreak, Text, Menu) are always included.

## Test Structure

- `test_json_editor.py`: Tests for JSONField, foreign key validation, and E2E browser tests
- `test_json_plugins.py`: Tests for JSONPluginBase functionality and JMESPath support
- E2E tests use Playwright with Chromium
- Tests are marked with `@pytest.mark.e2e` for browser tests and `@pytest.mark.django_db` for database access

### Testing Style

- Use flat test functions rather than test classes (pytest style)
- Only use test classes when they provide meaningful structure/grouping benefits
- Test function names should be descriptive and start with `test_`

## Code Quality Tools

- **prek**: Rust-based pre-commit alternative that runs linting/formatting hooks (primary tool)
- **pre-commit**: Alternative if installed (optional)
- **ruff**: Python linting and formatting
- **biome**: JavaScript and CSS linting and formatting (if JS files present)

To run linting/formatting:
```bash
prek run --all-files
```

Or with pre-commit (if installed):
```bash
pre-commit run --all-files
```
