import json
import os

import pytest
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from playwright.sync_api import expect

from django_json_schema_editor.forms import resolve_foreign_key_descriptions
from testapp.models import File, Thing


# Set Django async unsafe to allow database operations in tests
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


def login_admin(page, live_server):
    """Helper function to login as admin."""
    # Delete any existing superusers with the same username to avoid conflicts
    User.objects.filter(username="admin").delete()

    User.objects.create_superuser("admin", "admin@example.com", "password")
    page.goto(f"{live_server.url}/admin/login/")
    page.fill("#id_username", "admin")
    page.fill("#id_password", "password")
    page.click("input[type=submit]")
    page.wait_for_url(f"{live_server.url}/admin/")


@pytest.mark.django_db
@pytest.mark.e2e
def test_json_editor_admin_form(page, live_server):
    """Test that the JSON editor is loaded in the admin form."""
    login_admin(page, live_server)

    # Go to the add page
    page.goto(f"{live_server.url}/admin/testapp/thing/add/")

    # Check that the prose editor is loaded
    editor_container = page.locator(".django_json_schema_editor")
    expect(editor_container).to_be_visible()


@pytest.mark.django_db
@pytest.mark.e2e
def test_json_editor_prose(page, live_server):
    """Test that prose editor loads and displays content correctly."""
    login_admin(page, live_server)

    thing = Thing.objects.create(
        data={
            "text": "Hello World",
            "prose": "<strong>Prose</strong> is <em>fine</em>",
        }
    )

    # Go to the change page
    page.goto(f"{live_server.url}/admin/testapp/thing/{thing.pk}/change/")

    # Check that the prose editor is loaded
    editor_container = page.locator(".django_json_schema_editor")
    expect(editor_container).to_be_visible()

    # Check that the prose editor contains the expected content
    prose_container = page.locator(".prose-editor")
    expect(prose_container).to_be_visible()

    # Wait for the editor to fully initialize
    page.wait_for_timeout(1000)

    # Verify the hidden textarea with our JSON data
    textarea = page.locator("textarea#id_data")
    # The textarea is hidden, so we don't check visibility
    textarea_value = textarea.input_value()
    textarea_json = page.evaluate("value => JSON.parse(value)", textarea_value)
    assert textarea_json["text"] == "Hello World"
    assert textarea_json["prose"] == "<strong>Prose</strong> is <em>fine</em>"

    # Find the JSON editor object container
    editor_container = page.locator(".je-object__container")
    expect(editor_container).to_be_visible()

    # Check for the text field using the exact ID from the HTML
    text_input = page.locator('input[id*="[text]"]')
    expect(text_input).to_be_visible()
    expect(text_input).to_have_value("Hello World")

    # Check for the prose content using the exact selector from the HTML
    prose_editor = page.locator(".prose-editor .ProseMirror")
    expect(prose_editor).to_be_visible()

    # Check if the prose editor contains our expected text
    expect(prose_editor).to_contain_text("Prose is fine")

    # Verify the HTML content
    prose_html = prose_editor.inner_html()
    assert "<strong>Prose</strong>" in prose_html
    assert "<em>fine</em>" in prose_html


@pytest.mark.django_db
@pytest.mark.e2e
def test_json_editor_edit_save(page, live_server):
    """Test editing and saving content in the JSON editor."""
    login_admin(page, live_server)

    thing = Thing.objects.create(
        data={
            "text": "Original text",
            "prose": "Original prose",
        }
    )

    # Go to the change page
    page.goto(f"{live_server.url}/admin/testapp/thing/{thing.pk}/change/")
    page.wait_for_timeout(1000)  # Wait for editor to initialize

    # Edit the regular text field
    text_input = page.locator('input[id*="[text]"]')
    expect(text_input).to_be_visible()
    text_input.fill("Updated text")

    # Edit the prose field - focus on the element first
    prose_editor = page.locator(".prose-editor .ProseMirror")
    expect(prose_editor).to_be_visible()
    prose_editor.click()

    # Clear the content and type new content
    page.keyboard.press("Control+A")
    page.keyboard.press("Delete")
    page.keyboard.type("New prose content")

    # Submit the form to save changes
    page.click('input[name="_save"]')

    # Navigate back to the object to verify the changes were saved
    page.goto(f"{live_server.url}/admin/testapp/thing/{thing.pk}/change/")
    page.wait_for_timeout(1000)

    # Verify text field was updated
    text_input = page.locator('input[id*="[text]"]')
    expect(text_input).to_have_value("Updated text")

    # Verify prose field was updated
    prose_editor = page.locator(".prose-editor .ProseMirror")
    expect(prose_editor).to_contain_text("New prose content")

    # Verify the underlying JSON data
    textarea = page.locator("textarea#id_data")
    textarea_value = textarea.input_value()
    textarea_json = page.evaluate("value => JSON.parse(value)", textarea_value)
    assert textarea_json["text"] == "Updated text"
    assert "New prose content" in textarea_json["prose"]


@pytest.mark.django_db
@pytest.mark.e2e
def test_json_editor_display(page, live_server):
    """Test that the JSON schema editor correctly displays data."""
    login_admin(page, live_server)

    # Create a test object directly via Django model
    test_data = {"text": "Test text field", "prose": "<p>Test prose content</p>"}
    Thing.objects.create(data=test_data)

    # Go directly to the edit page for the first Thing object
    thing = Thing.objects.first()
    page.goto(f"{live_server.url}/admin/testapp/thing/{thing.pk}/change/")

    # Wait for editor to initialize
    page.wait_for_timeout(1000)

    # Verify that text field displays our test data
    text_input = page.locator('input[id*="[text]"]')
    expect(text_input).to_be_visible()
    expect(text_input).to_have_value("Test text field")

    # Verify that prose field contains our test content
    prose_editor = page.locator(".prose-editor .ProseMirror")
    expect(prose_editor).to_be_visible()
    expect(prose_editor).to_contain_text("Test prose content")


@pytest.mark.django_db
@pytest.mark.e2e
def test_json_editor_ui_elements(page, live_server):
    """Test UI elements of the JSON editor like toolbar buttons."""
    login_admin(page, live_server)

    # Go to the add page
    page.goto(f"{live_server.url}/admin/testapp/thing/add/")
    page.wait_for_timeout(1000)  # Wait for editor to initialize

    # Verify the editor has loaded and the UI elements are present

    # Prose editor toolbar should be visible
    toolbar = page.locator(".prose-menubar")
    expect(toolbar).to_be_visible()

    # Check that formatting buttons exist and are visible
    expect(page.locator(".prose-menubar__button[title='bold']")).to_be_visible()
    expect(page.locator(".prose-menubar__button[title='italic']")).to_be_visible()
    expect(page.locator(".prose-menubar__button[title='underline']")).to_be_visible()

    # Verify the text editor field is present
    text_input = page.locator('input[id*="[text]"]')
    expect(text_input).to_be_visible()

    # Focus on the prose editor
    prose_editor = page.locator(".prose-editor .ProseMirror")
    expect(prose_editor).to_be_visible()
    prose_editor.click()

    # Type some text
    page.keyboard.type("Testing formatting")

    # Select the text
    page.keyboard.press("Control+A")

    # Click the bold button in the prose editor toolbar
    bold_button = page.locator(".prose-menubar__button[title='bold']")
    bold_button.click()

    # Verify the text is now bold (check in the DOM)
    prose_html = prose_editor.inner_html()
    assert "<strong>Testing formatting</strong>" in prose_html


@pytest.mark.django_db
def test_data_references():
    """Test that references to files are protected from deletion."""
    # Create test files
    files = [File.objects.create(name=f"file-{i}.png") for i in range(1, 5)]

    # Create a Thing object with a reference to the first file
    thing = Thing.objects.create(
        data={
            "text": "Test with file reference",
            "prose": "This references a file",
            "file": str(files[0].pk),
        }
    )

    # Verify the reference is stored correctly
    assert thing.data["file"] == str(files[0].pk)

    # Verify the file is protected from deletion
    with pytest.raises(ProtectedError):
        files[0].delete()

    # Verify other files (not referenced) can be deleted
    files[1].delete()
    assert File.objects.count() == 3

    # Modify the Thing to reference a different file
    thing.data["file"] = str(files[2].pk)
    thing.save()

    # Now the first file should be deletable, but the third should be protected
    files[0].delete()
    assert File.objects.count() == 2

    with pytest.raises(ProtectedError):
        files[2].delete()


@pytest.mark.django_db
@pytest.mark.e2e
def test_foreign_key_selector(page, live_server):
    """Test that the foreign key selector works properly in the UI."""
    login_admin(page, live_server)

    # Create some files for selection
    files = [File.objects.create(name=f"test-file-{i}") for i in range(1, 4)]

    # Go to the add page for a Thing
    page.goto(f"{live_server.url}/admin/testapp/thing/add/")
    page.wait_for_timeout(1000)  # Wait for the editor to initialize

    # Verify the foreign key field label is visible
    file_label = page.locator('label.je-form-input-label:has-text("file")')
    expect(file_label).to_be_visible()

    # Locate the foreign key input field
    foreign_key_input = page.locator(".vForeignKeyRawIdAdminField")
    expect(foreign_key_input).to_be_visible()

    # Lookup button should be visible
    lookup_button = page.locator("a.related-lookup")
    expect(lookup_button).to_be_visible()

    # Test with pre-populated data
    # Create a Thing with a file reference
    thing = Thing.objects.create(
        data={
            "text": "ForeignKey test",
            "prose": "Testing file reference",
            "file": str(files[0].pk),
        }
    )

    # Go to the edit page
    page.goto(f"{live_server.url}/admin/testapp/thing/{thing.pk}/change/")
    page.wait_for_timeout(1000)

    # Take a screenshot to debug the populated view
    screenshot_dir = "/tmp/playwright_screenshots"

    os.makedirs(screenshot_dir, exist_ok=True)
    page.screenshot(path=f"{screenshot_dir}/foreign_key_edit_test.png", full_page=True)

    # Verify the foreign key field label is visible
    file_label = page.locator('label.je-form-input-label:has-text("file")')
    expect(file_label).to_be_visible()

    # Now the input field should have a value
    foreign_key_input = page.locator(".vForeignKeyRawIdAdminField")
    expect(foreign_key_input).to_be_visible()
    expect(foreign_key_input).to_have_value(str(files[0].pk))

    # The related lookup link should still be visible
    lookup_button = page.locator("a.related-lookup")
    expect(lookup_button).to_be_visible()

    # There might be a strong element showing the file name, but it's not always visible
    # We've successfully verified the input field has the correct value

    # Save the form to check if the foreign key is properly stored
    page.click('input[name="_save"]')

    # Verify the data in the database
    thing.refresh_from_db()
    assert thing.data["file"] == str(files[0].pk)

    # We cannot test clicking the lookup button because it opens a popup window,
    # but we've verified the core UI elements are present and working correctly


@pytest.mark.django_db
def test_valid_foreign_key_references():
    """Test that valid foreign key references work correctly."""
    # Create test files
    file1 = File.objects.create(name="valid-file-1.txt")
    file2 = File.objects.create(name="valid-file-2.txt")

    # Test with valid single reference
    thing = Thing.objects.create(
        data={
            "text": "Valid reference test",
            "file": str(file1.pk),
        }
    )

    # Should not raise any validation errors
    thing.full_clean()

    # Test updating to another valid reference
    thing.data["file"] = str(file2.pk)
    thing.save()
    thing.full_clean()  # Should still be valid


@pytest.mark.django_db
def test_invalid_nonexistent_foreign_key_references():
    """Test that references to non-existent primary keys raise ValidationError."""
    # Create a file for context
    File.objects.create(name="existing-file.txt")

    # Test with non-existent primary key
    thing = Thing.objects.create(
        data={
            "text": "Invalid reference test",
            "file": "-1",  # Non-existent PK
        }
    )

    # Should raise ValidationError during full_clean
    with pytest.raises(ValidationError) as exc_info:
        thing.full_clean()

    error_message = str(exc_info.value)
    assert "Some of the references are invalid" in error_message
    assert "-1" in error_message

    thing.delete()


@pytest.mark.django_db
def test_invalid_unparseable_foreign_key_references():
    """Test that unparseable primary key values raise ValidationError."""
    # Create a file for context
    File.objects.create(name="existing-file.txt")

    # Test with unparseable primary key
    thing = Thing.objects.create(
        data={
            "text": "Unparseable reference test",
            "file": "asdf",  # Unparseable as integer PK
        }
    )

    # Should raise ValidationError during full_clean
    with pytest.raises(ValidationError) as exc_info:
        thing.full_clean()

    error_message = str(exc_info.value)
    assert "Some of the references are invalid" in error_message
    assert "asdf" in error_message

    thing.delete()


@pytest.mark.django_db
def test_empty_and_null_foreign_key_references():
    """Test that empty/null references are handled gracefully."""
    # Test with empty string
    thing1 = Thing.objects.create(
        data={
            "text": "Empty reference test",
            "file": "",  # Empty string should be fine
        }
    )

    # Should not raise any validation errors
    thing1.full_clean()

    # Test with null/None
    thing2 = Thing.objects.create(
        data={
            "text": "Null reference test",
            "file": None,  # None should be fine
        }
    )

    # Should not raise any validation errors
    thing2.full_clean()

    # Test with missing field entirely
    thing3 = Thing.objects.create(
        data={
            "text": "Missing field test",
            # No "file" field at all
        }
    )

    # Should not raise any validation errors
    thing3.full_clean()


@pytest.mark.django_db
def test_resolve_foreign_key_descriptions_error_handling():
    """Test that resolve_foreign_key_descriptions handles invalid PKs gracefully."""
    # Create a test file
    file1 = File.objects.create(name="test-file.txt")

    # Test with valid primary keys
    result = resolve_foreign_key_descriptions(File, [str(file1.pk)])
    assert f"testapp.file:{file1.pk}" in result
    assert result[f"testapp.file:{file1.pk}"] == "test-file.txt"

    # Test with mix of valid and invalid primary keys
    result = resolve_foreign_key_descriptions(File, [str(file1.pk), "asdf", "-1"])
    # Should return empty dict due to ValueError/TypeError in the mixed case
    assert result == {}

    # Test with only invalid primary keys
    result = resolve_foreign_key_descriptions(File, ["asdf", "xyz"])
    assert result == {}

    # Test with empty list
    result = resolve_foreign_key_descriptions(File, [])
    assert result == {}

    # Test with None
    result = resolve_foreign_key_descriptions(File, None)
    assert result == {}


@pytest.mark.django_db
def test_foreign_key_validation_with_string_pks():
    """Test validation works correctly with string primary keys."""
    # Note: File model uses integer PKs, but we test the conversion logic

    # Create files with known integer PKs
    file1 = File.objects.create(name="string-pk-test-1.txt")
    file2 = File.objects.create(name="string-pk-test-2.txt")

    # Test with string representations of valid integer PKs
    thing = Thing.objects.create(
        data={
            "text": "String PK test",
            "file": str(file1.pk),  # String representation of int PK
        }
    )

    # Should not raise validation errors
    thing.full_clean()

    # Test updating to different valid string PK
    thing.data["file"] = str(file2.pk)
    thing.save()
    thing.full_clean()


@pytest.mark.django_db
def test_foreign_key_validation_edge_cases():
    """Test edge cases in foreign key validation."""
    # Test with boolean False (falsy, should be treated as unset)
    thing1 = Thing.objects.create(
        data={
            "text": "Boolean False PK test",
            "file": False,  # Boolean False, falsy
        }
    )

    # Should NOT raise ValidationError since falsy values are treated as unset
    thing1.full_clean()  # Should pass without error

    # Test with integer 0 (also falsy, should be treated as unset)
    thing2 = Thing.objects.create(
        data={
            "text": "Integer zero PK test",
            "file": 0,  # Integer 0, falsy
        }
    )

    # Should NOT raise ValidationError since falsy values are treated as unset
    thing2.full_clean()  # Should pass without error

    # Test with boolean True (truthy, should be validated)
    thing3 = Thing(
        data={
            "text": "Boolean True PK test",
            "file": True,  # Boolean True, truthy but invalid
        }
    )

    # Should raise ValidationError (True is truthy but likely not a valid PK)
    with pytest.raises(ValidationError):
        thing3.full_clean()


@pytest.mark.django_db
def test_validation():
    class ThingForm(forms.ModelForm):
        class Meta:
            model = Thing
            fields = ["data"]

    form = ThingForm({"data": json.dumps({"stuff": "123"})})
    assert not form.is_valid()
    assert "data.stuff must match pattern" in str(form.errors)
