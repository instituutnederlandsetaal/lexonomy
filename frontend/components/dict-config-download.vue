<template>
<div class="dict-config-download">
   <LoadingOverlay v-if="loading || saving"/>
   <DictNav :links="[['config', 'Configure'], ['config-download', 'Download settings']]"/>
   <h1>Download settings</h1>
   <DictConfigButtons :dict-id="dictId" :save-data="saveData" :disabled="saving || !ready"></DictConfigButtons>
   <div v-if="ready" class="row">
      <div class="input-field">
         <textarea id="download_xslt"
               class="materialize-textarea" rows="6" v-model="draft.xslt"></textarea>
         <label for="download_xslt" class="active">XSLT transformation on download</label>
         <span class="helper-text">You can use this functionality to automatically apply an XSLT transformation when the dictionary is downloaded. If you do not input valid XSLT here, no transformation will be applied.</span>
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
import { ref } from 'vue'
import Materialize from '../libs/materialize/materialize.min.js'
import { parseXml } from '../js/xml.ts'

const props = defineProps<{ dictId: string }>()
const draft = ref({ xslt: '' })
const { loading, ready, saving, load, save } = useDictionarySetting(() => props.dictId, 'download', content => {
   draft.value.xslt = content.xslt ?? ''
})

function saveData() {
   if (draft.value.xslt && !parseXml(draft.value.xslt)) {
      Materialize.toast({ html: 'Failed to parse XSLT' })
      return
   }
   return save(draft.value)
}
</script>
