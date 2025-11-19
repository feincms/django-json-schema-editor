from functools import partial

import jmespath
from content_editor.admin import ContentEditorInline
from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models.query import ModelIterable
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

from django_json_schema_editor.fields import JSONField, paths_to_pks
from django_json_schema_editor.forms import JSONEditorField


class _JSONPluginModelIterable(ModelIterable):
    def __iter__(self):
        mapping = self.queryset.model._proxy_types_map
        for obj in super().__iter__():
            obj.__class__ = mapping[obj.type]
            yield obj


class _JSONPluginQuerySet(models.QuerySet):
    def downcast(self):
        obj = self._chain()
        obj._iterable_class = _JSONPluginModelIterable
        return obj


class JSONPluginBase(models.Model):
    type = models.CharField(_("type"), max_length=1000, editable=False)
    data = JSONField("", blank=True)

    objects = _JSONPluginQuerySet.as_manager()

    class Meta:
        abstract = True

    def __str__(self):
        path_value = None
        schema = getattr(self, "SCHEMA", {})
        if schema and (path := schema.get("__str__")):
            try:
                path_value = jmespath.search(path, self.data)
            except Exception:
                pass

        if path_value:
            return str(path_value)
        if title := schema.get("title"):
            return str(title)

        type = self.type
        if cls := self._proxy_types_map.get(self.type):
            type = cls._meta.verbose_name
        return f'{capfirst(type)} on {self.parent._meta.verbose_name} "{self.parent}"'

    def save(self, *args, **kwargs):
        self.type = self.TYPE
        super().save(*args, **kwargs)

    save.alters_data = True

    @classmethod
    def get_queryset(cls):
        return super().get_queryset().downcast()

    @classmethod
    def proxy(
        cls,
        type_name,
        *,
        schema,
        foreign_key_paths=None,
        verbose_name=None,
        meta=None,
        mixins=None,
    ):
        meta = {} if meta is None else meta
        meta["proxy"] = True
        meta["app_label"] = cls._meta.app_label
        meta.setdefault("verbose_name", verbose_name or type_name)

        meta_class = type("Meta", (cls.Meta,), meta)

        if not hasattr(cls, "_proxy_types_map"):
            cls._proxy_types_map = {}
            cls._proxy_types_foreign_key_paths = {}

        if type_name in cls._proxy_types_map:
            raise ImproperlyConfigured(
                f"The proxy type {type_name!r} has already been registered on {cls!r}."
            )

        # Convert mixins to tuple if provided as list
        mixins_tuple = tuple(mixins) if mixins else ()

        new_type = type(
            f"{cls.__qualname__}_{type_name}",
            (*mixins_tuple, cls),
            {
                "__module__": cls.__module__,
                "Meta": meta_class,
                "TYPE": type_name,
                "SCHEMA": schema,
            },
        )
        cls._proxy_types_map[type_name] = new_type
        cls._proxy_types_foreign_key_paths[type_name] = foreign_key_paths or {}
        return new_type

    @classmethod
    def register_foreign_key_reference(cls, model, *, name):
        def _getter(plugin):
            if (
                foreign_key_paths := cls._proxy_types_foreign_key_paths.get(plugin.type)
            ) and (paths := foreign_key_paths.get(model._meta.label_lower)):
                return paths_to_pks(
                    to=model,
                    paths=paths,
                    data=plugin.data,
                )
            return []

        cls.register_data_reference(model, name=name, getter=_getter)


class JSONPluginInline(ContentEditorInline):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(type=self.model.TYPE)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "data":
            foreign_key_descriptions = getattr(self, "foreign_key_descriptions", [])
            if not foreign_key_descriptions and (
                foreign_key_paths := self.model._proxy_types_foreign_key_paths.get(
                    self.model.TYPE
                )
            ):
                for model, paths in foreign_key_paths.items():
                    to = apps.get_model(model)
                    foreign_key_descriptions.append(
                        (
                            to._meta.label_lower,
                            partial(paths_to_pks, to=to, paths=paths),
                        )
                    )
            kwargs["form_class"] = partial(
                JSONEditorField,
                schema=self.model.SCHEMA,
                foreign_key_descriptions=foreign_key_descriptions,
            )
        return super().formfield_for_dbfield(db_field, request, **kwargs)
