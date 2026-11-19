<template>
<user-consent>
   <div v-if="siteSettings?.consent">
      <h1>Terms of use</h1>
      <div class="row">
         <div class="col">
            <RawHtml :content="siteSettings.consent.terms"></RawHtml>
         </div>
      </div>
      <div class="row">
         <div class="col">
            <button class="btn waves-effect waves-light"
                  :disabled="submitting" @click="consent">
               {{ siteSettings.consent.confirm }}
               <i class="material-symbols-outlined right">check</i>
            </button>
            <p v-if="failed" class="message messageError" role="alert">Could not save the consent.</p>
         </div>
      </div>
   </div>
</user-consent>
</template>

<script setup>
import { ref } from 'vue'
import { acceptConsent } from '../js/auth.ts'
import { siteSettings } from '../js/site-settings.ts'
import RawHtml from './raw-html.vue'

const failed = ref(false)
const submitting = ref(false)

async function consent() {
   if (submitting.value) return
   submitting.value = true
   failed.value = false
   try {
      failed.value = !await acceptConsent()
   } catch {
      failed.value = true
   } finally {
      submitting.value = false
   }
}
</script>
