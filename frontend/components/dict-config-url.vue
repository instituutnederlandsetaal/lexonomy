<template>
<div class="dict-config-url">
   <LoadingOverlay v-if="saving"/>
   <DictNav :links="[['config', 'Configure'], ['config-url', 'Change URL']]"/>
   <h1>Change URL</h1>
   <DictConfigButtons :dict-id="dictId" :save-data="saveData" :disabled="saving || Boolean(movedUrl)"
         label="Change"></DictConfigButtons>
   <div class="row">
      <span>Current URL</span>
      <div style="margin: 0 0 30px;">
         <span>{{ baseUrl }}{{ dictId }}</span>
      </div>
   </div>
   <div v-if="!movedUrl" class="row">
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
      <span v-if="moveResult === false" id="error">This dictionary URL is unavailable.</span>
      <span v-if="moveResult === true" id="success">
      <b>Your dictionary has been moved to a new URL.</b>
      <RouterLink class="btn waves-effect waves-light" :to="{ name: 'dictionary', params: { dictId: movedUrl } }" id="newlink">
         Go to new dictionary URL
      <i class="material-symbols-outlined right">trending_flat</i>
   </RouterLink>
      </span>
   </div>
</div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { pageUrl } from '../js/page-url.ts'
import { moveDictionary } from '../js/dictionary-config-api.ts'
import { loadMyDictionaries } from '../js/my-dictionaries.ts'
import { useDictionaryScope } from '../js/use-dictionary-setting.ts'
import Materialize from '../libs/materialize/materialize.min.js'
import DictConfigButtons from './dict-config-buttons.vue'
import DictNav from './dict-nav.vue'
import LoadingOverlay from './loading-overlay.vue'

const props = defineProps<{ dictId: string }>()
const scope = useDictionaryScope(() => props.dictId)
const url = ref<HTMLInputElement>()
const newUrl = ref('')
const movedUrl = ref('')
const moveResult = ref<boolean | null>(null)
const saving = ref(false)
const baseUrl = new URL('#/', pageUrl).href
watch(scope, () => {
   newUrl.value = ''
   movedUrl.value = ''
   moveResult.value = null
   saving.value = false
})

async function saveData() {
   if (saving.value || movedUrl.value || !url.value?.reportValidity()) return
   const current = scope.value
   const nextUrl = newUrl.value
   saving.value = true
   try {
      const { success } = await moveDictionary(current.dictId, nextUrl)
      if (success) void loadMyDictionaries()
      if (!current.active) return
      moveResult.value = success
      if (success) movedUrl.value = nextUrl
   } catch {
      if (current.active) Materialize.toast({ html: 'Could not change the dictionary URL.' })
   } finally {
      if (current.active) saving.value = false
   }
}
</script>
