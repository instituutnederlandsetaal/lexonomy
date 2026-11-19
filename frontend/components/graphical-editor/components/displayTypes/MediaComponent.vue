<template>
  <div>
    <section class="media-input" v-if="elementData.shown && !readOnly">
      <label v-if="isAttribute" class="text--md" :for="inputId">{{ label }}</label>
      <input :id="inputId" :name="fieldName" type="text" :value="value" aria-label="Media URL"
             @input="updateParent" @compositionend="updateParent">
    </section>

    <section v-if="elementData.shown && readOnly" class="read-only">
      <p v-if="showPreview" :class="textClass">{{ label }} </p>
      <span :class="textClass">{{ value }}</span>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, useId } from 'vue'
import type { Element } from 'xml-js'
import type { ElementDisplay } from '../../editor-schema.ts'
import type { ValueUpdate } from '../../use-editor-field.ts'

const props = defineProps<{
   elementData: ElementDisplay
   elementName: string
   content: Element
   isAttribute?: boolean
   showPreview?: boolean
}>()
const emit = defineEmits<{ input: [change: ValueUpdate] }>()
const inputId = useId()
const fieldName = computed(() => props.elementData.hideElementName ? '' : props.elementData.editorLabel)
const label = computed(() => fieldName.value ? fieldName.value + ':' : '')
const readOnly = computed(() => props.elementData.readOnly || props.showPreview)
const textClass = computed(() => props.showPreview ? 'text--xs' : 'text--md')
const value = computed(() => String(props.content.text ?? ''))

function updateParent(event: Event) {
   if ((event instanceof InputEvent && event.isComposing) || !(event.target instanceof HTMLInputElement)) return
   const { value: text } = event.target
   if (text === value.value) return
   const { content, elementName } = props
   if (props.isAttribute) emit('input', { attributes: { [content.name ?? elementName]: text } })
   else emit('input', { elements: [{ ...content, text }] })
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
