<template>
<div class="dict-config-flagging">
   <LoadingOverlay v-if="loading || saving"/>
   <DictNav :links="[['config', 'Configure'], ['config-flagging', 'Entry flags']]"/>
   <h1>Entry flags</h1>
   <DictConfigButtons :dict-id="dictId" :save-data="saveData" :disabled="saving || !ready"></DictConfigButtons>
   <template v-if="ready">
      <div v-if="!draft.flags.length"
            class="center-align grey-text">
         <h1>no entry flags</h1>
         <br>
         <button type="button" class="btn btn-primary waves-effect waves-light"
               @click="addFlag" :disabled="!flagOptions.length || saving">
            add flag
            <i class="material-symbols-outlined right">add</i>
         </button>
      </div>

      <template v-if="draft.flags.length">
         <table>
            <thead>
               <tr>
                  <th>Keyboard shortcut</th>
                  <th>Value</th>
                  <th>Label</th>
                  <th>Color</th>
                  <th></th>
               </tr>
            </thead>
            <tbody>
               <tr v-for="(flag, index) in draft.flags" :key="index">
                  <td>
                     <input type="text"
                           v-model="flag.key"
                           placeholder="key"/>
                  </td>
                  <td>
                     <input type="text"
                           v-model="flag.name"
                           placeholder="value"/>
                  </td>
                  <td>
                     <input type="text"
                           v-model="flag.label"
                           placeholder="label"/>
                  </td>
                  <td>
                     <input type="text"
                           v-model="flag.color"
                           placeholder="color"
                           :style="{ color: flagTextColor(flag.color), backgroundColor: flag.color }"/>
                     <input type="color" aria-label="Choose flag color"
                           :value="/^#[a-f0-9]{6}$/i.test(flag.color) ? flag.color : '#000000'"
                           @input="setColor(index, $event)"/>
                  </td>
                  <td>
                     <button type="button" class="btn btn-flat"
                           aria-label="Delete flag" @click="draft.flags.splice(index, 1)">
                        <i class="material-symbols-outlined">delete</i>
                     </button>
                  </td>
               </tr>
            </tbody>
         </table>
         <div>
            <button type="button" class="btn waves-effect waves-light"
                  @click="addFlag" :disabled="!flagOptions.length || saving">
               add flag
               <i class="material-symbols-outlined right">add</i>
            </button>
         </div>
         <br>
         <br>
         <div class="input-field"
               style="max-width: 400px;">
            <FormSelect id="flag-element" v-model="draft.flag_element" :options="flagOptions" aria-label="Flag element"/>
            <span class="helper-text">Select the element which the flags should be put into.</span>
         </div>
      </template>
   </template>
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
import type { DictionarySettings } from '../js/dictionary-config-api.ts'
import { flagTextColor } from './entry-flags.js'
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

<style>
.dict-config-flagging tr{
   border-bottom: none;
}
.dict-config-flagging th, .dict-config-flagging td{
   padding: 3px 10px 3px 0;
}
</style>
