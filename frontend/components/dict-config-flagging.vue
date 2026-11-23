<template>
<div class="dict-config-flagging">
   <LoadingOverlay v-if="loading || saving"/>
   <DictNav :links="[['config', 'Configure'], ['config-flagging', 'Entry flags']]"/>
   <h1>Entry flags</h1>
   <DictConfigButtons :dict-id="dictId" :save-data="saveData" :disabled="saving || !ready"/>
   <div v-if="ready" class="config-form">
      <div v-if="draft.flags.length" class="flag-table">
         <table aria-label="Entry flags">
            <thead>
               <tr>
                  <th scope="col">Keyboard shortcut</th>
                  <th scope="col">Value</th>
                  <th scope="col">Label</th>
                  <th scope="col">Color</th>
                  <th scope="col"></th>
               </tr>
            </thead>
            <tbody>
               <tr v-for="(flag, index) in draft.flags" :key="index">
                  <td><input type="text" v-model="flag.key" aria-label="Keyboard shortcut"/></td>
                  <td><input type="text" v-model="flag.name" aria-label="Flag value"/></td>
                  <td><input type="text" v-model="flag.label" aria-label="Flag label"/></td>
                  <td>
                     <div class="config-control-row">
                        <input type="text" v-model="flag.color" aria-label="Flag color"/>
                        <input type="color" aria-label="Choose flag color"
                           :value="flag.color?.match(/^(#[0-9a-f]{6})(?:[0-9a-f]{2})?$/i)?.[1] ?? '#000000'"
                           @input="setColor(index, $event)"/>
                     </div>
                  </td>
                  <td>
                     <button type="button" class="btn btn-flat" aria-label="Delete flag" @click="draft.flags.splice(index, 1)">
                        <i class="material-symbols-outlined">delete</i>
                     </button>
                  </td>
               </tr>
            </tbody>
         </table>
      </div>
      <p v-else>No entry flags configured.</p>
      <button type="button" class="btn waves-effect waves-light" @click="addFlag" :disabled="!flagOptions.length || saving">
         Add flag
         <i class="material-symbols-outlined right">add</i>
      </button>
      <div v-if="draft.flags.length" class="config-field">
         <label for="flag-element">Flag element</label>
         <FormSelect id="flag-element" v-model="draft.flag_element" :options="flagOptions"
            aria-describedby="flag-element-help"/>
         <span id="flag-element-help" class="helper-text">Select the element that stores the flag in each entry.</span>
      </div>
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
import '../css/dict-config-form.css'
import FormSelect from './FormSelect.vue'

const props = defineProps<{ dictId: string }>()
const draft = ref<DictionarySettings['flagging']>({ flag_element: '', flags: [] })
const { loading, ready, saving, load, save } = useDictionarySetting(() => props.dictId, 'flagging', content => {
   draft.value = { flag_element: content.flag_element ?? '', flags: content.flags ?? [] }
})
const xema = computed(() => activeDictionary.config?.xema)
const flagElements = computed(() => Object.keys(xema.value?.elements ?? {}).filter(id => id !== xema.value?.root))
const flagOptions = computed(() => [...new Set([draft.value.flag_element, ...flagElements.value])]
   .filter(Boolean).map(value => ({ value, label: xema.value?.elements[value]?.elementName || value })))

function setColor(index: number, event: Event) {
   if (event.target instanceof HTMLInputElement) draft.value.flags[index].color = event.target.value
}

function addFlag() {
   draft.value.flag_element ||= flagElements.value[0] ?? ''
   draft.value.flags.push({ key: '', name: '', label: '', color: '' })
}

function saveData() {
   return save(draft.value)
}
</script>

<style scoped>
.flag-table {
   overflow-x: auto;
}
.flag-table table {
   min-width: 35rem;
}
tr {
   border-bottom: 0;
}
th, td {
   padding: 0 .65rem .5rem 0;
}
th:last-child, td:last-child {
   padding-right: 0;
   width: 1%;
}
td input[type="text"] {
   height: 2.5rem;
   margin: 0;
}
td input[type="color"] {
   flex: none;
   width: 2.5rem;
   height: 2.5rem;
   padding: 2px;
   cursor: pointer;
}
.flag-table + .btn {
   margin-top: .25rem;
}
</style>
