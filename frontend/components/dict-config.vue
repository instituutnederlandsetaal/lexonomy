<template>
<div class="dict-config">
   <DictNav :links="[['config', 'Configure']]"/>
   <h1>Configuration</h1>
   <div class="row" v-if="!state.isResaving && (state.stats.needUpdate ?? 0) > 0">
      Your dictionary needs to be re-indexed ({{ state.stats.needUpdate }} entries).
      <button v-if="canReindex" type="button" class="btn" style="margin-left: 15px;" @click="resave">Do it now</button>
      <br>
      <span style="opacity: 75%; font-size: 80%;">You don't have to do this right now. But your dictionary may take longer to load, and searching entries may not always return the results you expect until you re-index.</span>
   </div>
   <div v-if="state.isResaving">
      <span>{{ state.resaveProgressMessage || 'Re-indexing...' }}</span>
      <br>
      <span style="opacity: 75%; font-size: 80%;">You may close or leave this window at any time to pause the process, and return later to resume.</span>
   </div>
   <div class="columnContainer"
         style="margin-left: 20px;">
      <div>
         <h3 class="header">Manage dictionary</h3>
         <ul>
            <li>
               <RouterLink :to="{ name: 'config-ident', params: { dictId } }">Description</RouterLink>
            </li>
            <li>
               <RouterLink :to="{ name: 'config-users', params: { dictId } }">Users</RouterLink>
            </li>
            <li>
               <RouterLink :to="{ name: 'config-publico', params: { dictId } }">Publishing</RouterLink>
            </li>
            <li>
               <RouterLink :to="{ name: 'config-url', params: { dictId } }">Change URL</RouterLink>
            </li>
         </ul>
      </div>
      <div>
         <h3 class="header">Entry settings</h3>
         <ul>
            <li>
               <RouterLink :to="{ name: 'config-xema', params: { dictId } }">Structure</RouterLink>
            </li>
            <li>
               <RouterLink :to="{ name: 'config-xemplate', params: { dictId } }">Formatting</RouterLink>
            </li>
            <li>
               <RouterLink :to="{ name: 'config-titling', params: { dictId } }">Headword list</RouterLink>
            </li>
            <li>
               <RouterLink :to="{ name: 'config-searchability', params: { dictId } }">Searching</RouterLink>
            </li>
         </ul>
      </div>
      <div style="margin-right: auto;">
         <h3 class="header">Expert settings</h3>
         <ul>
            <li>
               <RouterLink :to="{ name: 'config-editing', params: { dictId } }">Entry editor</RouterLink>
            </li>
            <li>
               <RouterLink :to="{ name: 'config-flagging', params: { dictId } }">Flags</RouterLink>
            </li>
            <li>
               <RouterLink :to="{ name: 'config-autonumber', params: { dictId } }">Auto-numbering</RouterLink>
            </li>
            <li>
               <RouterLink :to="{ name: 'config-links', params: { dictId } }">Linking</RouterLink>
            </li>
            <li>
               <RouterLink :to="{ name: 'config-download', params: { dictId } }">Download settings</RouterLink>
            </li>
            <li>
               <RouterLink :to="{ name: 'config-subbing', params: { dictId } }">Subentries</RouterLink>
            </li>
         </ul>
      </div>
   </div>

</div>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import Materialize from '../libs/materialize/materialize.min.js'
import { fetchDictionaryStats, reindexDictionaryBatch } from '../js/dictionary-config-api.ts'
import { activeDictionary } from '../js/dictionary-workspace.ts'
import { useDictionaryScope } from '../js/use-dictionary-setting.ts'
import DictNav from './dict-nav.vue'

const props = defineProps<{ dictId: string }>()
const scope = useDictionaryScope(() => props.dictId)
const state = reactive({
   stats: {} as Awaited<ReturnType<typeof fetchDictionaryStats>>,
   isResaving: false,
   resaveProgressMessage: ''
})
const canReindex = computed(() => {
   const access = activeDictionary.userAccess
   return activeDictionary.dictId === props.dictId && access?.canEdit && access.canConfig && access.canUpload
})
watch(scope, async current => {
   state.stats = {}
   state.isResaving = false
   state.resaveProgressMessage = ''
   try {
      const stats = await fetchDictionaryStats(current.dictId)
      if (current.active) state.stats = stats
   } catch {
      if (current.active) Materialize.toast({ html: 'Could not load dictionary statistics.' })
   }
}, { immediate: true })

async function resave() {
   if (state.isResaving || !canReindex.value) return
   const current = scope.value
   state.isResaving = true
   let remaining = Number.POSITIVE_INFINITY
   try {
      while (current.active) {
         const { todo, finished, progressMessage } = await reindexDictionaryBatch(current.dictId)
         if (!current.active) return
         state.stats.needUpdate = todo
         if (finished) return
         if (todo >= remaining) throw new Error('Re-indexing did not make progress')
         remaining = todo
         state.resaveProgressMessage = progressMessage
      }
   } catch {
      if (current.active) Materialize.toast({ html: 'Re-indexing stopped. Try again to resume.' })
   } finally {
      if (current.active) state.isResaving = false
   }
}
</script>

<style>
.dict-config .columnContainer{
   display: flex;
   gap: 4vw;
   justify-content: space-between;
   margin: auto;
}
.dict-config li{
   padding: 0 0 0.7rem 0.7rem;
}
</style>
