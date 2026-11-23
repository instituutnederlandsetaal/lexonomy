<template>
<div class="dict-config-titling">
   <LoadingOverlay v-if="loading || saving"/>
   <DictNav :links="[['config', 'Configure'], ['config-titling', 'Headword list']]"/>
   <h1>Headword list</h1>
   <DictConfigButtons :dict-id="dictId" :save-data="saveData" :disabled="saving || !ready"/>
   <div v-if="ready" class="config-form">
      <section>
         <h2>Headword and sorting</h2>
         <div class="config-fields">
            <div class="config-field">
               <label for="headword">Headword element</label>
               <FormSelect id="headword" v-model="draft.headword" :options="options(draft.headword)" aria-describedby="headword-help"/>
               <span id="headword-help" class="helper-text">If unset, Lexonomy will try to find the headword in each entry.</span>
            </div>
            <div class="config-field">
               <label for="headwordSorting">Sort by element</label>
               <FormSelect id="headwordSorting" v-model="draft.headwordSorting" :options="options(draft.headwordSorting)"
                  aria-describedby="sort-element-help"/>
               <span id="sort-element-help" class="helper-text">If unset, entries are sorted by the headword element.</span>
            </div>
            <div class="config-field">
               <label for="sort_locale">Sort language</label>
               <FormSelect id="sort_locale" v-model="draft.locale" :options="locales"/>
            </div>
            <label class="sort-direction">
               <input type="checkbox" v-model="draft.sortDesc"/>
               <span>Sort in descending order</span>
            </label>
         </div>
      </section>

      <section>
         <h2>Headword annotations</h2>
         <div class="config-fields">
            <div class="config-field annotation">
               <label>
                  <input name="hwannotype" type="radio" value="simple" v-model="draft.headwordAnnotationsType"/>
                  <span>Simple</span>
               </label>
               <select id="headwordAnnotations" class="browser-default" multiple size="5"
                  aria-label="Annotation elements" aria-describedby="annotation-elements-help" v-model="draft.headwordAnnotations"
                  :disabled="draft.headwordAnnotationsType === 'advanced'">
                  <option v-for="name in annotationOptions" :key="name" :value="name">{{ name }}</option>
               </select>
               <span id="annotation-elements-help" class="helper-text">Select elements to display beside the headword, such as homograph numbers or part-of-speech labels.</span>
            </div>
            <div class="config-field annotation">
               <label>
                  <input name="hwannotype" type="radio" value="advanced" v-model="draft.headwordAnnotationsType"/>
                  <span>Advanced</span>
               </label>
               <textarea id="advancedAnnotations" class="materialize-textarea" v-model="draft.headwordAnnotationsAdvanced"
                  aria-label="Annotation HTML" aria-describedby="annotation-html-help" :disabled="draft.headwordAnnotationsType === 'simple'"/>
               <span id="annotation-html-help" class="helper-text">Enter HTML with element placeholders, for example <code>&lt;b&gt;%(headword)&lt;/b&gt;</code>.</span>
            </div>
         </div>
      </section>

      <section>
         <h2>Entry list</h2>
         <div class="config-field">
            <label for="numberEntries">Entries per page</label>
            <input v-model="draft.numberEntries" id="numberEntries" type="number" min="1" aria-describedby="entry-limit-help"/>
            <span id="entry-limit-help" class="helper-text">Use a smaller number to load the list faster when entries contain large XML documents.</span>
         </div>
      </section>
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
import Materialize from '../libs/materialize/materialize.min.js'
import FormSelect from './FormSelect.vue'
import '../css/dict-config-form.css'

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

<style scoped>
.sort-direction {
   align-self: center;
}
.config-field.annotation > :is(select, textarea) {
   min-height: 9rem;
   padding: .5rem;
}
.annotation textarea {
   resize: vertical;
}
#numberEntries {
   width: min(100%, 10rem);
}
</style>
