# Django JSON Schema Editor

A powerful Django widget for integrating [`@json-editor/json-editor`](https://www.npmjs.com/package/@json-editor/json-editor) with Django forms and admin interfaces. It provides a rich, schema-based editing experience for JSON data in Django applications.

See [the blog post for the announcement and a screenshot](https://406.ch/writing/django-json-schema-editor/).

## Features

- Schema-based validation for JSON data
- Django admin integration
- Rich text editing capabilities with optional prose editor
- Foreign key references with Django admin lookups
- Referential integrity for JSON data containing model references

## JSON Schema Support

The widget supports the [JSON Schema](https://json-schema.org/) standard for defining the structure and validation rules of your JSON data. Notable supported features include:

- Basic types: string, number, integer, boolean, array, object
- Format validations: date, time, email, etc.
- Custom formats: prose (rich text), foreign_key (model references)
- Required properties
- Enums and default values
- Nested objects and arrays

The [documentation for the json-editor](https://www.npmjs.com/package/@json-editor/json-editor) offers a good overview over all supported features.

## Installation

```bash
pip install django-json-schema-editor
```

For django-prose-editor support (rich text editing):

```bash
pip install django-json-schema-editor[prose]
```

For JSON pointer support in feincms3 plugins:

```bash
pip install django-json-schema-editor[jsonpointer]
```

## Usage

### Basic Setup

1. Add `django_json_schema_editor` to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    'django_json_schema_editor',
    # ...
]
```

2. Use the `JSONField` in your models:

```python
from django.db import models
from django_json_schema_editor.fields import JSONField

class MyModel(models.Model):
    data = JSONField(
        schema={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "count": {"type": "integer"},
            },
            "required": ["title", "description", "count"],
        }
    )
```

**Note!** ``required`` contains a list of properties which should exist in the
JSON blob. The values themselves do not have to be truthy. The advantage of
always specifying ``required`` is that the properties are automatically shown
also when editing data which was added when those properties didn't all exist
yet.

### Rich Text Editing

For rich text editing, use the `prose` format:

```python
class MyModel(models.Model):
    data = JSONField(
        schema={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string", "format": "prose"},
            },
            "required": ["title", "content"],
        }
    )
```

#### Configuring Prose Editor Extensions

You can customize which formatting options are available in the prose editor by
specifying extensions in the field options:

```python
class MyModel(models.Model):
    data = JSONField(
        schema={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {
                    "type": "string",
                    "format": "prose",
                    "options": {
                        "extensions": {
                            "Bold": True,
                            "Italic": True,
                            # Only Bold and Italic will be available
                            # (core extensions are always included)
                        }
                    }
                },
            },
            "required": ["title", "content"],
        }
    )
```

The prose editor always includes core extensions (Document, Paragraph,
HardBreak, Text, Menu). By default, it also includes Bold, Italic, Underline,
Subscript, and Superscript extensions. When you specify custom extensions, only
the core extensions plus your specified extensions will be active.

### Foreign Key References

You can reference Django models in your JSON data:

```python
class MyModel(models.Model):
    data = JSONField(
        schema={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "image": {
                    "type": "string",
                    "format": "foreign_key",
                    "options": {
                        "url": "/admin/myapp/image/?_popup=1&_to_field=id",
                    },
                },
            },
            "required": ["title", "image"],
        }
    )
```

### Data References and Referential Integrity

One of the most powerful features is the ability to maintain referential
integrity between JSON data and model instances:

```python
from django.db import models
from django_json_schema_editor.fields import JSONField

class Image(models.Model):
    title = models.CharField(max_length=100)
    file = models.FileField(upload_to='images/')

class Article(models.Model):
    data = JSONField(
        schema={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string", "format": "prose"},
                "featured_image": {
                    "type": "string",
                    "format": "foreign_key",
                    "options": {
                        "url": "/admin/myapp/image/?_popup=1&_to_field=id",
                    },
                },
            },
            "required": ["title", "content", "featured_image"],
        }
    )

def get_image_ids(article):
    if image_id := article.data.get("featured_image"):
        return [int(image_id)]
    return []

# Register the reference to prevent images from being deleted when they're referenced
Article.register_data_reference(
    Image,
    name="featured_images",
    getter=get_image_ids,
)
```

This prevents a referenced image from being deleted as long as it's referenced in an article's JSON data.

The `name` field will be the name of the underlying `ManyToManyField` which actually references the `Image` instances.

Note that the `get_image_ids` getter has to be written in a very conservative way -- you cannot be sure that the model is valid otherwise. For example, you cannot assume that foreign key values are set (even when they are `null=False`). Django's validation hasn't cleared the model before the getter is invoked for the first time.

### feincms3 JSON Plugin Support

Django JSON Schema Editor provides enhanced support for feincms3 JSON plugins with self-describing capabilities using JSON pointers. This allows for more intelligent display names and better integration with feincms3's plugin system.

#### Self-Describing JSON Plugins

When using the `jsonpointer` optional dependency, you can define schemas that describe how to extract display values from the JSON data:

```python
from django_json_schema_editor.plugins import JSONPluginBase

class TextPlugin(JSONPluginBase):
    SCHEMA = {
        "type": "object",
        "title": "Text Block",
        "__str__": "/title",  # JSON pointer to extract display value
        "properties": {
            "title": {
                "type": "string",
                "title": "Title",
            },
            "content": {
                "type": "string",
                "format": "prose",
                "title": "Content",
            },
        },
        "required": ["title", "content"],
    }
```

With this setup:

1. **Display Names**: The `__str__` method will use the JSON pointer (`/title`) to extract a display value from the plugin's data
2. **Fallback Behavior**: If the JSON pointer fails or the value is empty, it falls back to the schema's `title` field
3. **Default Fallback**: If neither JSON pointer nor title are available, it falls back to the standard plugin type name

#### Installation for feincms3 Support

To use JSON pointer functionality, install the optional dependency:

```bash
pip install django-json-schema-editor[jsonpointer]
```

#### JSON Pointer Syntax

The `__str__` field in your schema should contain a valid JSON pointer as defined by RFC 6901. For example, `/title` points to the `title` property at the root level of your JSON data.

This feature makes feincms3 plugin instances much more readable in the admin interface and throughout your application.

## Development

To set up the development environment:

1. Clone the repository
2. Install development dependencies:

```bash
pip install -e ".[tests,prose]"
```

### Code Quality

This project uses several tools to maintain code quality:

- **pre-commit**: We use pre-commit hooks to ensure consistent code style and quality
- **ruff**: For Python linting and formatting
- **biome**: For JavaScript and CSS linting and formatting

To set up pre-commit:

```bash
uv tool install pre-commit
pre-commit install
```

The pre-commit configuration includes:
- Basic file checks (trailing whitespace, merge conflicts, etc.)
- Django upgrade checks
- Ruff for Python linting and formatting
- Biome for JavaScript and CSS linting and formatting
- pyproject.toml validations

### Running Tests

```bash
pytest
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
