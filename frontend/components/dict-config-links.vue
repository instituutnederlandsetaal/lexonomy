<template>
<div class="dict-config-links">
   <LoadingOverlay v-if="loading || saving"/>
   <DictNav :links="[['config', 'Configure'], ['config-links', 'Linking']]"/>
   <h1>Manual linking between entries</h1>
   <DictConfigButtons :dict-id="dictId" :save-data="saveData" :disabled="saving || !ready"></DictConfigButtons>

   <div>
      <p>Elements listed here can be used as target of cross-reference link. For each element, specify unique identifier in the form of placeholders <code>'%(element)'</code>. Eg. element <code>entry</code> can have identifier <code>%(lemma)-%(pos)</code>, element <code>sense</code> can have identifier <code>%(lemma)-%(number)</code>. Optionally, specify element you want to show as preview when selecting links.</p>
      <template v-if="ready">
         <table v-if="links.length">
            <thead>
               <tr>
                  <th>Linking element</th>
                  <th>Identifier</th>
                  <th>Preview</th>
                  <th></th>
               </tr>
            </thead>
            <tbody>
               <tr v-for="(element, index) in links" :key="index">
                  <td>
                     <div class="input-field">
                        <FormSelect v-model="element.linkElement" :options="[element.linkElement, ...unusedElements].map(value => ({ value, label: value }))"
                           :aria-label="`Linking element for row ${index + 1}`"/>
                     </div>
                  </td>
                  <td>
                     <div class="input-field">
                        <input type="text"
                              name="identifier" v-model="element.identifier" />
                     </div>
                  </td>
                  <td>
                     <div class="input-field">
                        <input type="text"
                              name="preview" v-model="element.preview"/>
                     </div>
                  </td>
                  <td>
                     <button type="button" class="btn btn-floating right"
                           aria-label="Delete linking element" @click="links.splice(index, 1)">
                        <i class="material-symbols-outlined">delete</i>
                     </button>
                  </td>
               </tr>
            </tbody>
         </table>
         <div class="buttons">
            <button type="button" class="btn" :disabled="!unusedElements.length"
                  @click="addLink">
               add element
               <i class="material-symbols-outlined right">add</i>
            </button>
         </div>
      </template>
   </div>
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
import type { DictionarySettings } from '../js/dictionary-config-api.ts'
import FormSelect from './FormSelect.vue'

type Link = DictionarySettings['links'][string]
const props = defineProps<{ dictId: string }>()
const links = ref<Link[]>([])
const { loading, ready, saving, load, save } = useDictionarySetting(() => props.dictId, 'links', content => {
   links.value = Object.values(content).filter(link => typeof link?.linkElement === 'string')
})
const unusedElements = computed(() => {
   const used = new Set(links.value.map(link => link.linkElement))
   return Object.keys(activeDictionary.config?.xema.elements ?? {}).filter(id => !used.has(id))
})

function addLink() {
   const linkElement = unusedElements.value[0]
   if (linkElement) links.value.push({ linkElement, identifier: '', preview: '' })
}

function saveData() {
   return save(Object.fromEntries(links.value.map(link => [link.linkElement, link])))
}
</script>

<style>
.dict-config-links tbody tr{
   border-bottom: none;
}
.dict-config-links th, .dict-config-links td{
   padding: 10px 10px 0 0;
}
.dict-config-links td{
   vertical-align: top;
}
.dict-config-links td .input-field{
   margin: 0;
}
</style>
