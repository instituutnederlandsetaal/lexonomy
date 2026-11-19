<template>
   <div id="editor" ref="element"></div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import type { WorkspaceConfig } from '../../js/dictionary-workspace.ts'
import type { EntryDraft, EntryRevision } from '../../js/entry-editor-api.ts'
import {
   createEditorExtensionServices, loadEditorExtension,
   type EditorExtensionEntry, type EditorExtensionEntryContext, type EditorExtensionInstance
} from '../../js/editor-extension.ts'
import { xmlElementName } from '../../js/xema.ts'
import { parseXml } from '../../js/xml.ts'

const props = defineProps<{
   source: string
   entry: EntryDraft | EntryRevision
   dictId: string
   config: WorkspaceConfig
   initialXml: string
   readOnly: boolean
}>()
const emit = defineEmits<{
   'mount-failed': []
   'dirty-change': [dirty: boolean]
   'open-entry': [id: number, doctype: string]
}>()
const element = ref<HTMLDivElement | null>(null)
const lifetime = new AbortController()
let instance: EditorExtensionInstance | undefined

function copyJson<T>(value: T): T {
   // Stored settings and entry data are JSON. Copy them out of Vue's reactive state.
   return JSON.parse(JSON.stringify(value))
}

onMounted(() => {
   if (!element.value) return
   try {
      const extension = loadEditorExtension(props.source)
      const schema = copyJson(props.config.xema)
      const definitions = copyJson(props.config.subbing)
      const draft = props.entry
      const entry: EditorExtensionEntry = {
         doctype: xmlElementName(schema, schema.root),
         schemaId: draft.schemaId ?? schema.root,
         content: draft.content || props.initialXml,
         ...('entry_id' in draft
            ? { id: draft.entry_id, revisionId: draft.revision_id }
            : copyJson({ id: draft.id, subentries: draft.subentries, parententries: draft.parententries })),
      }
      const context: EditorExtensionEntryContext = {
         dictionaryId: props.dictId,
         schema,
         entry,
         readOnly: props.readOnly,
         signal: lifetime.signal,
         headwordElement: definitions[schema.root]?.titling?.headword ?? props.config.titling.headword,
         ...createEditorExtensionServices(props.dictId, schema, definitions, lifetime.signal),
      }
      if (!entry.id && !draft.content && !props.readOnly && extension.initialXml) {
         const xml = extension.initialXml(context)
         if (typeof xml !== 'string' || !parseXml(xml)) throw new Error('Expected valid XML from initialXml()')
         entry.content = xml
      }
      instance = extension.mount({
         ...context,
         element: element.value,
         markDirty() {
            if (instance && !lifetime.signal.aborted && !props.readOnly) emit('dirty-change', true)
         },
         openEntry({ id, doctype }) {
            if (instance && !lifetime.signal.aborted) emit('open-entry', id, doctype)
         },
      })
      if (!instance || typeof instance.harvest !== 'function') throw new Error('Expected a harvest() method from mount()')
   } catch (error) {
      lifetime.abort()
      console.error('Failed to mount editor extension', error)
      emit('mount-failed')
   }
})

onBeforeUnmount(() => {
   lifetime.abort()
   try {
      instance?.dispose?.()
   } catch (error) {
      console.error('Failed to dispose editor extension', error)
   }
})

defineExpose({
   async harvest() {
      if (!instance || lifetime.signal.aborted) return
      const xml = await instance.harvest()
      if (typeof xml !== 'string') throw new Error('Expected an XML string from harvest()')
      return xml
   },
})
</script>
