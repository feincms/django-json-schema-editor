from django.db import models

from django_json_schema_editor.fields import JSONField


def itemgetter(key):
    return lambda value: value.get(key)


class File(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "file"

    def __str__(self):
        return self.name


class Thing(models.Model):
    data = JSONField(
        schema={
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "stuff": {"type": "string", "pattern": "^[A-Z]*$"},
                "prose": {"type": "string", "format": "prose"},
                "file": {
                    "type": "string",
                    "format": "foreign_key",
                    "options": {
                        "url": "/admin/testapp/file/?_popup=1&_to_field=id",
                        "model": "testapp.file",
                    },
                },
            },
        },
        foreign_key_descriptions=[("testapp.file", itemgetter("files"))],
    )

    def __str__(self):
        return ""


def get_file_ids(plugin):
    file = plugin.data.get("file")
    if file:
        return [file]
    return []


Thing.register_data_reference(
    File,
    name="files",
    getter=get_file_ids,
)
