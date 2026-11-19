<template>
<div class="userprofile">
   <h1>Account settings</h1>
   <form class="row" @submit.prevent="changePassword">
      <p role="status">{{ message }}</p>
      <label for="password">New password</label>
      <div class="input-field"
            style="margin-top: 0;">
         <div style="display: flex; gap: 10px; align-items: center;">
            <input id="password"
                  name="password" type="password" class="validate" autocomplete="new-password" required
                  style="width: 350px;"/>
            <button class="btn waves-effect waves-light"
                  type="submit" :disabled="submitting"
                  style="margin-bottom: 10px;">Change password
               <i class="material-symbols-outlined right">send</i>
            </button>
         </div>
         <span class="helper-text">Set your password to access Lexonomy.</span>
      </div>
   </form>
   <div>
      <RouterLink :to="{ name: 'home' }" class="btn">Your dictionaries</RouterLink>
   </div>

</div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { api } from '../js/api.ts'
import type { AuthResult } from '../js/auth.ts'

const message = ref('')
const submitting = ref(false)

async function changePassword(event: SubmitEvent) {
   if (submitting.value) return
   submitting.value = true
   message.value = ''
   const form = event.currentTarget as HTMLFormElement
   const response = await api.post<AuthResult>('changepwd.json', new FormData(form)).catch(() => null)
   message.value = response?.success ? 'Password changed.' : 'There was an error saving the password.'
   if (response?.success) form.reset()
   submitting.value = false
}

</script>
