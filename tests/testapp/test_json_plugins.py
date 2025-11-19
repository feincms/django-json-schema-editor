"""Tests for JSON path support in JSONPluginBase."""

from unittest.mock import MagicMock, patch

import pytest
from django.utils.translation import gettext_lazy as _
from playwright.sync_api import expect

from django_json_schema_editor.plugins import JSONPluginBase
from testapp import models
from testapp.test_json_editor import login_admin


class _TestPlugin(JSONPluginBase):
    """Test plugin class for JSON path testing."""

    SCHEMA = {
        "type": "object",
        "title": "Test Plugin",
        "__str__": "title",
        "properties": {
            "title": {"type": "string"},
            "content": {"type": "string"},
        },
    }

    class Meta:
        app_label = "testapp"


class _TestPluginWithoutPath(JSONPluginBase):
    """Test plugin without JSON path but with title."""

    SCHEMA = {
        "type": "object",
        "title": _("Simple Plugin"),
        "properties": {
            "content": {"type": "string"},
        },
    }

    class Meta:
        app_label = "testapp"


class _TestPluginMinimal(JSONPluginBase):
    """Test plugin with minimal schema."""

    SCHEMA = {}

    class Meta:
        app_label = "testapp"


@pytest.mark.django_db
class TestJSONPathSupport:
    """Test JSON path functionality in JSONPluginBase.__str__."""

    def test_str_with_json_path_success(self):
        """Test __str__ method with successful JSON path resolution."""
        plugin = _TestPlugin()
        plugin.data = {"title": "My Title", "content": "Some content"}

        result = str(plugin)

        assert result == "My Title"

    def test_str_with_json_path_exception(self):
        """Test __str__ method when JSON path resolution fails."""
        plugin = _TestPlugin()
        plugin.data = {"content": "Some content"}  # missing "title"
        plugin.type = "test_plugin"

        result = str(plugin)

        # Should fall back to schema title since JSON path fails
        assert result == "Test Plugin"

    def test_str_without_jmespath_module(self):
        """Test __str__ method when jmespath module is not available."""
        with patch("django_json_schema_editor.plugins.jmespath", None):
            plugin = _TestPlugin()
            plugin.data = {"title": "My Title"}
            plugin.type = "test_plugin"

            result = str(plugin)

            # Should fall back to schema title since jsonpath is None
            assert result == "Test Plugin"

    def test_str_with_empty_path_result(self):
        """Test __str__ method when JSON path returns empty string."""
        plugin = _TestPlugin()
        plugin.data = {"title": "", "content": "Some content"}
        plugin.type = "test_plugin"

        result = str(plugin)

        # Should fall back to schema title when path result is empty
        assert result == "Test Plugin"

    def test_str_with_none_path_result(self):
        """Test __str__ method when JSON path returns None."""
        plugin = _TestPlugin()
        plugin.data = {"title": None, "content": "Some content"}
        plugin.type = "test_plugin"

        result = str(plugin)

        # Should fall back to schema title when path result is None
        assert result == "Test Plugin"

    def test_str_fallback_to_schema_title(self):
        """Test __str__ method fallback to schema title."""
        with patch("django_json_schema_editor.plugins.jmespath", None):
            plugin = _TestPluginWithoutPath()
            plugin.data = {"content": "Some content"}
            plugin.type = "simple_plugin"

            result = str(plugin)

            assert result == "Simple Plugin"

    def test_str_minimal_schema_fallback(self):
        """Test __str__ method with minimal schema falls back to type."""
        with patch("django_json_schema_editor.plugins.jmespath", None):
            plugin = _TestPluginMinimal()
            plugin.data = {"content": "Some content"}
            plugin.type = "minimal_plugin"
            plugin._proxy_types_map = {}  # Empty proxy types map

            # Mock parent object
            mock_parent = MagicMock()
            mock_parent._meta.verbose_name = "Parent Object"
            mock_parent.__str__.return_value = "Parent Instance"
            plugin.parent = mock_parent

            result = str(plugin)

            assert result == 'Minimal_plugin on Parent Object "Parent Instance"'

    def test_str_with_proxy_type_fallback(self):
        """Test __str__ method fallback to proxy type verbose name."""

        # Mock proxy type with verbose name
        class MockProxyType:
            class _meta:
                verbose_name = "Mock Proxy Type"

        # Create plugin with no schema title to force proxy type fallback
        plugin = _TestPluginMinimal()  # This has empty schema
        plugin.data = {}
        plugin.type = "test_plugin"
        plugin._proxy_types_map = {"test_plugin": MockProxyType}

        # Mock parent object
        mock_parent = MagicMock()
        mock_parent._meta.verbose_name = "Parent Object"
        mock_parent.__str__.return_value = "Parent Instance"
        plugin.parent = mock_parent

        result = str(plugin)

        assert result == 'Mock Proxy Type on Parent Object "Parent Instance"'

    def test_str_with_valid_path_value_overrides_title(self):
        """Test that valid JSON path value takes precedence over schema title."""
        plugin = _TestPlugin()
        plugin.data = {"title": "Path Value"}

        result = str(plugin)

        # Should use path value, not schema title
        assert result == "Path Value"
        assert result != "Test Plugin"  # Should not fall back to schema title

    def test_str_no_schema_attribute(self):
        """Test __str__ method when SCHEMA attribute is missing."""

        class PluginNoSchema(JSONPluginBase):
            class Meta:
                app_label = "testapp"

        plugin = PluginNoSchema()
        plugin.data = {"content": "test"}
        plugin.type = "no_schema_plugin"
        plugin._proxy_types_map = {}

        # Mock parent object
        mock_parent = MagicMock()
        mock_parent._meta.verbose_name = "Parent Object"
        mock_parent.__str__.return_value = "Parent Instance"
        plugin.parent = mock_parent

        result = str(plugin)

        # Should fall back to type name with parent info
        assert result == 'No_schema_plugin on Parent Object "Parent Instance"'


@pytest.mark.django_db
def test_json_plugin_models():
    article = models.Article.objects.create()
    models.Text.objects.create(
        parent=article, region="main", ordering=10, data={"text": "Hello World"}
    )
    models.Download.objects.create(
        parent=article,
        region="main",
        ordering=20,
        data={"file": models.File.objects.create(name="test.png").pk},
    )

    plugins = list(models.JSONPlugin.get_queryset())

    assert isinstance(plugins[0], models.Text)
    assert isinstance(plugins[1], models.Download)


@pytest.mark.django_db
@pytest.mark.e2e
def test_json_plugin_admin(page, live_server):
    """Test that the JSON editor is loaded in the admin form."""
    login_admin(page, live_server)

    article = models.Article.objects.create()
    models.Text.objects.create(
        parent=article, region="main", ordering=10, data={"text": "Hello World"}
    )
    models.Download.objects.create(
        parent=article,
        region="main",
        ordering=20,
        data={"file": models.File.objects.create(name="test.png").pk},
    )

    page.goto(f"{live_server.url}/admin/testapp/article/{article.pk}/change/")

    # Check that the editor is loaded
    # editor_container = page.locator(".django_json_schema_editor")
    # Fails because locator doesn't like matching multiple elements
    # expect(editor_container).to_be_visible()

    raw_id_field_label = page.locator(".django_json_schema_editor .form-control strong")
    expect(raw_id_field_label).to_contain_text("test.png")


@pytest.mark.django_db
def test_proxy_with_single_mixin():
    """Test that proxy accepts a single mixin class."""

    class CustomMixin:
        def custom_method(self):
            return "custom_value"

    ProxyPlugin = models.JSONPlugin.proxy(
        "test_single_mixin",
        schema={"type": "object"},
        mixins=[CustomMixin],
    )

    # Verify mixin is in MRO
    assert CustomMixin in ProxyPlugin.__mro__

    # Create an article and plugin instance
    article = models.Article.objects.create()
    plugin = ProxyPlugin.objects.create(
        parent=article, region="main", ordering=10, data={}
    )

    # Verify mixin method is accessible
    assert plugin.custom_method() == "custom_value"


@pytest.mark.django_db
def test_proxy_with_multiple_mixins():
    """Test that proxy accepts multiple mixin classes."""

    class MixinA:
        def method_a(self):
            return "a"

    class MixinB:
        def method_b(self):
            return "b"

    ProxyPlugin = models.JSONPlugin.proxy(
        "test_multiple_mixins",
        schema={"type": "object"},
        mixins=[MixinA, MixinB],
    )

    # Verify both mixins are in MRO
    assert MixinA in ProxyPlugin.__mro__
    assert MixinB in ProxyPlugin.__mro__

    # Create an article and plugin instance
    article = models.Article.objects.create()
    plugin = ProxyPlugin.objects.create(
        parent=article, region="main", ordering=10, data={}
    )

    # Verify both mixin methods are accessible
    assert plugin.method_a() == "a"
    assert plugin.method_b() == "b"


@pytest.mark.django_db
def test_proxy_mixin_method_resolution_order():
    """Test that mixin MRO follows Python's standard resolution order."""

    class MixinA:
        def shared_method(self):
            return "from_a"

    class MixinB:
        def shared_method(self):
            return "from_b"

    ProxyPlugin = models.JSONPlugin.proxy(
        "test_mro",
        schema={"type": "object"},
        mixins=[MixinA, MixinB],
    )

    # Create an article and plugin instance
    article = models.Article.objects.create()
    plugin = ProxyPlugin.objects.create(
        parent=article, region="main", ordering=10, data={}
    )

    # First mixin should take precedence
    assert plugin.shared_method() == "from_a"


@pytest.mark.django_db
def test_proxy_without_mixins_default():
    """Test that proxy works without mixins parameter (default empty tuple)."""
    ProxyPlugin = models.JSONPlugin.proxy(
        "test_no_mixins",
        schema={"type": "object"},
    )

    # Create an article and plugin instance
    article = models.Article.objects.create()
    plugin = ProxyPlugin.objects.create(
        parent=article, region="main", ordering=10, data={}
    )

    # Should work normally without mixins
    assert plugin.type == "test_no_mixins"


@pytest.mark.django_db
def test_proxy_with_meta_parameter():
    """Test that meta parameter adds to Meta class."""
    ProxyPlugin = models.JSONPlugin.proxy(
        "test_meta",
        schema={"type": "object"},
        meta={"ordering": ["-id"]},
    )

    # Verify meta attribute is set
    assert ProxyPlugin._meta.ordering == ["-id"]


@pytest.mark.django_db
def test_proxy_mixin_with_properties():
    """Test that mixin can add properties to proxy class."""

    class PropertyMixin:
        @property
        def computed_value(self):
            return f"computed_{self.type}"

    ProxyPlugin = models.JSONPlugin.proxy(
        "test_property",
        schema={"type": "object"},
        mixins=[PropertyMixin],
    )

    # Create an article and plugin instance
    article = models.Article.objects.create()
    plugin = ProxyPlugin.objects.create(
        parent=article, region="main", ordering=10, data={}
    )

    assert plugin.computed_value == "computed_test_property"


@pytest.mark.django_db
def test_proxy_mixin_access_to_schema_and_type():
    """Test that mixin can access TYPE and SCHEMA class attributes."""

    class AccessMixin:
        def get_schema_title(self):
            return self.SCHEMA.get("title", "No title")

        def get_type_name(self):
            return self.TYPE

    ProxyPlugin = models.JSONPlugin.proxy(
        "test_access",
        schema={"type": "object", "title": "Test Schema"},
        mixins=[AccessMixin],
    )

    # Create an article and plugin instance
    article = models.Article.objects.create()
    plugin = ProxyPlugin.objects.create(
        parent=article, region="main", ordering=10, data={}
    )

    assert plugin.get_schema_title() == "Test Schema"
    assert plugin.get_type_name() == "test_access"
