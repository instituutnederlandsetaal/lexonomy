<template>
<div class="dict-new">
   <LoadingOverlay v-if="loading"/>
   <div class="col s12 m8 offset-m2">
      <h3 style="border-bottom: 2px solid #004494;">Create a dictionary</h3>
      <form class="newBox" @submit.prevent="submit">
         <div class="row">
            <div class="input-field">
               <input id="title" v-model.trim="title" type="text" class="validate inlineBlock" required>
               <label for="title">Title</label>
               <span class="helper-text">Enter a human-readable title such as "My Esperanto Dictionary". You will be able to change this later.</span>
            </div>
         </div>
         <label for="url">URL</label>
         <div class="row">
            <div class="url-input">
               <span class="grey-text">{{ baseUrl }}</span>
               <div class="input-field" style="margin-top: 0;">
                  <input id="url" v-model="url" type="text" class="validate inlineBlock"
                        required minlength="5" pattern="[a-zA-Z0-9_\-]+">
                  <span class="helper-text">This will be your dictionary's address on the web. You will be able to change this later. Allowed characters are letters, numbers, hyphens, and underscores.</span>
               </div>
            </div>
         </div>
         <div class="input-field">
            <label for="template">Template</label>
            <FormSelect id="template" v-model="template" :options="templates"/>
            <span class="helper-text">Each template comes with sample entries. You can edit or delete them and customize the template.</span>
         </div>
         <div v-if="errorMessage" class="section">
            <div class="message messageError" role="alert">{{ errorMessage }}</div>
         </div>
         <div class="buttons">
            <button id="makeButton" type="submit" class="btn waves-effect waves-light"
                  style="margin-left: auto" :disabled="loading">Create</button>
         </div>
      </form>
   </div>
</div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { pageUrl } from '../js/page-url.ts'
import { createDictionary, fetchDictionaryUrlSuggestion, type DictionaryTemplate } from '../js/public-dictionary-api.ts'
import { loadMyDictionaries } from '../js/my-dictionaries.ts'
import FormSelect from './FormSelect.vue'
import LoadingOverlay from './loading-overlay.vue'

const router = useRouter()
const loading = ref(true)
const errorMessage = ref('')
const url = ref('')
const title = ref('')
const baseUrl = new URL('#/', pageUrl).href
const template = ref<DictionaryTemplate>('blank')
const templates: { value: DictionaryTemplate; label: string }[] = [
   { value: 'blank', label: '(none)' },
   { value: 'smd', label: 'Simple Monolingual Dictionary' },
   { value: 'sbd', label: 'Simple Bilingual Dictionary' }
]

onMounted(async () => {
   try {
      const suggestion = await fetchDictionaryUrlSuggestion()
      if (!url.value) url.value = suggestion.suggested
   } catch {
      errorMessage.value = 'Could not suggest a dictionary URL. You can enter one yourself.'
   } finally {
      loading.value = false
   }
})

async function submit() {
   if (loading.value || !title.value) return
   loading.value = true
   errorMessage.value = ''
   const originalRoute = router.currentRoute.value
   try {
      const response = await createDictionary({ url: url.value, title: title.value, template: template.value })
      if (!response.success) {
         errorMessage.value = 'This dictionary URL is unavailable.'
         return
      }
      void loadMyDictionaries()
      if (router.currentRoute.value === originalRoute) {
         await router.push({ name: 'dictionary', params: { dictId: response.url } })
      }
   } catch {
      errorMessage.value = 'Could not create the dictionary.'
   } finally {
      loading.value = false
   }
}
</script>

<style>
.dict-new .newBox {
   padding: 1em;
   background: #fff;
   border-radius: 8px;
}
.dict-new .newBox label {
   color: #000;
   font-weight: 500;
}
.dict-new .newBox input {
   border: 1px solid #c7d0dd;
   border-radius: 4px;
}
.dict-new .newBox label[for="template"] {
   position: static;
   transform: none;
}
.dict-new .url-input {
   display: flex;
   align-items: baseline;
}
</style>
