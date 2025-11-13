from functools import partial

import jmespath
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models
from django.db.models import Q, signals
from django.utils.translation import gettext as _

from django_json_schema_editor.forms import JSONEditorField


def _register_reference(jsonmodel, to, *, name, getter, field=None):
    class Meta:
        verbose_name = f"{jsonmodel.__name__} ⇒ {to.__name__} reference"

    ns = {
        "__module__": jsonmodel.__module__,
        "parent": models.ForeignKey(
            jsonmodel, on_delete=models.CASCADE, related_name="+"
        ),
        "object": models.ForeignKey(to, on_delete=models.PROTECT, related_name="+"),
        "Meta": Meta,
        "__str__": lambda obj: str(obj.parent),
    }

    reference = type(
        f"{jsonmodel._meta.model_name}_{to._meta.label_lower.replace('.', '_')}_ref",
        (models.Model,),
        ns,
    )

    def listener(sender, instance, **kwargs):
        if not isinstance(instance, jsonmodel):
            return

        if (data := getter(instance)) is None or not isinstance(data, list):
            return

        pks = [pk for pk in data if pk]
        valid_pks = []
        for pk in pks:
            try:
                reference.objects.update_or_create(parent=instance, object_id=pk)
                valid_pks.append(pk)
            except (ValueError, TypeError, IntegrityError):
                # Skip primary keys that can't be processed by the database
                pass

        # Only try to delete references for valid PKs to avoid database errors
        q = Q(parent=instance)
        if valid_pks:
            q &= ~Q(object_id__in=valid_pks)
        reference.objects.filter(q).delete()

    # This doesn't work because we're using proxy models:
    # signals.post_save.connect(listener, sender=jsonmodel, weak=False)
    signals.post_save.connect(listener, weak=False)

    models.ManyToManyField(to, editable=False, through=reference).contribute_to_class(
        jsonmodel, name
    )

    def validate(instance):
        if (data := getter(instance)) is None or not isinstance(data, list):
            return

        pks = []
        invalid = []

        for pk in data:
            # Primary key is unset (falsy), this is fine
            if not pk:
                continue

            # Primary key is not convertible to its Python equivalent
            try:
                pks.append(to._meta.pk.to_python(pk))
            except Exception:
                invalid.append(pk)

        if not invalid and pks:
            objects = to._base_manager.filter(pk__in=pks)
            if len(objects) != len(pks):
                found = {obj.pk for obj in objects}
                invalid = [pk for pk in pks if pk not in found]

        if invalid:
            raise ValidationError(
                _("Some of the references are invalid: {}").format(
                    ", ".join(map(str, invalid))
                )
            )

    field._reference_validators.append(validate)


class JSONField(models.JSONField):
    def __init__(self, *args, **kwargs):
        self._config = kwargs.pop("config", None)
        self._schema = kwargs.pop("schema", None)
        self._foreign_key_descriptions = kwargs.pop("foreign_key_descriptions", [])
        self._reference_validators = []
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, "django.db.models.JSONField", args, kwargs

    def formfield(self, **kwargs):
        kwargs.setdefault(
            "form_class",
            partial(
                JSONEditorField,
                config=self._config,
                schema=self._schema,
                foreign_key_descriptions=self._foreign_key_descriptions,
            ),
        )
        return super().formfield(**kwargs)

    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        setattr(
            cls,
            f"register_{name}_reference",
            partial(_register_reference, cls, field=self),
        )

    def validate(self, value, model_instance):
        super().validate(value, model_instance)
        for validator in self._reference_validators:
            validator(model_instance)


def flatten(lst):
    """
    Recursively flatten a list of values and nested lists
    """
    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result


def paths_to_pks(data, *, to, paths):
    """
    Converts a list of JMES paths to a list of primary key values

    Arguments:

    - ``to``: The Django model instance or class, used to access the primary
      key field's ``to_python`` method
    - ``data``: The data dictionary
    - ``paths``: A list of JMES paths

    The returned array is automatically flattened.
    """
    pk = to._meta.pk
    return [
        pk.to_python(value)
        for value in flatten([jmespath.search(path, data) for path in paths])
        if value
    ]
