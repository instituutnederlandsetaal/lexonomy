<template>
<div class="dict-config-searchability">
   <LoadingOverlay v-if="loading || saving"/>
   <DictNav :links="[['config', 'Configure'], ['config-searchability', 'Searching']]"/>
   <h1>Searching</h1>
   <DictConfigButtons :dict-id="dictId" :save-data="saveData" :disabled="saving || !ready"
         :show-save="elements.length > 0"></DictConfigButtons>
   <div v-if="ready && !elements.length"
         class="center-align grey-text">
      <h1>No elements found</h1>
   </div>
   <div v-if="ready && elements.length > 0">
      <h2 class="flow-text">Searchable elements</h2>
      <div class="helper-text">
         The contents of elements you select here will be searchable (in addition to each entry's headword).
      </div>
      <br>
      <div v-for="element in elements" :key="element">
         <label>
            <input type="checkbox"
                  :value="element"
                  v-model="draft.searchableElements"
                  :disabled="element === headword || saving"/>
            <span>{{ element }}</span>
         </label>
      </div>
   </div>
   <br><br>
   <p v-if="!loading && !ready">Settings could not be loaded. <button class="btn-flat" type="button" @click="load">Retry</button></p>
</div>
</template>

<script setup lang="ts">
import { useDictionarySetting } from '../js/use-dictionary-setting.ts'
import DictConfigButtons from './dict-config-buttons.vue'
import DictNav from './dict-nav.vue'
import LoadingOverlay from './loading-overlay.vue'
import { computed, ref } from 'vue'
import { activeDictionary } from '../js/dictionary-workspace.ts'

const props = defineProps<{ dictId: string }>()
const draft = ref({ searchableElements: [] as string[] })
const { loading, ready, saving, load, save } = useDictionarySetting(() => props.dictId, 'searchability', content => {
   draft.value.searchableElements = content.searchableElements ?? []
})
const elements = computed(() => Object.keys(activeDictionary.config?.xema.elements ?? {}))
const headword = computed(() => activeDictionary.config?.titling.headword)
const saveData = () => save(draft.value)
</script>
