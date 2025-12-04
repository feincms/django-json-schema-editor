/* global JSONEditor */

JSONEditor.defaults.themes.django = class DjangoTheme extends (
  JSONEditor.defaults.themes.html
) {
  getIndentedPanel() {
    const el = super.getIndentedPanel()

    // reset styles (borders/spacing)
    el.removeAttribute("style")

    // set class for easier styling via css
    el.setAttribute("class", "indented-panel")
    return el
  }
  getButton(text, icon, title) {
    const el = super.getButton(text, icon, title)
    el.setAttribute("class", `${el.getAttribute("class")} button`)
    return el
  }
  getButtonHolder() {
    const el = super.getButtonHolder()
    el.removeAttribute("style")
    el.classList.add("je-button-holder")
    return el
  }
  getHeaderButtonHolder() {
    const el = super.getHeaderButtonHolder()
    el.removeAttribute("style")
    el.classList.add("je-button-holder")
    return el
  }
  getTabHolder() {
    const el = super.getTabHolder()
    el.setAttribute("class", "je-tab-holder")
    el.innerHTML = [
      "<div class='je-tabs'></div>",
      "<div class='je-content'></div>",
      "<div style='clear:both;'></div>",
    ].join("")
    return el
  }
  getTab(span) {
    const el = super.getTab(span)
    el.appendChild(span)
    el.setAttribute("class", "je-tab button")
    el.removeAttribute("style")
    return el
  }
  markTabActive(row) {
    super.markTabActive(row)
    row.tab.classList.add("active")
    row.tab.removeAttribute("style")
  }
  getTextareaInput() {
    // reset styles
    const el = super.getTextareaInput()

    // set class for easier styling via css
    el.removeAttribute("style")
    return el
  }
  setGridColumnSize(el, size) {
    el.setAttribute("style", `width: ${(size / 12) * 100}%`)
  }
}

const iconClass = "material-icons"
const iconPrefix = ""
const mapping = {
  collapse: "arrow_drop_up",
  expand: "arrow_drop_down",
  delete: "delete",
  edit: "edit",
  add: "add",
  subtract: "remove",
  cancel: "cancel",
  save: "save",
  moveup: "arrow_upward",
  movedown: "arrow_downward",
  moveright: "arrow_forward",
  moveleft: "arrow_back",
  copy: "content_copy",
  clear: "highlight_off",
  time: "access_time",
  calendar: "calendar_today",
  upload: "cloud_upload",
  edit_properties: "list",
}

JSONEditor.defaults.iconlibs.django = class DjangoTheme extends (
  JSONEditor.AbstractIconLib
) {
  constructor() {
    super(iconPrefix, mapping)
    this.icon_class = iconClass
  }

  getIconClass(_key) {
    /* This method is unused. */
    return this.icon_class
  }

  getIcon(key) {
    /* Get the mapping. */
    const mapping = this.mapping[key]
    if (!mapping) return null

    /* @see http://materializecss.com/icons.html */
    const i = document.createElement("i")
    i.classList.add(this.icon_class)
    const t = document.createTextNode(mapping)
    i.appendChild(t)
    return i
  }
}
