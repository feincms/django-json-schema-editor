import { createEditor } from "django-prose-editor/configurable"

const core = {
  Document: true,
  Paragraph: true,
  HardBreak: true,
  Text: true,
  Menu: true,
}
const defaults = {
  Bold: true,
  Italic: true,
  Underline: true,
  Subscript: true,
  Superscript: true,
}

function createJSONProseEditor(textarea, options, setClobber) {
  setClobber(null)

  let extensions = defaults
  if (Object.hasOwn(options, "extensions")) {
    extensions = options.extensions
  }

  createEditor(textarea, {
    ...options,
    extensions: { ...core, ...extensions },
  }).then((editor) => {
    setClobber(() => {
      editor.destroy()
    })
  })
}

JSONEditor.defaults.editors.prose = class extends (
  JSONEditor.defaults.editors.string
) {
  setValue(value, initial, fromTemplate) {
    const res = super.setValue(value, initial, fromTemplate)

    if (res?.changed) {
      this.clobber?.()

      createJSONProseEditor(this.input, this.options, (clobber) => {
        this.clobber = clobber
      })
    }
  }

  build() {
    this.options.format = "textarea"
    super.build()
    this.input_type = this.schema.format // Restore original format
  }

  afterInputReady() {
    this.clobber?.()
    createJSONProseEditor(this.input, this.options, (clobber) => {
      this.clobber = clobber
    })

    this.input.addEventListener("input", (e) => {
      e.preventDefault()
      e.stopPropagation()

      this.value = this.input.value
      this.onChange(true)
    })
  }

  getNumColumns() {
    return 6
  }
}

JSONEditor.defaults.resolvers.unshift((schema) => {
  if (schema.type === "string" && schema.format === "prose") {
    return "prose"
  }
})
