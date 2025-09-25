from functools import partial

from content_editor.admin import ContentEditorInline
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models.query import ModelIterable
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

from django_json_schema_editor.fields import JSONField
from django_json_schema_editor.forms import JSONEditorField


try:
    import jsonpointer
except ImportError:
    jsonpointer = None


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
        pointer_value = None
        schema = getattr(self, "SCHEMA", {})
        if jsonpointer and schema and (pointer := schema.get("__str__")):
            try:
                pointer_value = jsonpointer.resolve_pointer(self.data, pointer)
            except Exception:
                pass

        if pointer_value:
            return pointer_value
        if title := schema.get("title"):
            return title

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
    def proxy(cls, type_name, *, schema, **meta):
        meta["proxy"] = True
        meta["app_label"] = cls._meta.app_label
        meta.setdefault("verbose_name", type_name)

        meta_class = type("Meta", (cls.Meta,), meta)

        if not hasattr(cls, "_proxy_types_map"):
            cls._proxy_types_map = {}

        if type_name in cls._proxy_types_map:
            raise ImproperlyConfigured(
                f"The proxy type {type_name!r} has already been registered on {cls!r}."
            )

        new_type = type(
            f"{cls.__qualname__}_{type_name}",
            (cls,),
            {
                "__module__": cls.__module__,
                "Meta": meta_class,
                "TYPE": type_name,
                "SCHEMA": schema,
            },
        )
        cls._proxy_types_map[type_name] = new_type
        return new_type


class JSONPluginInline(ContentEditorInline):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(type=self.model.TYPE)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "data":
            kwargs["form_class"] = partial(
                JSONEditorField,
                schema=self.model.SCHEMA,
                foreign_key_descriptions=getattr(self, "foreign_key_descriptions", []),
            )
        return super().formfield_for_dbfield(db_field, request, **kwargs)
