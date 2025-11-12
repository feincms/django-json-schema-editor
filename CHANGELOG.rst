Change log
==========

Next version
~~~~~~~~~~~~

- **Backwards incompatible** The JSON pointer usage has been replaced by
  jmespath usage. ``__str__`` values in schemas for the ``JSONPluginBase``
  should be updated for the new syntax (for example, ``object.title`` instead
  of ``/object/title``), otherwise the code acts as if they weren't there.
  Failures are silent because crashes aren't worth it. Removed the
  ``jsonpointer`` extra and instead added a hard dependency on ``jmespath``.
- Be more careful in ``JSONPluginBase.__str__`` to actually return strings.
- Allowed forwarding more config options to the configurable prose editor, not
  just extensions.


0.8 (2025-09-25)
~~~~~~~~~~~~~~~~

- Fixed the initialization of the JSON editor when we start with null values.
- Changed the ID attributes of generated elements to hopefully be unique by
  using a unique ``form_name_root`` per editor instance.
- Added optional support for self-describing JSON plugins using JSON pointers.


0.7 (2025-09-05)
~~~~~~~~~~~~~~~~

- Reverted the ``required_by_default`` change, it was bad (tm) because it
  didn't allow removing existing properties at all. Better learn setting the
  ``required`` properties explicitly!


0.6 (2025-09-05)
~~~~~~~~~~~~~~~~

- Added validation for foreign key references to provide meaningful error
  messages instead of server crashes when invalid primary keys are entered.
- Fixed the error where edits could be lost by automatically dispatching
  ``change`` events when seeing ``input`` events to trigger the JSON editor's
  ``onChange`` updates.

0.5 (2025-06-26)
~~~~~~~~~~~~~~~~

- Fixed the size of checkboxes in the JSON editor.
- Added configurable extensions support for the prose editor, allowing
  customization of available formatting options.


0.4 (2025-03-24)
~~~~~~~~~~~~~~~~

- Added a simple e2e test suite.
- Improved the prose editor integration, added the required importmap
  dependency.
- Expanded the README a lot.


0.3 (2025-03-20)
~~~~~~~~~~~~~~~~

- Fixed the JSON plugin data reference handling.
- Added a ``[prose]`` extra depending on the newest alpha version of
  django-prose-editor.


0.2 (2024-12-04)
~~~~~~~~~~~~~~~~

- Included the `django-prose-editor
  <https://django-prose-editor.readthedocs.io/>`__ support by default, it's a
  small file without much impact as long as the editor itself isn't loaded. The
  minimum supported version of django-prose-editor is 0.10a5.
- Updated the JSON editor to 2.15.2.


0.1 (2024-08-02)
~~~~~~~~~~~~~~~~

- Initial beta release.
