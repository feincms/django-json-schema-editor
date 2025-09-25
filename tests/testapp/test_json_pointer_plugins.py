"""Tests for JSON pointer support in JSONPluginBase."""

# Mock content_editor to avoid dependency issues
import sys
from unittest.mock import MagicMock, patch

import pytest


content_editor_mock = MagicMock()
content_editor_mock.admin.ContentEditorInline = MagicMock()
sys.modules["content_editor"] = content_editor_mock
sys.modules["content_editor.admin"] = content_editor_mock.admin

from django_json_schema_editor.plugins import JSONPluginBase  # noqa: E402


class _TestPlugin(JSONPluginBase):
    """Test plugin class for JSON pointer testing."""

    SCHEMA = {
        "type": "object",
        "title": "Test Plugin",
        "__str__": "/title",
        "properties": {
            "title": {"type": "string"},
            "content": {"type": "string"},
        },
    }

    class Meta:
        app_label = "testapp"


class _TestPluginWithoutPointer(JSONPluginBase):
    """Test plugin without JSON pointer but with title."""

    SCHEMA = {
        "type": "object",
        "title": "Simple Plugin",
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
class TestJSONPointerSupport:
    """Test JSON pointer functionality in JSONPluginBase.__str__."""

    def test_str_with_json_pointer_success(self):
        """Test __str__ method with successful JSON pointer resolution."""
        plugin = _TestPlugin()
        plugin.data = {"title": "My Title", "content": "Some content"}

        result = str(plugin)

        assert result == "My Title"

    def test_str_with_json_pointer_exception(self):
        """Test __str__ method when JSON pointer resolution fails."""
        plugin = _TestPlugin()
        plugin.data = {"content": "Some content"}  # missing "title"
        plugin.type = "test_plugin"

        result = str(plugin)

        # Should fall back to schema title since JSON pointer fails
        assert result == "Test Plugin"

    def test_str_without_jsonpointer_module(self):
        """Test __str__ method when jsonpointer module is not available."""
        with patch("django_json_schema_editor.plugins.jsonpointer", None):
            plugin = _TestPlugin()
            plugin.data = {"title": "My Title"}
            plugin.type = "test_plugin"

            result = str(plugin)

            # Should fall back to schema title since jsonpointer is None
            assert result == "Test Plugin"

    def test_str_with_empty_pointer_result(self):
        """Test __str__ method when JSON pointer returns empty string."""
        plugin = _TestPlugin()
        plugin.data = {"title": "", "content": "Some content"}
        plugin.type = "test_plugin"

        result = str(plugin)

        # Should fall back to schema title when pointer result is empty
        assert result == "Test Plugin"

    def test_str_with_none_pointer_result(self):
        """Test __str__ method when JSON pointer returns None."""
        plugin = _TestPlugin()
        plugin.data = {"title": None, "content": "Some content"}
        plugin.type = "test_plugin"

        result = str(plugin)

        # Should fall back to schema title when pointer result is None
        assert result == "Test Plugin"

    def test_str_fallback_to_schema_title(self):
        """Test __str__ method fallback to schema title."""
        with patch("django_json_schema_editor.plugins.jsonpointer", None):
            plugin = _TestPluginWithoutPointer()
            plugin.data = {"content": "Some content"}
            plugin.type = "simple_plugin"

            result = str(plugin)

            assert result == "Simple Plugin"

    def test_str_minimal_schema_fallback(self):
        """Test __str__ method with minimal schema falls back to type."""
        with patch("django_json_schema_editor.plugins.jsonpointer", None):
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

    def test_str_with_valid_pointer_value_overrides_title(self):
        """Test that valid JSON pointer value takes precedence over schema title."""
        plugin = _TestPlugin()
        plugin.data = {"title": "Pointer Value"}

        result = str(plugin)

        # Should use pointer value, not schema title
        assert result == "Pointer Value"
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
