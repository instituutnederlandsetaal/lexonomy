export default {
  inject: ['editorState', 'requiredFields'],
  data() {
    return {
      hasBlurred: false
    }
  },
  computed: {
    validationMessage() {
      const field = this.hasBlurred && this.missingField()
      return field ? `The ${field} value is required.` : ''
    }
  },
  mounted() {
    this.requiredFields.add(this.missingField)
  },
  beforeUnmount() {
    this.requiredFields.delete(this.missingField)
  },
  methods: {
    missingField() {
      if (!this.elementData.shown || this.readOnly || !this.isAttribute) return
      const attribute = this.editorState.entry.dictConfigs.xema.elements[this.parentElementName]?.attributes?.[this.elementName]
      if (attribute?.optionality === 'obligatory' && !String(this.value ?? '').trim()) {
        return this.computedElementName || this.elementName
      }
    }
  }
}
