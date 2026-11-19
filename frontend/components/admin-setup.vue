<template>
   <form class="section" @submit.prevent="submit">
      <h4>Set up Lexonomy</h4>
      <p>Create the <strong>root@localhost</strong> administrator account. Find the setup code in the backend startup logs.</p>
      <div class="input-field">
         <input id="setup-code" name="code" type="password" autocomplete="off" required>
         <label for="setup-code">Setup code</label>
      </div>
      <div class="input-field">
         <input id="setup-password" name="password" type="password" autocomplete="new-password"
                minlength="12" maxlength="1024" required>
         <label for="setup-password">Administrator password</label>
         <span class="helper-text">Use at least 12 characters.</span>
      </div>
      <div class="input-field">
         <input id="setup-confirm" name="confirmation" type="password" autocomplete="new-password" required>
         <label for="setup-confirm">Confirm password</label>
      </div>
      <p v-if="error" class="message messageError" role="alert">{{ error }}</p>
      <button class="btn btn-primary waves-effect waves-light" type="submit" :disabled="submitting">
         Create administrator
      </button>
   </form>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { api } from '../js/api.ts'
import type { AuthResult } from '../js/auth.ts'

const emit = defineEmits<{ complete: [] }>()
const error = ref('')
const submitting = ref(false)

async function submit(event: SubmitEvent) {
   if (submitting.value) return
   const form = event.currentTarget as HTMLFormElement
   const fields = new FormData(form)
   const password = String(fields.get('password') ?? '')
   if (password !== fields.get('confirmation')) {
      error.value = 'The passwords do not match.'
      return
   }
   error.value = ''
   submitting.value = true
   try {
      const { success } = await api.post<AuthResult>('initial-admin.json', {
         code: String(fields.get('code') ?? '').trim(),
         password
      })
      if (success) emit('complete')
      else error.value = 'Setup was rejected. Check the current setup code or reload if setup has finished.'
   } catch {
      error.value = 'Could not complete setup. Please try again.'
   } finally {
      submitting.value = false
   }
}
</script>
