<template>
<dict-config-ident>
   <LoadingOverlay v-if="state.isLoading || state.isSaving"/>
   <DictNav :links="[['config', 'Configure'], ['config-ident', 'Description']]"/>
   <h1>Description</h1>
   <div>
      <form>
         <DictConfigButtons :save-data="saveData"></DictConfigButtons>
         <div class="row">
            <div class="input-field">
               <input v-model="state.data.title"
                     placeholder="My Dictionary"
                     id="ident_title"
                     type="text"
                     class="validate"
                     style="width:300px" />
               <label for="ident_title">Dictionary name</label>
               <span class="helper-text">A human-readable title for your dictionary, such as <i>My Esperanto Dictionary</i>.</span>
            </div>
         </div>
         <div class="row">
            <div class="input-field">
               <textarea id="ident_blurb"
                     class="materialize-textarea"
                     placeholder="Yet another Lexonomy dictionary."
                     rows="3" v-model="state.data.blurb"></textarea>
               <label for="ident_blurb">Dictionary description</label>
               <span class="helper-text">
                  This will appear on your dictionary's home page. You can leave it blank if you prefer.<br/>You can use <a href='https://daringfireball.net/projects/markdown/' target='_blank'>Markdown</a> here.
               </span>
            </div>
         </div>
         <div class="row">
            <div class="input-field">
               <input v-model="state.data.lang"
                     type="text"
                     id="ident_lang"
                     ref="language"
                     class="autocomplete"
                     placeholder="Type to search for language, or write your custom info"
                     style="width:300px">
               <label for="ident_lang">Main language</label>
               <span class="helper-text">Language of dictionary entries, used to sort dictionaries on your home page. You can select language from the list, or write down your own.</span>
            </div>
         </div>
         <div class="row">
            <div class="input-field">
               <input v-model="state.data.handle"
                     placeholder="URL"
                     id="ident_handle"
                     type="text"
                     class="validate"/>
               <label for="ident_title">Metadata from CLARIN repository</label>
               <span class="helper-text">Link to metadata recorded in CLARIN repository, provide URL to 'handle' link, eg. <code>http://hdl.handle.net/11356/1094</code>.</span>
            </div>
         </div>
      </form>
   </div>
</dict-config-ident>
</template>

<script>
import Materialize from '../libs/materialize/materialize.min.js'
import { dictionaryWorkspace } from '../js/dictionary-workspace.ts'
import { loadMyDictionaries } from '../js/my-dictionaries.ts'
import DictConfigButtons from './dict-config-buttons.vue'
import DictNav from './dict-nav.vue'
import LoadingOverlay from './loading-overlay.vue'
export default {
   components: { DictConfigButtons, DictNav, LoadingOverlay },
   data() {
      return {
         state: {
            isLoading: true,
            isSaving: false,
            data: {}
         }
      }
   },

   async mounted() {
      const response = await dictionaryWorkspace.loadDictionaryConfig('ident')
      if (response) {
         this.state.data = response.content
      }
      this.state.isLoading = false
      await this.$nextTick()
      if (!this.$refs.language) return
      Materialize.updateTextFields()
      Materialize.textareaAutoResize(this.$el.querySelector('#ident_blurb'))
      if (this.state.data.langs) {
         const data = Object.fromEntries(this.state.data.langs.map(language => [language.lang, null]))
         Materialize.Autocomplete.init(this.$refs.language, {
            data, onAutocomplete: lang => { this.state.data.lang = lang }
         })
      }
   },

   beforeUnmount() {
      Materialize.Autocomplete.getInstance(this.$refs.language)?.destroy()
   },

   methods: {
      async saveData() {
         this.state.isSaving = true
         const { title = '', blurb = '', lang = '', handle = '' } = this.state.data
         const response = await dictionaryWorkspace.updateDictionaryConfig("ident", { title, blurb, lang, handle })
         if (response?.success) loadMyDictionaries()
         this.state.isSaving = false
      }
   }
}
</script>
