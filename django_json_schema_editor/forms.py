import json
import warnings
from copy import deepcopy

import fastjsonschema
from django import forms
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.text import Truncator
from django.utils.translation import get_language
from js_asset import JS, importmap


# Optional import for prose editor support. The import has the side effect of
# updating the importmap with the necessary entries our prose editor plugin
# needs.
try:
    import django_prose_editor.widgets  # noqa: F401
except ImportError:
    pass  # Prose editor functionality will be gracefully unavailable


DEFAULT_CONFIG = getattr(
    settings,
    "JSONEDITORWIDGET_DEFAULT_CONFIG",
    {
        # "disable_properties": True,
        "disable_collapse": True,
        # "disable_edit_json": True,
        "display_required_only": False,
        "theme": "django",
        "iconlib": "django",
    },
)


class JSONEditorField(forms.JSONField):
    def __init__(self, *args, **kwargs):
        self._config = kwargs.pop("config", {})
        self._schema = kwargs.pop("schema")
        self._foreign_key_descriptions = kwargs.pop("foreign_key_descriptions", [])
        kwargs["widget"] = JSONEditorWidget
        super().__init__(*args, **kwargs)
        if self._config:
            self.widget.editor_config.update(self._config)
        if self._schema:
            self.widget.editor_config["schema"] = self._schema
        self.widget.foreign_key_descriptions = self._foreign_key_descriptions

    def clean(self, value):
        value = super().clean(value)
        if schema := self._schema:
            try:
                fastjsonschema.validate(schema, value, use_formats=False)
            except fastjsonschema.JsonSchemaValueException as ex:
                raise ValidationError(ex.message) from ex
        else:
            warnings.warn(
                "Skipping JSON validation because there's no schema.",
                RuntimeWarning,
                stacklevel=1,
            )
        return value


def resolve_foreign_key_descriptions(model, pks):
    pks = [pk for pk in pks if pk] if pks else ()
    try:
        return (
            {
                f"{model._meta.label_lower}:{obj.pk}": Truncator(obj).words(5)
                for obj in model._default_manager.filter(pk__in=pks)
            }
            if pks
            else {}
        )
    except (ValueError, TypeError):
        # This can happen when the list of primary keys contains values which
        # are not parseable as primary keys.
        return {}


class JSONEditorWidget(forms.Textarea):
    template_name = "django_json_schema_editor/widget.html"
    supported_translations = {"de"}

    def __init__(self, *args, editor_config=None, **kwargs):
        self.editor_config = deepcopy(DEFAULT_CONFIG)
        if editor_config:
            self.editor_config.update(editor_config)
        super().__init__(*args, **kwargs)

    def get_context(self, *args, **kwargs):
        context = super().get_context(*args, **kwargs)
        context["editor_config"] = json.dumps(self.editor_config, cls=DjangoJSONEncoder)

        if (fkd := getattr(self, "foreign_key_descriptions", None)) and (
            value := json.loads(context["widget"]["value"])
        ):
            fk = {}
            for model, getter in fkd:
                fk |= resolve_foreign_key_descriptions(
                    apps.get_model(model), getter(value)
                )
            context["foreign_key"] = json.dumps(fk)
        return context

    @property
    def media(self):
        css = {
            "screen": [
                "django_json_schema_editor/vendor/material-icons.css",
                "django_json_schema_editor/django_theme.css",
            ],
        }
        js = [
            importmap,
            "django_json_schema_editor/vendor/jsoneditor.js",
            "django_json_schema_editor/django_theme.js",
            "django_json_schema_editor/foreign_key.js",
            "django_json_schema_editor/widget.js",
            JS("django_json_schema_editor/prose_editor.js", {"type": "module"}),
        ]
        language = get_language()
        if language in self.supported_translations:
            js.append(f"django_json_schema_editor/language_{language}.js")
        return forms.Media(css=css, js=js)
