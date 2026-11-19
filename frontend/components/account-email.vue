<template>
<div class="account-email">
   <LoadingOverlay v-if="submitting" :fullscreen="registering"/>
   <div v-if="sent" class="section message messageSuccess" role="status">
      We have sent you an e-mail with instructions on how to
      {{ registering ? 'create a new account' : 'reset your password' }}.
   </div>
   <div v-if="failed" class="section message messageError" role="alert">
      Incorrect e-mail.
   </div>
   <form v-if="!sent" class="section" @submit.prevent="submit">
      <div class="input-field">
         <input id="email" name="email" type="email" class="validate" autocomplete="email" required/>
         <label for="email">Your e-mail</label>
         <span class="helper-text">
            {{ registering
               ? 'To get a new account, enter your e-mail address and we will send you instructions.'
               : 'If you have forgotten your password, enter your e-mail address and we will send you instructions on how to create a new one.' }}
         </span>
      </div>
      <div class="buttons">
         <RouterLink :to="{ name: 'home' }" class="btn btn-secondary waves-effect waves-light">Back</RouterLink>
         <button class="btn waves-effect waves-light" type="submit" :disabled="submitting">
            {{ registering ? 'Register' : 'Get a new password' }}
         </button>
      </div>
   </form>
</div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { api } from '../js/api.ts'
import type { AuthResult } from '../js/auth.ts'
import LoadingOverlay from './loading-overlay.vue'

const props = defineProps<{ action: 'register' | 'forgot' }>()
const registering = computed(() => props.action === 'register')
const sent = ref(false)
const failed = ref(false)
const submitting = ref(false)

async function submit(event: SubmitEvent) {
   if (submitting.value) return
   submitting.value = true
   failed.value = false
   const endpoint = registering.value ? 'signup.json' : 'forgotpwd.json'
   const data = new FormData(event.currentTarget as HTMLFormElement)
   const response = await api.post<AuthResult>(endpoint, data).catch(() => null)
   sent.value = response?.success === true
   failed.value = !sent.value
   submitting.value = false
}
</script>
