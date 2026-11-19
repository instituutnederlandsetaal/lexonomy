<template>
<div class="main-page">
   <div v-if="session && !tokenPage">
      <UserConsent v-if="siteSettings?.consent?.terms && !session.consent"/>
      <DictNew v-else-if="mainSubPage === 'new'"/>
      <Userprofile v-else-if="mainSubPage === 'userprofile'"/>
      <DictList v-else/>
   </div>
   <div v-else>
      <div class="row">
         <div class="col s12 m5 offset-m4" style="text-align:center">
            <img class="login-logo" alt="Lexonomy" src="/assets/img/logo_lexonomy_white.png">
         </div>
      </div>
      <div class="row">
         <div class="col s12 m5 offset-m4 login-box">
            <AdminSetup v-if="mainSubPage === 'login' && siteSettings?.setupRequired" @complete="finishSetup"/>
            <template v-else-if="mainSubPage === 'login'">
               <p v-if="setupComplete" class="section message messageSuccess" role="status">
                  Administrator created. Sign in as root@localhost.
               </p>
               <Login/>
            </template>
            <AccountEmail v-else-if="mainSubPage === 'register' || mainSubPage === 'forgot'"
               :key="mainSubPage" :action="mainSubPage"/>
            <AccountPassword v-else-if="mainSubPage === 'registerPassword' || mainSubPage === 'forgotPassword'"
               :key="mainSubPage + ':' + token"
               :action="mainSubPage === 'registerPassword' ? 'register' : 'recovery'" :token="token"/>
         </div>
      </div>
      <div class="row" v-if="mainSubPage === 'login'">
         <div class="col s12 m5 offset-m4" style="margin-top: -10px;">
            <RouterLink class="login-public-link" :to="{ name: 'public-list' }">Public dictionaries</RouterLink>
         </div>
      </div>
   </div>
</div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { siteSettings } from '../js/site-settings.ts'
import { session } from '../js/auth.ts'
import AccountEmail from './account-email.vue'
import AccountPassword from './account-password.vue'
import AdminSetup from './admin-setup.vue'
import DictList from './dict-list.vue'
import DictNew from './dict-new.vue'
import Login from './login.vue'
import UserConsent from './user-consent.vue'
import Userprofile from './userprofile.vue'

const props = defineProps<{ mainSubPage: string; token?: string }>()

const setupComplete = ref(false)
const tokenPage = computed(() => props.mainSubPage === 'registerPassword' || props.mainSubPage === 'forgotPassword')

function finishSetup() {
   if (siteSettings.value) siteSettings.value = { ...siteSettings.value, setupRequired: false }
   setupComplete.value = true
}
</script>

<style>
.main-page .login-box {
   background: #FFFFFF;
   box-shadow: 0px 0px 30px rgba(92, 32, 170, 0.7);
   border-radius: 16px;
}
.main-page .login-logo {
   height: 40px;
}
.main-page{
   margin-top: 20px;
}
.main-page .login-public-link {
   color: #ffffff;
}
.main-page .login-public-link:hover {
   color: #c62132;
}
</style>
