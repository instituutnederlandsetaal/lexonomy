<template>
  <div>
    <section v-if="elementData.shown && !readOnly"
             class="dropdown"
             :class="{ error: validationMessage }">
      <p class="text--md">{{ (isAttribute) ? computedElementNameWithColon : '' }}</p>
      <select
        ref="select"
        :name="computedElementName || elementName"
        v-model="value"
        @change="hasBlurred = true"
      >
        <option
          value=""
          disabled
        >
          Choose {{ computedElementName || elementName }}
        </option>
        <option v-for="option in options" :key="option.value" :value="option.value">{{ option.caption }}</option>
      </select>
    </section>
    <section v-if="elementData.shown && readOnly" class="read-only">
      <p v-if="showPreview" :class="computedClass">{{ computedElementNameWithColon }} </p>
      <span :class="computedClass">{{ valueCaption }}</span>
    </section>
  </div>
</template>

<script>
import Materialize from '../../../../libs/materialize/materialize.min.js'

import computedElementName from "../../shared-resources/mixins/computedElementName.js"
import showPreview from "../../shared-resources/mixins/showPreview.js"
import computedValidation from "../../shared-resources/mixins/computedValidation.js"

export default {
  inject: ['editorState'],
  name: "DropdownComponent",
  emits: ['input'],
  props: {
    elementData: Object,
    elementName: String,
    content: {
      type: Object,
      required: true
    }
  },
  mixins: [computedElementName, showPreview, computedValidation],
  computed: {
    valueCaption() {
      let selectedOption = this.options.find(el => el.value === this.value)
      return selectedOption && selectedOption.caption
    }
  },
  data() {
    return {
      value: null,
      options: []
    }
  },
  watch: {
    content(content) {
      this.value = content.text ?? ''
    },
    value(newVal) {
      if (newVal === this.content.text) {
        return
      }
      if (this.content.type === "attribute") {
        this.$emit('input', {elementName: this.elementName, attributes: {[this.content.name]: newVal}})
      } else {
        let elements = Object.assign({}, this.content)
        elements.text = newVal
        this.$emit('input', {elementName: this.elementName, elements: [elements]})
      }
    }
  },
  created() {
    let structureConfig = this.editorState.entry.dictConfigs.xema.elements[this.elementName]
    if (!structureConfig) {
      let parentConfig = this.editorState.entry.dictConfigs.xema.elements[this.parentElementName].attributes || {}
      structureConfig = parentConfig[this.elementName]
    }
    this.options = structureConfig?.values ?? []
    this.value = this.content.text ?? ''
  },
  mounted() {
    if (this.$refs.select) {
      Materialize.FormSelect.init(this.$refs.select)
    }
  },
  beforeUnmount() {
    if (this.$refs.select) {
      Materialize.FormSelect.getInstance(this.$refs.select)?.destroy()
    }
  }
}
</script>

<style lang="scss" scoped>
.dropdown {
  display: flex;
  justify-content: start;

  p {
    margin-right: 8px;
    color: inherit;
  }
}

</style>
