<template>
<dict-config-download>
   <LoadingOverlay v-if="state.isLoading || state.isSaving"/>
   <DictNav :links="[['config', 'Configure'], ['config-download', 'Download settings']]"/>
   <h1>Download settings</h1>
   <DictConfigButtons :save-data="saveData"></DictConfigButtons>
   <div class="row">
      <div class="input-field">
         <textarea id="download_xslt"
               class="materialize-textarea" v-model="state.data.xslt"></textarea>
         <label for="download_xslt">XSLT transformation on download</label>
         <span class="helper-text">You can use this functionality to automatically apply an XSLT transformation when the dictionary is downloaded. If you do not input valid XSLT here, no transformation will be applied.</span>
      </div>
   </div>
</dict-config-download>
</template>

<script>
import Materialize from '../libs/materialize/materialize.min.js'
import { dictionaryWorkspace } from '../js/dictionary-workspace.ts'
import { parseXml } from '../js/xml.js'
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
            data: {xslt: ''}
         }
      }
   },

   async mounted() {
      const response = await dictionaryWorkspace.loadDictionaryConfig('download')
      if (response) {
         this.state.data = response.content
      }
      this.state.isLoading = false
      await this.$nextTick()
      Materialize.updateTextFields()
      if (this.$el.isConnected) Materialize.textareaAutoResize(this.$el.querySelector('#download_xslt'))
   },

   methods: {
      async saveData() {
         const xslt = this.state.data.xslt
         if (xslt && !parseXml(xslt)) {
            Materialize.toast({html: 'Failed to parse XSLT'})
            return
         }
         this.state.isSaving = true
         await dictionaryWorkspace.updateDictionaryConfig('download', {xslt})
         this.state.isSaving = false
      }
   }
}
</script>
