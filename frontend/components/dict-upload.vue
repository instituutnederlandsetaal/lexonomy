<template>
<dict-upload>
   <LoadingOverlay v-if="state.isUploading"/>
   <DictNav :links="[['upload', 'Upload']]"/>
   <h1>Upload</h1>
   <div class="file-field input-field buttons"
         style="max-width: 700px;">
      <div class="btn">
         <span>Choose XML file</span>
         <input type="file"
               id="file" ref="file">
      </div>
      <div class="file-path-wrapper">
         <input class="file-path validate"
               type="text">
      </div>
      <div>
         <a class="waves-effect waves-light btn btn-primary" :class="{ disabled: state.isUploading || state.isImporting }"
               @click="doUpload"
               id="startButton">
            <i class="material-symbols-outlined left">file_upload</i>Upload file
         </a>
      </div>
   </div>
   <div>
      <label>
         <input type="checkbox"
               id="purge" ref="purge"/>
         <span>Purge dictionary before upload</span>
      </label>
   </div>
   <br><br>

   <template v-if="state.infoMessage || state.errorMessage">
      <h3>Progress</h3>
      <div v-if="state.infoMessage"
            class="message messageInfo">
         {{ state.infoMessage }}
         <template v-if="state.importFinished">
            Dictionary import finished. <RouterLink :to="{ name: 'dictionary', params: { dictId: activeDictionary.dictId } }">See dictionary</RouterLink>
         </template>
      </div>
      <div v-if="state.errorMessage"
            class="message messageError">
         {{ state.errorMessage }}
      </div>
   </template>
</dict-upload>
</template>

<script>
import { activeDictionary, dictionaryWorkspace } from '../js/dictionary-workspace.ts'
import { loadMyDictionaries } from '../js/my-dictionaries.ts'
import DictNav from './dict-nav.vue'
import LoadingOverlay from './loading-overlay.vue'
import { api } from '../js/api.ts'

export default {
   setup: () => ({ activeDictionary }),
   components: { DictNav, LoadingOverlay },
   data() {
      return {
         state: {
            isUploading: false,
            isImporting: false,
            importFinished: false,
            timeoutHandle: null,
            errorMessage: "",
            infoMessage: ""
         }
      }
   },

   beforeUnmount() {
      clearTimeout(this.state.timeoutHandle)
   },

   methods: {
      async doUpload() {
         const file = this.$refs.file.files[0]
         if (!file || this.state.isUploading || this.state.isImporting) return

         const fd = new FormData()
         fd.append('myfile', file)
         if (this.$refs.purge.checked) fd.append('purge', 'on')
         const dictId = this.activeDictionary.dictId
         Object.assign(this.state, {
            isUploading: true,
            importFinished: false,
            errorMessage: "",
            infoMessage: "Upload started, please keep the window open."
         })
         try {
            const { success, file, uploadStart } = await api.post(`${encodeURIComponent(dictId)}/upload.html`, fd)
            if (!success || !file) throw new Error('Upload rejected')
            if (this.$el.isConnected) this.pollImport(dictId, { filename: file, uploadStart })
         } catch {
            this.state.infoMessage = 'Error while uploading file'
         } finally {
            this.state.isUploading = false
         }
      },

      async pollImport(dictId, upload) {
         this.state.isImporting = true
         const endpoint = `${encodeURIComponent(dictId)}/import.json`
         try {
            const response = await api.get(endpoint, upload)
            if (!this.$el.isConnected || this.activeDictionary.dictId !== dictId) return
            this.state.infoMessage = response.progressMessage
            if (response.finished) {
               this.state.importFinished = true
               loadMyDictionaries()
               dictionaryWorkspace.loadEntryList()
            } else if (response.errors) {
               this.state.infoMessage = 'There were some errors during XML parsing'
               const { errorData } = await api.get(endpoint, { ...upload, showErrors: true, truncate: 10000 })
               this.state.errorMessage = errorData.replaceAll('&lt;', '<')
            } else {
               this.state.timeoutHandle = setTimeout(() => this.pollImport(dictId, upload), 2000)
               return
            }
         } catch {
            this.state.infoMessage = 'Error while checking import progress'
         }
         this.state.isImporting = false
      }
   }
}
</script>
