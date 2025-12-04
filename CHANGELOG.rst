Change log
==========

Next version
~~~~~~~~~~~~

- Added the material icons library and added the iconlib integration for it to
  the JSON editor by default.


0.11 (2025-11-19)
~~~~~~~~~~~~~~~~~

- **Backwards incompatible**: Changed the ``JSONPluginBase.proxy`` classmethod
  signature. The ``**class_dict`` parameter (introduced in 0.10) has been
  replaced with a ``mixins`` parameter that accepts a list or tuple of mixin
  classes. This provides a cleaner, more explicit pattern for extending proxy
  plugin functionality.

  Before (0.10 only)::

      MyPlugin = JSONPluginBase.proxy(
          "my_plugin",
          schema={...},
          custom_method=lambda self: "value",  # Added to class body
      )

  After::

      class MyMixin:
          def custom_method(self):
              return "value"

      MyPlugin = JSONPluginBase.proxy(
          "my_plugin",
          schema={...},
          mixins=[MyMixin],
      )

  The ``meta`` parameter (introduced in 0.10) continues to work for adding
  attributes to the ``Meta`` class. The ``verbose_name`` parameter also
  continues to work as before.

0.10 (2025-11-17)
~~~~~~~~~~~~~~~~~

- Cleaned up the implementation, added ``paths_to_pks`` to the fields module
  for reuse.
- **Backwards incompatible**: Changed the ``JSONPluginBase.proxy`` classmethod
  to add keyword arguments passed to it to the class and not to the ``Meta``
  class. To add to the ``Meta`` class, use the ``meta`` keyword argument. The
  ``verbose_name`` argument which is also used in the documentation continues
  to work.

0.9 (2025-11-13)
~~~~~~~~~~~~~~~~

- **Backwards incompatible change to ``JSONPluginBase``** The JSON pointer
  usage has been replaced by jmespath usage. ``__str__`` values in schemas for
  the ``JSONPluginBase`` should be updated for the new syntax (for example,
  ``object.title`` instead of ``/object/title``), otherwise the code acts as if
  they weren't there. Failures are silent because crashes aren't worth it.
  Removed the ``jsonpointer`` extra and instead added a hard dependency on
  ``jmespath``.
- Be more careful in ``JSONPluginBase.__str__`` to actually return strings.
- Allowed forwarding more config options to the configurable prose editor, not
  just extensions.
- Added a more streamlined way to use foreign key references when using the
  ``JSONPluginBase``, see ``foreign_key_paths`` and
  ``register_foreign_key_reference`` in the documentation. The new
  functionality allows preventing deletion of referenced objects and showing a
  description of the referenced object (like Django's own ``raw_id_fields``)
  with less steps.


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
