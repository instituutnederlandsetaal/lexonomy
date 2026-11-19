<template>
<dict-config-searchability>
   <LoadingOverlay v-if="state.isLoading || state.isSaving"/>
   <DictNav :links="[['config', 'Configure'], ['config-searchability', 'Searching']]"/>
   <h1>Searching</h1>
   <DictConfigButtons :save-data="saveData"
         :show-save="elements.length > 0"></DictConfigButtons>
   <div v-if="!state.isLoading && !elements.length"
         class="center-align grey-text">
      <h1>No elements found</h1>
   </div>
   <div v-if="!state.isLoading && elements.length > 0">
      <label for="search-element">Searchable elements</label>
      <div class="helper-text">
         The contents of elements you select here will be searchable (in addition to each entry's headword).
      </div>
      <br>
      <div v-for="element in elements" :key="element">
         <label>
            <input type="checkbox"
                  :value="element"
                  v-model="state.data.searchableElements"
                  :disabled="element === activeDictionary.config?.titling?.headword"/>
            <span>{{ element }}</span>
         </label>
      </div>
   </div>
   <br><br>
</dict-config-searchability>
</template>

<script>
import { activeDictionary, dictionaryWorkspace } from '../js/dictionary-workspace.ts'
import DictConfigButtons from './dict-config-buttons.vue'
import DictNav from './dict-nav.vue'
import LoadingOverlay from './loading-overlay.vue'
export default {
   setup: () => ({ activeDictionary }),
   components: { DictConfigButtons, DictNav, LoadingOverlay },
   data() {
      return {
         state: {
            isLoading: true,
            isSaving: false,
            data: {searchableElements: []}
         }
      }
   },

   computed: {
      elements() {
         return Object.keys(this.activeDictionary.config?.xema?.elements || {})
      }
   },

   async mounted() {
      const response = await dictionaryWorkspace.loadDictionaryConfig('searchability')
      if (response) {
         this.state.data.searchableElements = response.content?.searchableElements || []
      }
      this.state.isLoading = false
   },

   methods: {
      async saveData() {
         this.state.isSaving = true
         await dictionaryWorkspace.updateDictionaryConfig("searchability", this.state.data)
         this.state.isSaving = false
      }
   }
}
</script>
