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

#### Displaying Foreign Key Labels

By default, foreign key fields only store the primary key value. To display human-readable labels in the admin interface, use the `foreign_key_descriptions` parameter:

```python
class Article(models.Model):
    data = JSONField(
        schema={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "featured_image": {
                    "type": "string",
                    "format": "foreign_key",
                    "options": {
                        "url": "/admin/myapp/image/?_popup=1&_to_field=id",
                    },
                },
                "gallery": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "format": "foreign_key",
                        "options": {
                            "url": "/admin/myapp/image/?_popup=1&_to_field=id",
                        },
                    },
                },
            },
            "required": ["title"],
        },
        foreign_key_descriptions=[
            ("myapp.image", lambda data: [
                pk for pk in [data.get("featured_image")] + data.get("gallery", []) if pk
            ]),
        ],
    )
```

The `foreign_key_descriptions` parameter accepts a list of tuples, where each tuple contains:
1. **Model label** (string): The model's app label and model name in the format `"app_label.model_name"`
2. **Getter function**: A callable that takes the JSON data and returns a **list** of primary keys to resolve

**Important**: The getter function must always return a list of primary keys (even for single foreign key values), which will be resolved to display strings in the admin interface.

### Data References and Referential Integrity

One of the most powerful features is the ability to maintain referential integrity between JSON data and model instances. This prevents referenced objects from being deleted while they're still in use.

#### Basic Usage with JSONField

For regular Django models using `JSONField`, you can manually register data references:

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

**Important**: The `get_image_ids` getter must be written defensively -- you cannot assume the model is valid. For example, you cannot assume that foreign key values are set (even when they are `null=False`). Django's validation hasn't cleared the model before the getter is invoked for the first time.

You can use the `paths_to_pks` utility also; the `get_image_ids` implementation using it would look like this:

```python
from django_json_schema_editor.fields import paths_to_pks

def get_image_ids(article):
    return paths_to_pks(to=Image, paths=["featured_image"], data=article.data)
```

#### Streamlined Approach with foreign_key_paths

For JSON plugins (see the feincms3 section below), the `foreign_key_paths` parameter provides a more declarative way to achieve the same result without writing manual getter functions. Instead of extracting values with custom Python code, you specify JMESPath expressions that locate foreign keys in your JSON structure.

### feincms3 JSON Plugin Support

Django JSON Schema Editor provides enhanced support for feincms3 JSON plugins with self-describing capabilities using jmespath values. This allows for more intelligent display names and better integration with feincms3's plugin system.

#### Self-Describing JSON Plugins

When using the `jmespath` dependency, you can define schemas that describe how to extract display values from the JSON data:

```python
from django_json_schema_editor.plugins import JSONPluginBase

class TextPlugin(JSONPluginBase):
    SCHEMA = {
        "type": "object",
        "title": "Text Block",
        "__str__": "title",  # jmespath to extract display value
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

1. **Display Names**: The `__str__` method will use the jmespath (`title`) to extract a display value from the plugin's data
2. **Fallback Behavior**: If the jmespath fails or the value is empty, it falls back to the schema's `title` field
3. **Default Fallback**: As a last resort, it falls back to the standard plugin type name

This feature makes feincms3 plugin instances much more readable in the admin interface and throughout your application.

#### Foreign Key References in JSON Plugins

When your JSON plugins contain foreign key references, you can use `foreign_key_paths` to streamline the configuration:

```python
from django_json_schema_editor.plugins import JSONPluginBase

class VocabularyPlugin(JSONPluginBase):
    SCHEMA = {
        "type": "object",
        "title": "Vocabulary Table",
        "__str__": "title",
        "properties": {
            "title": {"type": "string"},
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "word": {"type": "string"},
                        "audiofile": {
                            "type": "string",
                            "format": "foreign_key",
                            "options": {
                                "url": "/admin/files/file/?_popup=1&_to_field=id",
                                "model": "files.file",
                            },
                        },
                        "example": {"type": "string"},
                        "example_audiofile": {
                            "type": "string",
                            "format": "foreign_key",
                            "options": {
                                "url": "/admin/files/file/?_popup=1&_to_field=id",
                                "model": "files.file",
                            },
                        },
                    },
                },
            },
        },
    }

# Create the proxy plugin with foreign_key_paths
VocabularyTablePlugin = JSONPluginBase.proxy(
    "vocabulary_table",
    verbose_name="Vocabulary Table",
    schema=SCHEMA,
    foreign_key_paths={
        "files.file": ["items[*].audiofile", "items[*].example_audiofile"],
    },
)
```

The `foreign_key_paths` parameter:
- **Key**: Model label in the format `"app_label.model_name"`
- **Value**: List of JMESPath expressions that locate foreign key values in the JSON data
- Supports complex paths including array wildcards (`[*]`) for nested structures

This provides two main benefits:

1. **Referential Integrity**: When combined with `register_foreign_key_reference()`, it automatically prevents referenced models from being deleted while they're in use
2. **Admin Display**: In the admin interface (via `JSONPluginInline`), foreign key values are automatically resolved to display human-readable labels

##### Setting Up Referential Integrity

After defining your plugin proxy classes, register them to maintain referential integrity:

```python
# Register foreign key relationships for all plugins
ChapterStructuredData.register_foreign_key_reference(
    File,  # The model being referenced
    name="referenced_files",  # Name for the M2M relationship
)
```

This will automatically:
- Extract foreign key values from your JSON data using the `foreign_key_paths` defined in each plugin
- Create many-to-many relationships to track these references
- Prevent deletion of referenced models when they're in use

The `foreign_key_paths` approach is more maintainable than manually writing getter functions, especially when dealing with nested arrays or multiple foreign key fields in your JSON schema.

#### Extending Proxy Plugins with Mixins

When creating proxy plugins with `JSONPluginBase.proxy()`, you can add custom functionality using the `mixins` parameter:

```python
from django_json_schema_editor.plugins import JSONPluginBase

class RenderMixin:
    def render(self):
        """Custom rendering logic for this plugin type."""
        return f"<div>{self.data.get('content', '')}</div>"

TextPlugin = JSONPluginBase.proxy(
    "text",
    verbose_name="Text Block",
    schema={
        "type": "object",
        "properties": {
            "content": {"type": "string", "format": "prose"},
        },
    },
    mixins=[RenderMixin],
)
```

**Why mixins instead of subclassing?** Proxy plugins created with `.proxy()` are automatically registered in an internal map. This registration enables the QuerySet's `.downcast()` method to return the correct proxy class for each plugin type. If you were to subclass the returned proxy further, those subclasses wouldn't be registered, and `.downcast()` would return the base proxy instead of your extended version.

The `mixins` parameter accepts a list or tuple of mixin classes that will be added to the proxy's method resolution order (MRO), allowing you to:
- Add custom methods and properties
- Override base class behavior
- Share functionality across multiple plugin types

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
