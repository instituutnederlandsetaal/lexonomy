<template>
  <div>
    <section class="media-input" v-if="elementData.shown && !readOnly">
      <label v-if="isAttribute" class="text--md" :for="computedElementName">{{ computedElementNameWithColon }}</label>
      <input :name="computedElementName" type="text" v-model="value"
             @change="updateParent">
    </section>

    <section v-if="elementData.shown && readOnly" class="read-only">
      <p v-if="showPreview" :class="computedClass">{{ computedElementNameWithColon }} </p>
      <span :class="computedClass">{{ value }}</span>
    </section>
  </div>
</template>

<script>
import computedElementName from "../../shared-resources/mixins/computedElementName.js"
import showPreview from "../../shared-resources/mixins/showPreview.js"

export default {
  name: "MediaComponent",
  emits: ['input'],
  props: {
    elementData: Object,
    elementName: String,
    content: {
      type: Object,
      required: true
    }
  },
  mixins: [computedElementName, showPreview],
  data() {
    return {
      value: ""
    }
  },
  mounted() {
    this.value = this.content.text
  },
  methods: {
    updateParent() {
      this.$nextTick(() => {
        if (this.value === this.content.text) {
          return
        }
        if (this.content.type === "attribute") {
          this.$emit('input', {elementName: this.elementName, attributes: {[this.content.name]: this.value}})
        } else {
          let elements = Object.assign({}, this.content)
          elements.text = this.value
          this.$emit('input', {elementName: this.elementName, elements: [elements]})
        }
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.media-input {
  display: flex;
  align-items: center;

  input {
    margin: 0;
  }

  label {
    text-transform: capitalize;
    padding-right: 10px;
    color: inherit;
  }
}

</style>
