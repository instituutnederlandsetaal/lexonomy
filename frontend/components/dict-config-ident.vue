<template>
<div class="dict-config-ident">
   <LoadingOverlay v-if="loading || saving"/>
   <DictNav :links="[['config', 'Configure'], ['config-ident', 'Description']]"/>
   <h1>Description</h1>
   <div>
      <form v-if="ready" @submit.prevent="saveData">
         <DictConfigButtons :dict-id="dictId" :save-data="saveData" :disabled="saving || !ready"></DictConfigButtons>
         <div class="row">
            <div class="input-field">
               <input v-model="draft.title"
                     placeholder="My Dictionary"
                     id="ident_title"
                     type="text"
                     class="validate"
                     style="width:300px" />
               <label class="active" for="ident_title">Dictionary name</label>
               <span class="helper-text">A human-readable title for your dictionary, such as <i>My Esperanto Dictionary</i>.</span>
            </div>
         </div>
         <div class="row">
            <div class="input-field">
               <textarea id="ident_blurb"
                     class="materialize-textarea"
                     placeholder="Yet another Lexonomy dictionary."
                     rows="3" v-model="draft.blurb"></textarea>
               <label class="active" for="ident_blurb">Dictionary description</label>
               <span class="helper-text">
                  This will appear on your dictionary's home page. You can leave it blank if you prefer.<br/>You can use <a href='https://daringfireball.net/projects/markdown/' target='_blank'>Markdown</a> here.
               </span>
            </div>
         </div>
         <div class="row">
            <div class="input-field">
               <input v-model="draft.lang"
                     type="text"
                     id="ident_lang"
                     placeholder="Type to search for language, or write your custom info"
                     style="width:300px" list="dictionary-languages">
               <datalist id="dictionary-languages"><option v-for="language in languages" :key="language" :value="language"/></datalist>
               <label class="active" for="ident_lang">Main language</label>
               <span class="helper-text">Language of dictionary entries, used to sort dictionaries on your home page. You can select language from the list, or write down your own.</span>
            </div>
         </div>
         <div class="row">
            <div class="input-field">
               <input v-model="draft.handle"
                     placeholder="URL"
                     id="ident_handle"
                     type="text"
                     class="validate"/>
               <label class="active" for="ident_handle">Metadata from CLARIN repository</label>
               <span class="helper-text">Link to metadata recorded in CLARIN repository, provide URL to 'handle' link, eg. <code>http://hdl.handle.net/11356/1094</code>.</span>
            </div>
         </div>
      </form>
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
import type { DictionarySettings } from '../js/dictionary-config-api.ts'
import { loadMyDictionaries } from '../js/my-dictionaries.ts'

const props = defineProps<{ dictId: string }>()
const defaults: DictionarySettings['ident'] = { title: '', blurb: '', lang: '', handle: '' }
const draft = ref({ ...defaults })
const { loading, ready, saving, load, save } = useDictionarySetting(() => props.dictId, 'ident', content => {
   draft.value = { ...defaults, ...content }
})
const languages = computed(() => [...new Set(draft.value.langs?.map(language => language.lang) ?? [])])

async function saveData() {
   const { title, blurb, lang, handle } = draft.value
   if (await save({ title, blurb, lang, handle })) void loadMyDictionaries()
}
</script>
