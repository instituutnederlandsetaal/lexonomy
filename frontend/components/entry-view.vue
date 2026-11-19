<template>
   <div class="entry-view">
      <LoadingOverlay v-if="loading"/>
      <div id="viewer" class="viewer"><RawHtml :content="html"/></div>
   </div>
</template>

<script setup lang="ts">
import Materialize from '../libs/materialize/materialize.min.js'
import { computed, ref, watch } from 'vue'
import { entryEditorApi, type EditorEntry } from '../js/entry-editor-api.ts'
import type { WorkspaceConfig } from '../js/dictionary-workspace.ts'
import { entryHtml, type CrossReferenceHref } from '../widgets/xemplatron.ts'
import LoadingOverlay from './loading-overlay.vue'
import RawHtml from './raw-html.vue'

const props = defineProps<{ dictId: string; entryId: number | null; config: WorkspaceConfig; crossReferenceHref: CrossReferenceHref }>()

const loading = ref(false)
const entry = ref<EditorEntry | null>(null)
const html = computed(() => entry.value ? entryHtml(entry.value, props.config, props.crossReferenceHref) : '')

watch([() => props.dictId, () => props.entryId], async ([dictId, id], _, onCleanup) => {
   entry.value = null
   loading.value = Boolean(dictId && id)
   if (!dictId || !id) return
   let current = true
   onCleanup(() => { current = false })
   try {
      const result = await entryEditorApi.read(dictId, id)
      if (!result.success) throw new Error('Entry not found')
      if (current) entry.value = result
   } catch {
      if (current) Materialize.toast({ html: 'Could not load entry.' })
   } finally {
      if (current) loading.value = false
   }
}, { immediate: true })
</script>

<style>
.entry-view {
   position: relative;
   min-height: calc(100vh - 260px);
}
</style>
