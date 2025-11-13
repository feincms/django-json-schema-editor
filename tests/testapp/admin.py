from content_editor.admin import ContentEditor
from django.contrib import admin

from django_json_schema_editor.fields import paths_to_pks
from django_json_schema_editor.plugins import JSONPluginInline
from testapp import models


@admin.register(models.File)
class FileAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Thing)
class ThingAdmin(admin.ModelAdmin):
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "data":
            kwargs["foreign_key_descriptions"] = [
                (
                    "testapp.file",
                    lambda data: paths_to_pks(
                        data,
                        to=models.File,
                        paths=["file"],
                    ),
                ),
            ]
        return super().formfield_for_dbfield(db_field, request, **kwargs)


@admin.register(models.Article)
class ArticleAdmin(ContentEditor):
    inlines = [
        JSONPluginInline.create(models.Text),
        JSONPluginInline.create(models.Download),
    ]
