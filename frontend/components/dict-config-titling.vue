<template>
<div class="dict-config-titling">
   <LoadingOverlay v-if="loading || saving"/>
   <DictNav :links="[['config', 'Configure'], ['config-titling', 'Headword list']]"/>
   <h1>Headword</h1>
   <DictConfigButtons :dict-id="dictId" :save-data="saveData" :disabled="saving || !ready"></DictConfigButtons>
   <template v-if="ready">
      <div class="row">
         <div class="input-field col s6">
            <FormSelect id="headword" v-model="draft.headword" :options="options(draft.headword)" aria-label="Headword"/>
            <span class="helper-text">Select the element which contains the entry's headword. If you make no selection here Lexonomy will try to guess what the headword of each entry is.</span>
         </div>
      </div>
      <div class="row">
         <div class="input-field col s6">
            <FormSelect id="headwordSorting" v-model="draft.headwordSorting" :options="options(draft.headwordSorting)" aria-label="Headword sorting"/>
            <span class="helper-text">Select the element which will be used for sorting of headwords in the entry list. If you make no selection here Lexonomy will use the element you chose for headword.</span>
         </div>
         <div class="input-field col s6">
            <label style="padding-top: 30px;">
               <input type="checkbox"
                     id="sortDesc"
                     v-model="draft.sortDesc"/>
               <span>Sort in descending order</span>
            </label>
         </div>
      </div>
      <div class="row">
         <h4>Headword annotations</h4>
      </div>
      <div class="row">
         <div class="col s5">
            <label>
               <input name="hwannotype"
                     type="radio"
                     value="simple"
                     v-model="draft.headwordAnnotationsType"/>
               <span>simple</span>
            </label>
            <br/>
            <div class="input-field">
               <select id="headwordAnnotations" class="browser-default" aria-label="Headword annotations" v-model="draft.headwordAnnotations"
                     multiple
                     :disabled="draft.headwordAnnotationsType === 'advanced'">
                  <option v-for="name in annotationOptions" :key="name" :value="name">{{ name }}</option>
               </select>
               <span class="helper-text">You can select any elements here whose content you want displayed beside the headword in the entry list, such as homograph numbers or part-of-speech labels.</span>
            </div>
         </div>
         <div class="col s5">
            <label>
               <input name="hwannotype"
                     type="radio"
                     value="advanced"
                     v-model="draft.headwordAnnotationsType"/>
               <span>advanced</span>
            </label>
            <br/>
            <div class="input-field">
               <textarea id="advancedAnnotations"
                     class="materialize-textarea"
                     placeholder="headword annotations"
                     :disabled="draft.headwordAnnotationsType == 'simple'" v-model="draft.headwordAnnotationsAdvanced"></textarea>
               <span class="helper-text">You can insert any HTML containing placeholders for elements in the form of '%(element)', e.g. '&lt;b>%(headword)&lt;/b>'.</span>
            </div>
         </div>
      </div>
      <div class="row">
         <div class="input-field col s8">
            <FormSelect id="sort_locale" v-model="draft.locale" :options="locales" aria-label="Alphabetical order"/>
            <span class="helper-text">Select language to sort entries alphabetically in the entry list.</span>
         </div>
      </div>
      <div class="row">
         <div class="input-field col s6">
            <input v-model="draft.numberEntries"
                  id="numberEntries"
                  type="number" min="1" />
            <label for="numberEntries" class="active">Number of entries to be shown in the entry list at once</label>
            <span class="helper-text">If your dictionary contains large entries (large XML files), it is recommended to reduce this number for quicker loading of entry list.</span>
         </div>
      </div>
   </template>
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
import Materialize from '../libs/materialize/materialize.min.js'
import FormSelect from './FormSelect.vue'

const props = defineProps<{ dictId: string }>()
const defaults = { numberEntries: 1000, headword: '', headwordSorting: '', headwordAnnotationsType: 'simple' as const,
   headwordAnnotations: [] as string[], locale: '' }
const draft = ref<DictionarySettings['titling'] & { headwordAnnotations: string[] }>(defaults)
const { loading, ready, saving, load, save } = useDictionarySetting(() => props.dictId, 'titling', settings => {
   draft.value = { ...defaults, ...settings, numberEntries: settings.numberEntries || 1000,
      locale: settings.locale || settings.sort_locale || '', headwordAnnotations: settings.headwordAnnotations ?? [] }
})

const elementsById = computed(() => activeDictionary.config?.xema.elements ?? {})
const elements = computed(() => Object.keys(elementsById.value))
function options(current?: string) {
   return [{ value: '', label: '(not set)' }, ...[...new Set([...elements.value, ...(current ? [current] : [])])]
      .map(value => ({ value, label: elementsById.value[value]?.elementName || value }))]
}
const annotationOptions = computed(() => elements.value.filter(name => name !== draft.value.headword))
const locales = computed(() => {
   const options = (draft.value.locales ?? []).map(locale => ({ value: locale.code, label: locale.lang }))
   const code = draft.value.locale
   if (code && !options.some(option => option.value === code)) options.push({ value: code, label: code })
   return [{ value: '', label: '(not set)' }, ...options]
})

function saveData() {
   const { locales: _locales, sort_locale: _legacyLocale, ...settings } = draft.value
   if (!Number.isSafeInteger(settings.numberEntries) || Number(settings.numberEntries) < 1) {
      Materialize.toast({ html: 'Enter a positive whole number for the entry list size.' })
      return
   }
   settings.headwordAnnotations = settings.headwordAnnotations.filter(id => id !== settings.headword)
   return save(settings)
}
</script>
