<template>
<dict-config-url>
   <LoadingOverlay v-if="state.isSaving"/>
   <DictNav :links="[['config', 'Configure'], ['config-url', 'Change URL']]"/>
   <h1>Change URL</h1>
   <DictConfigButtons :save-data="saveData"
         label="Change"></DictConfigButtons>
   <div class="row">
      <label for="url">Current URL</label>
      <div style="margin: 0 0 30px;">
         <span>{{ baseUrl }}{{ activeDictionary.dictId }}</span>
      </div>
   </div>
   <div class="row">
      <label for="url">New URL</label>
      <div>
         <div style="display: flex; align-items: baseline;">
            <span id="baseUrl">{{ baseUrl }}</span>
            <span>
               <input id="url"
                     ref="url"
                     v-model="newUrl"
                     type="text"
                     class="validate inlineBlock"
                     required
                     minlength="5"
                     pattern="[a-zA-Z0-9\-_]*"
                     style="max-width: 300px;"/>
            </span>
         </div>
         <div class="input-field"
               style="margin-top: 0;">
            <span class="helper-text">This will be your dictionary's address on the web. Minimum length: 5 characters. Allowed: letters, numbers, - and _</span>
         </div>
      </div>
   </div>
   <br>
   <div>
      <span v-if="moveResult === false" id="error">This URL is already taken.</span>
      <span v-if="moveResult === true" id="success">
      <b>Your dictionary has been moved to a new URL.</b>
      <RouterLink class="btn waves-effect waves-light" :to="{ name: 'dictionary', params: { dictId: movedUrl } }" id="newlink">
         Go to new dictionary URL
      <i class="material-symbols-outlined right">trending_flat</i>
   </RouterLink>
      </span>
   </div>
</dict-config-url>
</template>

<script>
import Materialize from '../libs/materialize/materialize.min.js'
import { siteSettings } from '../js/site-settings.ts'
import { activeDictionary } from '../js/dictionary-workspace.ts'
import DictConfigButtons from './dict-config-buttons.vue'
import DictNav from './dict-nav.vue'
import LoadingOverlay from './loading-overlay.vue'
import { api, basePath } from '../js/api.ts'

export default {
   setup: () => ({ activeDictionary }),
   components: { DictConfigButtons, DictNav, LoadingOverlay },
   data() {
      return {
         state: { isSaving: false },
         newUrl: '',
         movedUrl: '',
         moveResult: null
      }
   },

   computed: {
      baseUrl() {
         return siteSettings.value?.baseUrl || location.origin + basePath
      }
   },

   methods: {
      async saveData() {
         if (this.state.isSaving || !this.$refs.url.reportValidity()) return
         const url = this.newUrl
         this.state.isSaving = true
         try {
            const { success } = await api.post(`${encodeURIComponent(this.activeDictionary.dictId)}/move.json`, { url })
            this.moveResult = success
            if (success) this.movedUrl = url
         } catch {
            Materialize.toast({ html: 'Could not change the dictionary URL.' })
         } finally {
            this.state.isSaving = false
         }
      }
   }
}
</script>
