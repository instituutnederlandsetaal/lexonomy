<template>
   <div>
      <section v-if="elementData.shown && !readOnly" class="dropdown" :class="{ error: validationMessage }">
         <p v-if="isAttribute" class="text--md">{{ name }}:</p>
         <FormSelect :model-value="value" :options="options" :aria-label="name"
                     :placeholder="`Choose ${name}`" @update:model-value="choose"
                     @blur="hasBlurred = true"/>
      </section>
      <section v-else-if="elementData.shown" class="read-only">
         <p v-if="showPreview" class="text--xs">{{ name }}:</p>
         <span :class="showPreview ? 'text--xs' : 'text--md'">{{ valueCaption }}</span>
      </section>
   </div>
</template>

<script setup lang="ts">
import { editorContextKey, requiredFieldsKey } from '../../editor-context.ts'
import { computed, inject, onBeforeUnmount, ref } from 'vue'
import type { Attributes, Element } from 'xml-js'
import { xmlElementName } from '../../../../js/xema.ts'
import FormSelect from '../../../FormSelect.vue'
import { valueDefinition, type ElementDisplay } from '../../editor-schema.ts'

const props = defineProps<{
   elementData: ElementDisplay
   elementName: string
   parentElementName?: string
   content: Element
   isAttribute?: boolean
   showPreview?: boolean
}>()
const emit = defineEmits<{
   input: [change: { elementName: string; attributes?: Attributes; elements?: Element[] }]
}>()
const editor = inject(editorContextKey)!
const requiredFields = inject(requiredFieldsKey)!
const hasBlurred = ref(false)
const readOnly = computed(() => props.elementData.readOnly || props.showPreview)
const xema = computed(() => editor.config.xema)
const definition = computed(() => valueDefinition(xema.value, props.elementName, props.parentElementName, props.isAttribute))
const mandatory = computed(() => props.isAttribute && definition.value && 'optionality' in definition.value && definition.value.optionality === 'obligatory')
const name = computed(() => props.isAttribute ? props.elementName : xmlElementName(xema.value, props.elementName))
const options = computed(() => (definition.value?.values ?? []).map(({ value, caption }) => ({ value, label: caption || value })))
const value = computed(() => String(props.content.text ?? ''))
const valueCaption = computed(() => options.value.find(option => option.value === value.value)?.label ?? value.value)
const validationMessage = computed(() => hasBlurred.value && missingField() ? `The ${name.value} value is required.` : '')
requiredFields.add(missingField)
onBeforeUnmount(() => requiredFields.delete(missingField))

function missingField() {
   if (props.elementData.shown && !readOnly.value && mandatory.value && !value.value) return name.value
}

function choose(nextValue: unknown) {
   if (typeof nextValue !== 'string' || nextValue === value.value) return
   hasBlurred.value = true
   const { content, elementName } = props
   if (props.isAttribute) emit('input', { elementName, attributes: { [content.name ?? elementName]: nextValue } })
   else emit('input', { elementName, elements: [{ ...content, text: nextValue }] })
}
</script>

<style scoped>
.dropdown { display: flex; align-items: baseline; }
.dropdown p { margin-right: 8px; color: inherit; }
</style>
