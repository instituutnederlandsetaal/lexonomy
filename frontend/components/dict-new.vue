<template>
<dict-new>
   <LoadingOverlay v-if="state.isLoading"/>
   <div class="col s12 m8 offset-m2">
      <h3 style="border-bottom: 2px solid #004494;">
         Create a dictionary
      </h3>
      <div class="newBox">
      <div class="row">
         <div class="input-field">
            <input id="title" v-model="state.title"
            type="text"
            class="validate inlineBlock"
            required/>
            <label for="title">Title</label>
            <span class="helper-text">Enter a human-readable title such as "My Esperanto Dictionary". You will be able to change this later.</span>
         </div>
      </div>
      <div>
         <label for="url">URL</label>
      </div>

      <div class="row">
         <div style="display: flex; align-items: baseline;">
            <span class="grey-text">{{ state.baseUrl }}</span>
            <span class="input-field"
            style="margin-top: 0;">
            <input id="url"
            type="text"
            class="validate inlineBlock"
            v-model="state.url"
                  required
            minlength="5"
            pattern="[a-zA-Z0-9\-_]*"/>
            <span class="helper-text">This will be your dictionary's address on the web. You will be able to change this later. Allowed:  letters, numbers, - and _</span>
         </span>
      </div>
   </div>
   <div>
   </div>
   <div class="input-field">
      <div >
         <select id="template" ref="dictTemplate">
            <option value="blank">(none)</option>
            <option value="smd">Simple Monolingual Dictionary</option>
            <option value="sbd">Simple Bilingual Dictionary</option>
         </select>
      </div>
      <label>Template</label>
      <span class="helper-text">You can choose a template here to start you off. Each template comes with a few sample entries. You will be able to change or delete those and to customize the template.</span>
   </div>
   <div v-if="state.errorMessage != ''"
         class="section">
   <div class="message messageError">
      {{ state.errorMessage }}
   </div>
   </div>
   <div class="buttons">
      <button class="btn waves-effect waves-light" style="margin-left: auto" name="makeDict" id="makeButton" @click="doMake">Create
      </button>
   </div>
   </div>
   </div>
</dict-new>
</template>

<script>
import Materialize from '../libs/materialize/materialize.min.js'
import LoadingOverlay from './loading-overlay.vue'
import { api, basePath } from '../js/api.ts'
import { loadMyDictionaries } from '../js/my-dictionaries.ts'

export default {
   components: { LoadingOverlay },
   data() {
      return {
         state: {
            isLoading: true,
            errorMessage: '',
            url: '',
            title: '',
            baseUrl: location.origin + basePath
         }
      }
   },

   async mounted() {
      try {
         const { suggested, baseUrl } = await api.get('makesuggest.json')
         Object.assign(this.state, { url: suggested, baseUrl })
      } catch {
         this.state.errorMessage = 'Could not suggest a dictionary URL.'
      }
      this.state.isLoading = false
      await this.$nextTick()
      if (this.$refs.dictTemplate) {
         Materialize.updateTextFields()
         Materialize.FormSelect.init(this.$refs.dictTemplate)
      }
   },

   beforeUnmount() {
      Materialize.FormSelect.getInstance(this.$refs.dictTemplate)?.destroy()
   },

   methods: {
      async doMake() {
         if (!this.state.title || this.state.isLoading) return
         this.state.isLoading = true
         try {
            const response = await api.post('make.json', {
               url: this.state.url,
               template: this.$refs.dictTemplate.value,
               title: this.state.title
            })
            if (response.success) {
               loadMyDictionaries()
               this.$router.push({ name: 'dictionary', params: { dictId: response.url } })
            } else {
               this.state.errorMessage = 'Selected URL is already taken.'
            }
         } catch {
            this.state.errorMessage = 'Could not create the dictionary.'
         } finally {
            this.state.isLoading = false
         }
      }
   }
}
</script>

<style>
dict-new .newBox {
   padding: 1em;
   background: #FFFFFF;
   box-shadow: 0px 0px 0px rgba(19, 19, 151, 0.2);
   border-radius: 8px;
}
dict-new .newBox label {
   color: #000000 !important;
   font-weight: 500;
}
dict-new .newBox input {
   border: 1px solid #c7d0dd !important;
   outline: unset !important;
   border-radius: 4px !important;
}
</style>
