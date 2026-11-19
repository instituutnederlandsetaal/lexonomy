<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { dictionaryDownloadUrl } from '../js/dictionary-files-api.ts'
import DictNav from './dict-nav.vue'

const route = useRoute()
const clean = ref(false)
const dictId = computed(() => typeof route.params.dictId === 'string' ? route.params.dictId : '')
const downloadUrl = computed(() => dictId.value ? dictionaryDownloadUrl(dictId.value, clean.value) : undefined)

watch(dictId, () => { clean.value = false })
</script>

<template>
   <section>
      <DictNav :links="[['download', 'Download']]"/>
      <h1>Download</h1>
      <div class="input-field">
         <a class="waves-effect waves-light btn btn-primary download-link" target="_blank" rel="noopener" :href="downloadUrl">
            <i class="material-symbols-outlined left" aria-hidden="true">file_download</i>
            Download {{ dictId }}.xml
         </a>
      </div>
      <label>
         <input v-model="clean" type="checkbox" class="noAttributes" name="noAttributes">
         <span>XML without Lexonomy attributes</span>
      </label>
      <small class="helper-text">
         If you want to import the XML file back to Lexonomy, you need Lexonomy attributes.
      </small>
   </section>
</template>
