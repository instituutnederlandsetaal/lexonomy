<template>
  <div v-if="editorState.entry.dictConfigs && editorState.entry.dictConfigs.xemplate">
    <ComponentGeneratorComponent
      :children="preparedDataForEntry"
      :content="dataStructure"
      @input="handleContentUpdate"
    />

  </div>
</template>

<script>
import ComponentGeneratorComponent from "./ComponentGeneratorComponent.vue"
import {js2xml, xml2js} from "xml-js"

export default {
  name: "EntryDisplay",
  inject: ['editorState', 'requiredFields'],
  components: {
    ComponentGeneratorComponent
  },
  emits: ['dirty-change'],
  watch: {
    dirty(value) {
      this.$emit('dirty-change', value)
    }
  },
  computed: {
    preparedDataForEntry() {
      if (!this.editorState.entry.dictConfigs) {
        return []
      }
      const content = this.editorState.entry.content
      let rootName = (content.elements && content.elements[0] && content.elements[0].name) || this.editorState.entry.dictConfigs.xema.root
      return [{
        max: 1,
        min: 1,
        name: rootName
      }]
    }
  },
  data() {
    return {
      dataStructure: {},
      dirty: false
    }
  },
  created() {
    this.dataStructure = this.editorState.entry.content
    this.setHeadwordElement()
  },
  methods: {
    setHeadwordElement() {
      let config = this.editorState.entry.dictConfigs
      let titling = config.titling
      if (titling && titling.headword) {
        this.editorState.headwordElement = titling.headword
        return
      }
      let root = config.xema.root
      if (root) {
        let rootConfig = config.xema.elements[root]
        if (rootConfig && rootConfig.children && rootConfig.children.length > 0) {
          this.editorState.headwordElement = rootConfig.children[0].name
        }
      }
    },
    handleContentUpdate(data) {
      this.dataStructure = data.content
      this.dirty = this.areAnyChanges()
    },
    areAnyChanges() {
      let structureCopy = this.createDeepCopy()
      this.fixElementNames(structureCopy)
      let updatedContent = js2xml(structureCopy, this.editorState.xml2jsConfig)
      let initialContent = js2xml(this.editorState.initialContent, this.editorState.xml2jsConfig)
      return initialContent != updatedContent
    },
    getXmlData() {
      const missing = [...this.requiredFields].map(check => check()).filter(Boolean)
      if (missing.length && !confirm(`Are you sure you want to save despite some elements missing? \n \n Missing fields: \n${missing.join('\n')}`)) {
        return null
      }
      return this.prepareXMLData()
    },
    prepareXMLData() {
      let structureCopy = this.createDeepCopy()
      delete structureCopy.declaration
      this.fixElementNames(structureCopy)
      return js2xml(structureCopy, this.editorState.xml2jsConfig)
    },
    createDeepCopy() {
      let xml = js2xml(this.dataStructure, this.editorState.xml2jsConfig)
      return xml2js(xml, this.editorState.xml2jsConfig)
    },
    fixElementNames(structure) {
      if (structure.name) {
        let config = this.getStructureConfig(structure.name)
        if (config && config.elementName) {
          structure.name = config.elementName
        }
      }
      if (structure.attributes) {
        for (const attribute of Object.keys(structure.attributes)) {
          let config = this.getStructureConfig(attribute, structure.name)
          if (config && config.elementName) {
            structure.attributes[config.elementName] = structure.attributes[attribute]
            delete structure.attributes[attribute]
          }
        }
      }
      if (structure.elements) {
        for (const element of structure.elements) {
          this.fixElementNames(element)
        }
      }
    },
    getStructureConfig(elementName, parentElement = null) {
      let config = this.editorState.entry.dictConfigs.xema.elements
      if (!config[elementName]) {
        return {}
      }
      if (parentElement) {
        return config[parentElement].attributes[elementName]
      }
      return config[elementName] || {}
    }
  }
}
</script>

<style scoped>

</style>
