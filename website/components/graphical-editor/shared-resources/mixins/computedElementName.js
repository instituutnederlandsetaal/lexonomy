export default {
   inject: ['editorState'],
  props: {
    elementData: Object,
    isAttribute: {
      type: Boolean
    },
    parentElementName: {
      type: String
    }
  },
  computed: {
    computedElementNameWithColon() {
       if (!this.computedElementName) {
          return ""
       }
      return this.computedElementName + ":"
    },
    computedElementName() {
      if (this.elementData && this.elementData.hideElementName) {
        return ""
      }
      const structureConfig = this.editorState.entry.dictConfigs.xema.elements
      let name = (structureConfig[this.elementName] && structureConfig[this.elementName].elementName) || this.elementName
      if (this.isAttribute) {
        try {
          let optionality = structureConfig[this.parentElementName].attributes[this.elementName].optionality

          if (optionality === "obligatory") {
            name += "*"
          }
        } catch (e) {
          console.log("", name)
        }
      }
      return name
    }
  }
}
