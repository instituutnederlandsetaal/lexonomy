<template>
<div class="dict-config-publico">
   <LoadingOverlay v-if="loading || saving"/>
   <DictNav :links="[['config', 'Configure'], ['config-publico', 'Publishing']]"/>
   <h1>Publishing</h1>
   <template v-if="ready">
      <DictConfigButtons :dict-id="dictId" :save-data="() => save(draft)" :disabled="saving || (draft.public && !selectedLicence)"></DictConfigButtons>
      <div class="row">
         <div class="input-field">
            <p>
               <label>
                  <input name="publico_public"
                        type="radio"
                        class="with-gap"
                        value="0"
                        :checked="!draft.public"
                        @change="setPublishing(false)"/>
                  <span>Private</span>
               </label>
               <label style="margin-left: 30px;">
                  <input name="publico_public"
                        type="radio"
                        class="with-gap"
                        value="1"
                        :checked="draft.public"
                        @change="setPublishing(true)" />
                  <span>Public</span>
               </label>
            </p>
            <span class="helper-text">
               <i>Private</i> means that the dictionary is not publicly viewable. <i>Public</i> means that the dictionary is publicly viewable.
            </span>
         </div>
      </div>
      <div v-if="draft.public"
            class="row">
         <div class="input-field"
               id="publico_licence_info"
               style="max-width: 500px;">
            <FormSelect id="publico_licence" v-model="draft.licence" :options="licences"
               aria-label="Licence" placeholder="Choose a licence"/>
            <span v-if="licenceUrl" class="helper-text">
               More information about this licence: <a :href="licenceUrl" target="_blank" rel="noopener">{{ licenceUrl }}</a>.
            </span>
         </div>
      </div>
   </template>
   <p v-else-if="!loading">Publishing settings could not be loaded. <button class="btn-flat" type="button" @click="load">Retry</button></p>
</div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { siteSettings } from '../js/site-settings.ts'
import { useDictionarySetting } from '../js/use-dictionary-setting.ts'
import DictConfigButtons from './dict-config-buttons.vue'
import DictNav from './dict-nav.vue'
import FormSelect from './FormSelect.vue'
import LoadingOverlay from './loading-overlay.vue'

const props = defineProps<{ dictId: string }>()
const draft = ref({ public: false, licence: '' })
const { loading, ready, saving, load, save } = useDictionarySetting(() => props.dictId, 'publico', content => {
   draft.value = { public: content.public, licence: content.licence ?? '' }
})
const licences = computed(() => Object.entries(siteSettings.value?.licences ?? {})
   .map(([value, { title }]) => ({ value, label: title })))
const selectedLicence = computed(() => siteSettings.value?.licences?.[draft.value.licence])
const licenceUrl = computed(() => selectedLicence.value?.url)

function setPublishing(value: boolean) {
   draft.value.public = value
   if (value && !selectedLicence.value) draft.value.licence = licences.value[0]?.value ?? ''
}
</script>
