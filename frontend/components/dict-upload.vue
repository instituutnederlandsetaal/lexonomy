<script setup lang="ts">
import { computed, onScopeDispose, ref, shallowRef, watch } from 'vue'
import { useRoute } from 'vue-router'
import { fetchImportErrors, fetchImportStatus, startDictionaryUpload } from '../js/dictionary-files-api.ts'
import { dictionaryWorkspace } from '../js/dictionary-workspace.ts'
import { loadMyDictionaries } from '../js/my-dictionaries.ts'
import DictNav from './dict-nav.vue'
import LoadingOverlay from './loading-overlay.vue'

const route = useRoute()
const dictId = computed(() => typeof route.params.dictId === 'string' ? route.params.dictId : '')
const file = shallowRef<File | null>(null)
const purge = ref(false)
const phase = ref<'ready' | 'uploading' | 'importing' | 'finished'>('ready')
const busy = computed(() => phase.value === 'uploading' || phase.value === 'importing')
const infoMessage = ref('')
const errorMessage = ref('')
let operation = 0
let pollTimer: ReturnType<typeof setTimeout> | undefined

function reset() {
   operation++
   clearTimeout(pollTimer)
   phase.value = 'ready'
   file.value = null
   purge.value = false
   infoMessage.value = errorMessage.value = ''
}
watch(dictId, reset)
onScopeDispose(reset)

function selectFile(event: Event) {
   if (event.target instanceof HTMLInputElement) file.value = event.target.files?.[0] ?? null
}

async function upload() {
   const current = dictId.value
   if (!current || !file.value || busy.value) return
   const version = ++operation
   const isCurrent = () => operation === version && dictId.value === current
   phase.value = 'uploading'
   errorMessage.value = ''
   infoMessage.value = 'Uploading XML…'
   let job: Awaited<ReturnType<typeof startDictionaryUpload>>
   try {
      job = await startDictionaryUpload(current, file.value, purge.value)
   } catch {
      if (isCurrent()) {
         phase.value = 'ready'
         errorMessage.value = 'The XML file could not be uploaded.'
         infoMessage.value = ''
      }
      return
   }
   if (!isCurrent()) return
   phase.value = 'importing'

   async function poll() {
      try {
         const status = await fetchImportStatus(current, job)
         if (!isCurrent()) return
         infoMessage.value = status.progressMessage
         if (status.finished) {
            phase.value = 'finished'
            void loadMyDictionaries()
            void dictionaryWorkspace.refreshEntries(current)
         } else if (status.errors) {
            const details = await fetchImportErrors(current, job)
            if (isCurrent()) {
               phase.value = 'ready'
               errorMessage.value = details || 'The XML file could not be imported.'
            }
         } else {
            pollTimer = setTimeout(poll, 2000)
         }
      } catch {
         if (isCurrent()) {
            phase.value = 'ready'
            errorMessage.value = 'Import progress could not be checked.'
         }
      }
   }
   await poll()
}
</script>

<template>
   <section>
      <LoadingOverlay v-if="phase === 'uploading'"/>
      <DictNav :links="[['upload', 'Upload']]"/>
      <h1>Upload</h1>
      <form @submit.prevent="upload">
         <div class="file-field input-field buttons" style="max-width: 700px;">
            <div class="btn">
               <span>Choose XML file</span>
               <input :key="dictId" id="file" type="file" aria-label="Choose XML file" :disabled="busy" @change="selectFile">
            </div>
            <div class="file-path-wrapper">
               <input class="file-path" type="text" aria-hidden="true" tabindex="-1" readonly :value="file?.name ?? ''">
            </div>
            <button id="startButton" type="submit" class="waves-effect waves-light btn btn-primary"
                  :disabled="!file || busy">
               <i class="material-symbols-outlined left" aria-hidden="true">file_upload</i>Upload file
            </button>
         </div>
         <label>
            <input id="purge" v-model="purge" type="checkbox" :disabled="busy">
            <span>Purge dictionary before upload</span>
         </label>
      </form>

      <section v-if="infoMessage || errorMessage">
         <h3>Progress</h3>
         <div v-if="infoMessage" class="message messageInfo" role="status">
            {{ infoMessage }}
            <RouterLink v-if="phase === 'finished'" :to="{ name: 'dictionary', params: { dictId } }">See dictionary</RouterLink>
         </div>
         <div v-if="errorMessage" class="message messageError" role="alert">{{ errorMessage }}</div>
      </section>
   </section>
</template>
