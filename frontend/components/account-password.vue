<template>
<div class="account-password">
   <LoadingOverlay v-if="checking || submitting"/>
   <p v-if="checking && registering">Validating signup token...</p>
   <div v-if="verificationFailed" class="section message messageError" role="alert">
      Could not check this link. Reload the page to try again.
   </div>
   <div v-else-if="!checking && !valid" class="section message messageError" role="alert">
      This {{ registering ? 'signup' : 'recovery' }} link is invalid. It may have expired or has been used before.
   </div>
   <div v-if="failed" class="section message messageError" role="alert">
      {{ registering ? 'Error while creating account.' : 'Could not reset your password.' }}
   </div>
   <p v-if="saved && registering" role="status">
      We have created your account.
      You can now <RouterLink :to="{ name: 'home' }">log in</RouterLink> with your e-mail address and password.
   </p>
   <div v-if="saved && !registering">
      <div class="message messageSuccess" role="status">
         Your password is updated. You can now log in with your e-mail address and password.
      </div>
      <div class="section center-align"><RouterLink :to="{ name: 'home' }" class="btn btn-primary">log in</RouterLink></div>
   </div>
   <form v-if="valid && !saved" @submit.prevent="submit">
      <div class="input-field">
         <input id="password" name="password" type="password" class="validate" autocomplete="new-password" required/>
         <label for="password">Your password</label>
         <span class="helper-text">Set your password to access Lexonomy.</span>
      </div>
      <button class="btn waves-effect waves-light" type="submit" :disabled="submitting">Set password</button>
   </form>
</div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { api } from '../js/api.ts'
import type { AuthResult } from '../js/auth.ts'
import LoadingOverlay from './loading-overlay.vue'

const props = defineProps<{ action: 'register' | 'recovery', token?: string }>()
const registering = computed(() => props.action === 'register')
const checking = ref(true)
const valid = ref(false)
const verificationFailed = ref(false)
const saved = ref(false)
const failed = ref(false)
const submitting = ref(false)

onMounted(async () => {
   if (props.token) {
      const data = { token: props.token, type: props.action }
      try {
         const response = await api.post<AuthResult>('verifytoken.json', data)
         valid.value = response.success === true
      } catch {
         verificationFailed.value = true
      }
   }
   checking.value = false
})

async function submit(event: SubmitEvent) {
   if (!props.token || !valid.value || submitting.value) return
   submitting.value = true
   failed.value = false
   const endpoint = registering.value ? 'createaccount.json' : 'recoverpwd.json'
   const data = new FormData(event.currentTarget as HTMLFormElement)
   data.set('token', props.token)
   const response = await api.post<AuthResult>(endpoint, data).catch(() => null)
   saved.value = response?.success === true
   failed.value = !saved.value
   submitting.value = false
}
</script>
