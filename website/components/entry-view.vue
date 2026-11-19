<template>
<entry-view>
   <LoadingOverlay v-if="loading"/>
   <div class="viewer" id="viewer" v-html="html"></div>
</entry-view>
</template>

<script setup>
import Materialize from '../libs/materialize/materialize.min.js'
import { computed, ref, watch } from 'vue'
import { api } from '../js/api.ts'
import { activeDictionary } from '../js/dictionary-workspace.ts'
import { entryHtml } from '../widgets/xemplatron.js'
import LoadingOverlay from './loading-overlay.vue'

const loading = ref(false)
const entry = ref(null)
const html = computed(() => entry.value && activeDictionary.config ? entryHtml(entry.value, activeDictionary.config) : '')

watch(() => activeDictionary.entryId, async (id, _, onCleanup) => {
   entry.value = null
   loading.value = Boolean(id)
   if (!id) return
   let current = true
   onCleanup(() => { current = false })
   try {
      const result = await api.post(`${encodeURIComponent(activeDictionary.dictId)}/entryread.json`, { id })
      if (current && result.success) entry.value = result
      else if (current) Materialize.toast({ html: 'Could not load entry.' })
   } catch {
      if (current) Materialize.toast({ html: 'Could not load entry.' })
   } finally {
      if (current) loading.value = false
   }
}, { immediate: true })
</script>

<style>
entry-view {
   position: relative;
   display: block;
   min-height: calc(100vh - 260px);
}
</style>
