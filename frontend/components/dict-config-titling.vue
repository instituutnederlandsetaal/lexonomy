<template>
<dict-config-titling>
   <LoadingOverlay v-if="state.isLoading || state.isSaving"/>
   <DictNav :links="[['config', 'Configure'], ['config-titling', 'Headword list']]"/>
   <h1>Headword</h1>
   <DictConfigButtons :save-data="saveData"></DictConfigButtons>
   <div class="row">
      <div class="input-field col s6">
         <select id="headword" v-model="state.data.headword">
            <option value="">(not set)</option>
            <option v-for="name in elements" :key="name" :value="name">{{ name }}</option>
         </select>
         <label for="headword">Headword</label>
         <span class="helper-text">Select the element which contains the entry's headword. If you make no selection here Lexonomy will try to guess what the headword of each entry is.</span>
      </div>
   </div>
   <div class="row">
      <div class="input-field col s6">
         <select id="headwordSorting" v-model="state.data.headwordSorting">
            <option value="">(not set)</option>
            <option v-for="name in elements" :key="name" :value="name">{{ name }}</option>
         </select>
         <label for="headwordSorting">Headword sorting</label>
         <span class="helper-text">Select the element which will be used for sorting of headwords in the entry list. If you make no selection here Lexonomy will use the element you chose for headword.</span>
      </div>
      <div class="input-field col s6">
         <label style="padding-top: 30px;">
            <input type="checkbox"
                  id="sortDesc"
                  v-model="state.data.sortDesc"/>
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
                  v-model="state.data.headwordAnnotationsType"/>
            <span>simple</span>
         </label>
         <br/>
         <div class="input-field">
            <select id="headwordAnnotations" v-model="state.data.headwordAnnotations"
                  multiple
                  :disabled="state.data.headwordAnnotationsType === 'advanced'">
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
                  v-model="state.data.headwordAnnotationsType"/>
            <span>advanced</span>
         </label>
         <br/>
         <div class="input-field">
            <textarea id="advancedAnnotations"
                  class="materialize-textarea"
                  placeholder="headword annotations"
                  :disabled="state.data.headwordAnnotationsType == 'simple'" v-model="state.data.headwordAnnotationsAdvanced"></textarea>
            <span class="helper-text">You can insert any HTML containing placeholders for elements in the form of '%(element)', e.g. '&lt;b>%(headword)&lt;/b>'.</span>
         </div>
      </div>
   </div>
   <div class="row">
      <div class="input-field col s8">
         <input ref="locale" v-model="localeName"
               type="text" id="sort_locale"
               class="autocomplete"
               placeholder="Type to search for language"/>
         <label for="sort_locale">Alphabetical order</label>
         <span class="helper-text">Select language to sort entries alphabetically in the entry list.</span>
      </div>
   </div>
   <div class="row">
      <div class="input-field col s6">
         <input v-model="state.data.numberEntries"
               id="numberEntries"
               type="number" />
         <label for="numberEntries">Number of entries to be shown in the entry list at once</label>
         <span class="helper-text">If your dictionary contains large entries (large XML files), it is recommended to reduce this number for quicker loading of entry list.</span>
      </div>
   </div>
</dict-config-titling>
</template>

<script>
import Materialize from '../libs/materialize/materialize.min.js'
import { activeDictionary, dictionaryWorkspace } from '../js/dictionary-workspace.ts'
import DictConfigButtons from './dict-config-buttons.vue'
import DictNav from './dict-nav.vue'
import LoadingOverlay from './loading-overlay.vue'
import { materializeSelects } from './form-select.js'
export default {
   setup: () => ({ activeDictionary }),
   components: { DictConfigButtons, DictNav, LoadingOverlay },
   mixins: [materializeSelects],

   data() {
      return {
         localeName: '',
         state: {
            isLoading: true,
            isSaving: false,
            data: {
               headwordAnnotationsType: 'simple',
               headwordAnnotations: []
            }
         }
      }
   },

   async mounted() {
      const response = await dictionaryWorkspace.loadDictionaryConfig('titling')
      if (response) {
         const config = response.content
         this.state.data = {
            ...config,
            numberEntries: config.numberEntries || 1000,
            headwordAnnotationsType: config.headwordAnnotationsType || 'simple',
            headwordAnnotations: config.headwordAnnotations || []
         }
         this.localeName = config.locales?.find(locale => locale.code === (config.locale || config.sort_locale))?.lang || ''
      }
      this.state.isLoading = false
      await this.$nextTick()
      if (!this.$refs.locale) return
      Materialize.updateTextFields()
      Materialize.textareaAutoResize(this.$el.querySelector('#advancedAnnotations'))
      Materialize.Autocomplete.init(this.$refs.locale, {
         data: Object.fromEntries((this.state.data.locales || []).map(locale => [locale.lang, null])),
         onAutocomplete: name => { this.localeName = name }
      })
   },

   beforeUnmount() {
      Materialize.Autocomplete.getInstance(this.$refs.locale)?.destroy()
   },

   computed: {
      elements() {
         return Object.keys(this.activeDictionary.config?.xema?.elements || {})
      },
      annotationOptions() {
         return this.elements.filter(name => name !== this.state.data.headword)
      }
   },

   methods: {
      async saveData() {
         const { locales, sort_locale, ...config } = this.state.data
         config.locale = (locales || []).find(locale => locale.lang === this.localeName)?.code || ''
         this.state.isSaving = true
         await dictionaryWorkspace.updateDictionaryConfig('titling', config)
         this.state.isSaving = false
      }
   }
}
</script>
