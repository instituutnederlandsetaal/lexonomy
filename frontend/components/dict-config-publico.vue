<template>
<dict-config-publico>
   <LoadingOverlay v-if="state.isLoading || state.isSaving"/>
   <DictNav :links="[['config', 'Configure'], ['config-publico', 'Publishing']]"/>
   <h1>Publishing</h1>
   <template v-if="!state.isLoading">
      <DictConfigButtons :save-data="saveData"></DictConfigButtons>
      <div class="row">
         <div class="input-field">
            <p>
               <label>
                  <input name="publico_public"
                        type="radio"
                        class="with-gap"
                        value="0"
                        :checked="!state.data.public"
                        @change="onCheckboxChange"/>
                  <span>Private</span>
               </label>
               <label style="margin-left: 30px;">
                  <input name="publico_public"
                        type="radio"
                        class="with-gap"
                        value="1"
                        :checked="state.data.public"
                        @change="onCheckboxChange" />
                  <span>Public</span>
               </label>
            </p>
            <span class="helper-text">
               <i>Private</i> means that the dictionary is not publicly viewable. <i>Public</i> means that the dictionary is publicly viewable.
            </span>
         </div>
      </div>
      <div v-if="state.data.public"
            class="row">
         <div class="input-field"
               id="publico_licence_info"
               style="max-width: 500px;">
            <select id="publico_licence" v-model="state.data.licence">
               <option v-for="licence in licences" :key="licence.id" :value="licence.id">{{ licence.title }}</option>
            </select>
            <label>Licence</label>
            <span v-if="licenceUrl" class="helper-text">
               More information about this licence: <a :href="licenceUrl" target="_blank" rel="noopener">{{ licenceUrl }}</a>.
            </span>
         </div>
      </div>
   </template>

</dict-config-publico>
</template>

<script>
import { dictionaryWorkspace } from '../js/dictionary-workspace.ts'
import DictConfigButtons from './dict-config-buttons.vue'
import DictNav from './dict-nav.vue'
import LoadingOverlay from './loading-overlay.vue'
import { materializeSelects } from './form-select.js'
export default {
   components: { DictConfigButtons, DictNav, LoadingOverlay },
   mixins: [materializeSelects],

   data() {
      return {
         state: {
            isLoading: true,
            isSaving: false,
            data: {}
         },
         licences: [
            {
               id: 'cc-by-4.0',
               title: 'Creative Commons Attribution 4.0 International',
               url: 'https://creativecommons.org/licenses/by/4.0/'
            },
            {
               id: 'cc-by-sa-4.0',
               title: 'Creative Commons Attribution Share-Alike 4.0 International',
               url: 'https://creativecommons.org/licenses/by-sa/4.0/'
            },
            {
               id: 'odbl-1.0',
               title: 'Open Database Licence 1.0',
               url: 'https://opendatacommons.org/licenses/odbl/summary/'
            }
         ]
      }
   },

   async mounted() {
      const response = await dictionaryWorkspace.loadDictionaryConfig('publico')
      if (response) {
         this.state.data = response.content
      }
      this.state.isLoading = false
   },

   computed: {
      licenceUrl() {
         return this.licences.find(licence => licence.id === this.state.data.licence)?.url
      }
   },

   methods: {
      onCheckboxChange(event) {
         this.state.data.public = event.target.value === '1'
         this.state.data.licence = this.state.data.public ? 'cc-by-4.0' : ''
      },

      async saveData() {
         this.state.isSaving = true
         await dictionaryWorkspace.updateDictionaryConfig("publico", this.state.data)
         this.state.isSaving = false
      }
   }
}
</script>
