<template>
<dict-download>
   <DictNav :links="[['download', 'download']]"/>
   <h1>Download</h1>
   <div class="input-field">
      <a class="waves-effect waves-light btn btn-primary download-link"
            target="_blank" rel="noopener"
            :href="downloadUrl">
         <i class="material-symbols-outlined left">file_download</i>
         Download {{ activeDictionary.dictId }}.xml
      </a>
   </div>
   <div>
      <label>
         <input type="checkbox"
               class="noAttributes"
               name="noAttributes" v-model="clean"/>
         <span>XML without Lexonomy attributes</span>
      </label>
   </div>
   <small class="helper-text">
      If you want to import the XML file back to Lexonomy, you need Lexonomy attributes.
   </small>
</dict-download>
</template>

<script>
import { activeDictionary } from '../js/dictionary-workspace.ts'
import DictNav from './dict-nav.vue'
import { basePath } from '../js/api.ts'

export default {
   setup: () => ({ activeDictionary }),
   components: { DictNav },
   data() {
      return { clean: false }
   },

   computed: {
      downloadUrl() {
         return `${basePath}${encodeURIComponent(this.activeDictionary.dictId)}/download.xml${this.clean ? '?clean=true' : ''}`
      }
   }
}
</script>
