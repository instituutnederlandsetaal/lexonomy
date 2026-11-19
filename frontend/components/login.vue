<template>
<div class="login">
   <LoadingOverlay v-if="submitting" :fullscreen="true"/>
   <div v-if="message" class="section message messageError" role="alert">
      {{ message }}
   </div>
   <form class="section" style="position:relative" @submit.prevent="submit">
      <h4>Registered user login</h4>
      <div class="input-field">
         <input id="username"
               name="email"
               type="email"
               class="validate" placeholder="E-mail address"
               aria-label="E-mail address" autocomplete="username" required/>
      </div>
      <div class="input-field">
         <input id="password"
               name="password"
               type="password"
               placeholder="Password"
               aria-label="Password" autocomplete="current-password" required/>
         <small>
            <RouterLink :to="{ name: 'forgot' }">Forgot password?</RouterLink>
         </small>
      </div>
      <RouterLink :to="{ name: 'register' }">Get an account</RouterLink>
      <button class="btn btn-primary waves-effect waves-light"
            name="login"
            id="loginButton"
            type="submit"
            :disabled="submitting">
         Log in
      </button>
   </form>
</div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { login } from '../js/auth.ts'
import LoadingOverlay from './loading-overlay.vue'

const message = ref('')
const submitting = ref(false)
const route = useRoute()
const router = useRouter()

async function submit(event: SubmitEvent) {
   if (submitting.value) return
   const fields = new FormData(event.currentTarget as HTMLFormElement)
   const email = String(fields.get('email') ?? '')
   const password = String(fields.get('password') ?? '')
   submitting.value = true
   message.value = ''
   try {
      if (!await login({ email, password })) {
         message.value = 'Incorrect username or password.'
      } else {
         const target = route.query.redirect
         if (typeof target === 'string' && target.startsWith('/') && !target.startsWith('//')) {
            await router.replace(target)
         }
      }
   } catch {
      message.value = 'Could not log in. Please try again.'
   } finally {
      submitting.value = false
   }
}
</script>

<style>
.login h4 {
   color: black;
   text-align: center;
}
.login .input-field input {
   border: 1px solid #C7D0DD;
   border-radius: 4px;
}
.login .input-field input:focus {
   border: 1px solid #005FCC;
   border-radius: 4px;
   color: #005fcc;
}
.login #loginButton {
   position: absolute;
   right: 1em;
   bottom: 2em;
}
.login a {
   color: #0000ee;
   }
   .login small{
      position: relative;
      top: -10px;
   }
</style>
