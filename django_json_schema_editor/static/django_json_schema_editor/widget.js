window.__djse_foreignKeys = {}

document.addEventListener("DOMContentLoaded", () => {
  const editors = document.querySelectorAll(".django_json_schema_editor")
  for (const el of editors) {
    const textarea = el.querySelector("textarea")
    if (textarea && !textarea.id.includes("__prefix__")) {
      initEditor(el)
    }
  }
})

document.addEventListener("DOMContentLoaded", () => {
  django.jQuery(document).on("formset:added", (event) => {
    const editors = event.target.querySelectorAll(".django_json_schema_editor")
    for (const el of editors) {
      initEditor(el)
    }
  })
})

let editorIndex = 0

const initEditor = (el) => {
  if (el.dataset.foreignKey) {
    Object.assign(window.__djse_foreignKeys, JSON.parse(el.dataset.foreignKey))
  }

  const input = el.querySelector("textarea")
  const config = JSON.parse(el.dataset.editorConfig)

  let value
  if (input.value && (value = JSON.parse(input.value))) {
    config.startval = value
  }

  // Set an unique name so that form widgets get somewhat more unique names
  config.form_name_root = `djse${++editorIndex}`

  const editor = new JSONEditor(el, config)
  editor.on("change", () => {
    input.value = JSON.stringify(editor.getValue())
  })

  // The JSON is only updated on change events. This can cause edits to be lost
  // when directly triggering a save without first leaving the input element.
  // (e.g. when using ctrl-s in the django-content-editor)
  const dispatchChangeEventOnInput = debounce((e) => {
    if (e.target.matches("input, textarea")) {
      e.target.dispatchEvent(new Event("change", { bubbles: true }))
    }
  }, 100)

  editor.element.addEventListener("input", dispatchChangeEventOnInput)
}

const debounce = (f, ms) => {
  let t
  return (...a) => {
    clearTimeout(t)
    t = setTimeout(() => f(...a), ms)
  }
}
