<template>
   <ComponentGeneratorComponent :children="rootChildren" :content="draft" @input="update"/>
</template>

<script setup lang="ts">
import { editorContextKey, provideEditorDraft, requiredFieldsKey } from '../editor-context.ts'
import { computed, inject, shallowRef } from 'vue'
import type { Element } from 'xml-js'
import ComponentGeneratorComponent from './ComponentGeneratorComponent.vue'
import { elementId, serializeDraft } from '../editor-schema.ts'

const props = defineProps<{ content: Element; originalXml: string }>()
const emit = defineEmits<{ 'dirty-change': [dirty: boolean] }>()
const editor = inject(editorContextKey)!
const requiredFields = inject(requiredFieldsKey)!
const draft = shallowRef(props.content)
const originalDraft = serializeDraft(props.content)
const rootChildren = computed(() => {
   const { xema } = editor.config
   const root = props.content.elements?.find(node => node.type === 'element')
   return [{ name: (root && elementId(xema, root)) || xema.root }]
})

provideEditorDraft(() => draft.value, content => update({ content }))
defineExpose({ harvest })

function update({ content }: { content: Element }) {
   draft.value = content
   emit('dirty-change', serializeDraft(content) !== originalDraft)
}

function harvest() {
   const missing = [...requiredFields].map(check => check()).filter(Boolean)
   if (missing.length && !window.confirm(`Save with these required fields empty?\n\n${missing.join('\n')}`)) return null
   const xml = serializeDraft(draft.value)
   return xml === originalDraft ? props.originalXml : xml
}
</script>
