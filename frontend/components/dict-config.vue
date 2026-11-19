<template>
<dict-config>
   <DictNav :links="[['config', 'Configure']]"/>
   <h1>Configuration</h1>
   <div class="row" v-if="!state.isResaving && state.stats && state.stats.needUpdate > 0">
      Your dictionary needs to be re-indexed ({{ state.stats.needUpdate }} entries). <button class="btn" style="margin-left: 15px;" @click="resave">Do it now </button>
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
               <RouterLink :to="{ name: 'config-ident', params: { dictId: activeDictionary.dictId } }">Description</RouterLink>
            </li>
            <li>
               <RouterLink :to="{ name: 'config-users', params: { dictId: activeDictionary.dictId } }">Users</RouterLink>
            </li>
            <li>
               <RouterLink :to="{ name: 'config-publico', params: { dictId: activeDictionary.dictId } }">Publishing</RouterLink>
            </li>
            <li>
               <RouterLink :to="{ name: 'config-url', params: { dictId: activeDictionary.dictId } }">Change URL</RouterLink>
            </li>
         </ul>
      </div>
      <div>
         <h3 class="header">Entry settings</h3>
         <ul>
            <li>
               <RouterLink :to="{ name: 'config-xema', params: { dictId: activeDictionary.dictId } }">Structure</RouterLink>
            </li>
            <li>
               <RouterLink :to="{ name: 'config-xemplate', params: { dictId: activeDictionary.dictId } }">Formatting</RouterLink>
            </li>
            <li>
               <RouterLink :to="{ name: 'config-titling', params: { dictId: activeDictionary.dictId } }">Headword list</RouterLink>
            </li>
            <li>
               <RouterLink :to="{ name: 'config-searchability', params: { dictId: activeDictionary.dictId } }">Searching</RouterLink>
            </li>
         </ul>
      </div>
      <div style="margin-right: auto;">
         <h3 class="header">Expert settings</h3>
         <ul>
            <li>
               <RouterLink :to="{ name: 'config-editing', params: { dictId: activeDictionary.dictId } }">Entry editor</RouterLink>
            </li>
            <li>
               <RouterLink :to="{ name: 'config-flagging', params: { dictId: activeDictionary.dictId } }">Flags</RouterLink>
            </li>
            <li>
               <RouterLink :to="{ name: 'config-autonumber', params: { dictId: activeDictionary.dictId } }">Auto-numbering</RouterLink>
            </li>
            <li>
               <RouterLink :to="{ name: 'config-links', params: { dictId: activeDictionary.dictId } }">Linking</RouterLink>
            </li>
            <li>
               <RouterLink :to="{ name: 'config-download', params: { dictId: activeDictionary.dictId } }">Download settings</RouterLink>
            </li>
            <li>
               <RouterLink :to="{ name: 'config-subbing', params: { dictId: activeDictionary.dictId } }">Subentries</RouterLink>
            </li>
         </ul>
      </div>
   </div>

</dict-config>
</template>

<script>
import Materialize from '../libs/materialize/materialize.min.js'
import { activeDictionary } from '../js/dictionary-workspace.ts'
import DictNav from './dict-nav.vue'
import { api } from '../js/api.ts'

export default {
   setup: () => ({ activeDictionary }),
   components: { DictNav },
   data() {
      return {
         state: {
            stats: {},
            isResaving: false,
            resaveProgressMessage: '',
         }
      }
   },

   async mounted() {
      this.state.stats = await api.get(`${encodeURIComponent(this.activeDictionary.dictId)}/stats.json`).catch(() => ({}))
   },

   unmounted() {
      this.state.isResaving = false
   },

   methods: {
      async resave() {
         if (this.state.isResaving) return
         const path = `${encodeURIComponent(this.activeDictionary.dictId)}/resave.json`
         this.state.isResaving = true
         try {
            while (this.state.isResaving) {
               const {progressMessage, finished} = await api.post(path)
               if (finished) {
                  this.state.stats = {needUpdate: 0}
                  return
               }
               this.state.resaveProgressMessage = progressMessage
            }
         } catch {
            Materialize.toast({ html: 'Re-indexing stopped. Try again to resume.' })
         } finally {
            this.state.isResaving = false
         }
      }
   }
}
</script>

<style>
dict-config .columnContainer{
   display: flex;
   gap: 4vw;
   justify-content: space-between;
   margin: auto;
}
dict-config li{
   padding: 0 0 0.7rem 0.7rem;
}
</style>
