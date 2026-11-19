<template>
   <div>
      <section v-if="elementData.shown && !readOnly" class="text-input">
         <label v-if="isAttribute && !elementData.hideElementName" :for="id" class="text--md">
            {{ name }}{{ mandatory ? '*' : '' }}:
         </label>
         <textarea v-if="elementData.editorInputType === 'textarea'" :id="id" :name="name"
                   cols="30" rows="10" :value="value" :placeholder="name" :aria-label="name"
                   :aria-required="mandatory" :aria-invalid="invalid"
                   :class="{ error: invalid }" @input="updateValue" @compositionend="updateValue" @blur="blurred = true"/>
         <input v-else :id="id" :name="name" :type="elementData.editorInputType === 'number' ? 'number' : 'text'"
                :value="value" :placeholder="name" :aria-label="name" :aria-required="mandatory" :aria-invalid="invalid"
                :class="{ error: invalid }" @input="updateValue" @compositionend="updateValue" @blur="blurred = true">
         <button v-if="elementData.interactivity" class="button--sm tertiary" type="button" @click="preview">Preview</button>
      </section>
      <section v-else-if="elementData.shown" class="read-only">
         <p v-if="showPreview && !elementData.hideElementName" class="text--xs">{{ name }}: </p>
         <span :class="showPreview ? 'text--xs' : 'text--md'">{{ value }}</span>
      </section>
   </div>
</template>

<script setup lang="ts">
import { editorContextKey, requiredFieldsKey } from '../../editor-context.ts'
import { computed, inject, onBeforeUnmount, ref, useId } from 'vue'
import type { Attributes, Element } from 'xml-js'
import { xmlElementName } from '../../../../js/xema.ts'
import { valueDefinition, type ElementDisplay } from '../../editor-schema.ts'

const props = defineProps<{
   elementData: ElementDisplay
   elementName: string
   parentElementName?: string
   content: Element
   isAttribute?: boolean
   showPreview?: boolean
}>()
const emit = defineEmits<{ input: [change: { elementName: string; attributes?: Attributes; elements?: Element[] }] }>()
const editor = inject(editorContextKey)!
const requiredFields = inject(requiredFieldsKey)!
const id = useId()
const xema = computed(() => editor.config.xema)
const name = computed(() => props.isAttribute ? props.elementName : xmlElementName(xema.value, props.elementName))
const readOnly = computed(() => props.elementData.readOnly || props.showPreview)
const value = computed(() => String(props.content.text ?? ''))
const blurred = ref(false)
const mandatory = computed(() => {
   const definition = valueDefinition(xema.value, props.elementName, props.parentElementName, props.isAttribute)
   return Boolean(props.isAttribute && definition && 'optionality' in definition && definition.optionality === 'obligatory')
})
const invalid = computed(() => Boolean(blurred.value && missingField()))
requiredFields.add(missingField)
onBeforeUnmount(() => requiredFields.delete(missingField))

function missingField() {
   if (props.elementData.shown && !readOnly.value && mandatory.value && !value.value.trim()) return name.value
}

function updateValue(event: Event) {
   if (event instanceof InputEvent && event.isComposing) return
   const text = (event.target as HTMLInputElement | HTMLTextAreaElement).value
   if (text === value.value) return
   const { content, elementName } = props
   if (props.isAttribute) emit('input', { elementName, attributes: { [content.name ?? elementName]: text } })
   else emit('input', { elementName, elements: [{ ...content, text }] })
}

function preview() {
   const text = value.value.trim()
   if (!text || !URL.canParse(text, document.baseURI)) return
   const url = new URL(text, document.baseURI)
   if (url.protocol === 'https:' || url.protocol === 'http:') window.open(url.href, '_blank', 'noopener,noreferrer')
}
</script>

<style scoped>
.text-input { display: flex; align-items: baseline; }
.text-input label { font-size: 1rem; text-transform: capitalize; padding-right: 10px; color: inherit; }
.text-input button { margin-left: 8px; }
</style>
