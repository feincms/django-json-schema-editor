/* global JSONEditor */
JSONEditor.defaults.language = "de"
JSONEditor.defaults.languages.de = {
  error_notset: "Eigenschaft muss gesetzt sein",
  error_notempty: "Wert wird benötigt",
  error_enum: "Wert muss einer der erlaubten Werte sein",
  error_const: "Wert muss der konstante Wert sein",
  error_anyOf:
    "Wert muss mindestens einem der bereitgestellten Schemas entsprechen",
  error_oneOf:
    "Wert muss genau einem der bereitgestellten Schemas entsprechen. Aktuell entspricht er {{0}} der Schemas.",
  error_not: "Wert darf dem bereitgestellten Schema nicht entsprechen",
  error_type_union: "Wert muss einen der bereitgestellten Typen haben",
  error_type: "Wert muss vom Typ {{0}} sein",
  error_disallow_union:
    "Wert darf nicht von einem der bereitgestellten verbotenen Typen sein",
  error_disallow: "Wert darf nicht vom Typ {{0}} sein",
  error_multipleOf: "Wert muss ein Vielfaches von {{0}} sein",
  error_maximum_excl: "Wert muss weniger als {{0}} sein",
  error_maximum_incl: "Wert muss höchstens {{0}} sein",
  error_minimum_excl: "Wert muss grösser als {{0}} sein",
  error_minimum_incl: "Wert muss mindestens {{0}} sein",
  error_maxLength: "Wert darf höchstens {{0}} Zeichen lang sein",
  // error_contains: "No items match contains",
  error_minContains:
    "Die Anzahl der Treffer ({{0}}) liegt unter der minimal geforderten Anzahl von {{1}}",
  error_maxContains:
    "Die Anzahl der Treffer ({{0}}) überschreitet die maximal erlaubte Anzahl von {{1}}",
  error_minLength: "Wert muss mindestens {{0}} Zeichen lang sein",
  error_pattern: "Wert muss dem Muster {{0}} entsprechen",
  error_additionalItems: "Keine zusätzlichen Elemente in diesem Array erlaubt",
  error_maxItems: "Wert darf höchstens {{0}} Elemente enthalten",
  error_minItems: "Wert muss mindestens {{0}} Elemente enthalten",
  error_uniqueItems: "Elemente des Arrays müssen eindeutig sein",
  error_maxProperties: "Objekt darf höchstens {{0}} Eigenschaften haben",
  error_minProperties: "Objekt muss mindestens {{0}} Eigenschaften haben",
  error_required: "Der erforderlichen Eigenschaft '{{0}}' fehlt im Objekt",
  error_additional_properties:
    "Keine zusätzlichen Eigenschaften erlaubt, aber die Eigenschaft {{0}} ist gesetzt",
  error_property_names_exceeds_maxlength:
    "Eigenschaftsname {{0}} überschreitet die maximale Länge",
  error_property_names_enum_mismatch:
    "Eigenschaftsname {{0}} entspricht keinem der erlaubten Werte",
  error_property_names_const_mismatch:
    "Eigenschaftsname {{0}} entspricht nicht dem konstanten Wert",
  error_property_names_pattern_mismatch:
    "Eigenschaftsname {{0}} entspricht nicht dem Muster",
  error_property_names_false:
    "Eigenschaftsname {{0}} ist ungültig, da propertyName auf false gesetzt ist",
  error_property_names_maxlength:
    "Eigenschaftsname {{0}} kann eine ungültige maxLength-Angabe nicht erfüllen",
  error_property_names_enum:
    "Eigenschaftsname {{0}} kann eine ungültige Enum-Angabe nicht erfüllen",
  error_property_names_pattern:
    "Eigenschaftsname {{0}} kann ein ungültiges Muster nicht erfüllen",
  error_property_names_unsupported: "Nicht unterstützter propertyName {{0}}",
  error_dependency: "Muss die Eigenschaft {{0}} besitzen",
  error_date: "Datum muss dem Format {{0}} entsprechen",
  error_time: "Zeit muss dem Format {{0}} entsprechen",
  error_datetime_local: "Datum/Zeit muss dem Format {{0}} entsprechen",
  error_invalid_epoch: "Datum muss nach dem 1. Januar 1970 liegen",
  error_ipv4:
    "Wert muss eine gültige IPv4-Adresse sein, bestehend aus 4 durch Punkte getrennten Zahlen zwischen 0 und 255",
  error_ipv6: "Wert muss eine gültige IPv6-Adresse sein",
  error_hostname: "Der Hostname hat das falsche Format",
  upload_max_size: "Datei zu gross. Maximale Grösse ist ",
  upload_wrong_file_format: "Falsches Dateiformat. Erlaubte Formate: ",
  button_save: "Sichern",
  button_copy: "Kopieren",
  button_cancel: "Abbrechen",
  button_add: "Hinzufügen",
  button_delete_all: "Alle",
  button_delete_all_title: "Alle löschen",
  button_delete_last: "Letztes {{0}}",
  button_delete_last_title: "Letztes {{0}} löschen",
  button_add_row_title: "{{0}} hinzufügen",
  button_move_down_title: "Nach unten",
  button_move_up_title: "Nach oben",
  button_properties: "Eigenschaften",
  button_object_properties: "Objekteigenschaften",
  button_copy_row_title: "{{0}} kopieren",
  button_delete_row_title: "{{0}} löschen",
  button_delete_row_title_short: "Löschen",
  button_copy_row_title_short: "Kopieren",
  button_collapse: "Einklappen",
  button_expand: "Aufklappen",
  button_edit_json: "JSON bearbeiten",
  button_upload: "Hochladen",
  flatpickr_toggle_button: "Umschalten",
  flatpickr_clear_button: "Leeren",
  choices_placeholder_text: "Tippen, um einen Wert hinzuzufügen",
  default_array_item_title: "Element",
  button_delete_node_warning: "Dieses Element wirklich löschen?",
}
