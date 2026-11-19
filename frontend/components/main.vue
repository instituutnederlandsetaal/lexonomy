<template>
   <div class="main" :class="{ 'login-page': loginPage, 'dark-page': darkPage }">
      <div v-if="newVersion" class="new-version">
         <div>New version available!</div>
         Please reload the page to use the latest version.
         <button class="btn" @click="reload">Reload</button>
      </div>
      <LoadingOverlay v-if="loading" :fullscreen="true"/>
      <AppHeader/>
      <main class="contentWrapper">
         <RouterView v-if="!loading" v-slot="{ Component, route }">
            <component :is="Component"
               class="container content row" :class="{ wideContainer: route.meta.wide }"/>
         </RouterView>
      </main>
      <AppFooter/>
   </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import Materialize from '../libs/materialize/materialize.min.js'
import { api } from '../js/api.ts'
import { session } from '../js/auth.ts'
import { clearMyDictionaries, loadMyDictionaries } from '../js/my-dictionaries.ts'
import { loadSiteSettings } from '../js/site-settings.ts'
import { unsavedEntry } from './entry-editor/unsaved.js'
import AppFooter from './app-footer.vue'
import AppHeader from './app-header.vue'
import LoadingOverlay from './loading-overlay.vue'

const route = useRoute()
const loadingSettings = ref(true)
const newVersion = ref(false)
const version: string | undefined = import.meta.env.VITE_LEXONOMY_VERSION
let versionTimer: ReturnType<typeof setInterval> | undefined

const loading = computed(() => !route.name || loadingSettings.value)
const loginPage = computed(() => route.meta.theme === 'account' &&
   (!session.value || route.name === 'registerPassword' || route.name === 'forgotPassword'))
const darkPage = computed(() => !session.value && route.meta.theme === 'public')

watch(() => session.value?.email, email => {
   if (email) void loadMyDictionaries()
   else clearMyDictionaries()
}, { immediate: true })

watch(unsavedEntry, (dirty, _, onCleanup) => {
   if (!dirty) return
   const beforeLeaving = (event: BeforeUnloadEvent) => {
      event.preventDefault()
      event.returnValue = true
   }
   window.addEventListener('beforeunload', beforeLeaving)
   onCleanup(() => window.removeEventListener('beforeunload', beforeLeaving))
})

onMounted(async () => {
   if (!import.meta.env.DEV && version) versionTimer = setInterval(checkVersion, 24 * 60 * 60 * 1000)
   try {
      await loadSiteSettings()
   } catch {
      Materialize.toast({ html: 'Could not load app configuration.' })
   } finally {
      loadingSettings.value = false
   }
})
onBeforeUnmount(() => clearInterval(versionTimer))

async function checkVersion() {
   const actual = await api.text('version.txt').catch(() => '')
   if (actual && actual.trim() !== version?.trim()) {
      newVersion.value = true
      clearInterval(versionTimer)
   }
}

function reload() {
   location.reload()
}
</script>

<style>
.main .new-version {
   position: sticky;
   top: 0;
   z-index: 99999;
   padding: 20px;
   text-align: center;
   background: white;
   box-shadow: 0 3px 3px rgb(0 0 0 / 14%), 0 1px 7px rgb(0 0 0 / 12%), 0 3px 1px -1px rgb(0 0 0 / 20%);
}
.main .new-version > div {
   font-size: 1.8rem;
   margin-bottom: 1rem;
}
.main .new-version > button {
   margin-left: 1.5rem;
}
.main .contentWrapper{
   position: relative;
   background-color: #f0f8ff;
}
.main .content{
   display: block;
   padding-left: 10px;
   min-height: 50vh;
}
.main .wideContainer{
   max-width: 1600px;
   width: 90vw;
}
.main.login-page .app-header {
   visibility: hidden;
}
.main.dark-page .app-header, .main.dark-page .app-header nav.white {
   background-color: #004494 !important;
}
.main.dark-page .app-header .nav-wrapper {
   color: #ffffff;
}
.main.dark-page .app-header .site-logo {
   background-image: url(/assets/img/logo_lexonomy_white.png) !important;
}
.main {
   background-color: #f0f8ff;
}
.main.dark-page, .main.login-page {
   background-image: url(/assets/img/background_dark.png);
   background-size: cover;
}
.main.dark-page .contentWrapper,
.main.login-page .contentWrapper {
   background-color: unset;
}
.main.dark-page .footer-logos,
.main.login-page .footer-logos{
   background-color: unset;
   border-top: 1px solid #ffffff;
}
.main.dark-page .app-footer a,
.main.login-page .app-footer a,
.main.dark-page .app-footer .version,
.main.login-page .app-footer .version,
.main.dark-page .app-footer .horizon-info,
.main.login-page .app-footer .horizon-info {
   color: #ffffff;
}
.main.dark-page .app-footer .eulogo,
.main.login-page .app-footer .eulogo {
   background-image: url(/assets/img/logo_eu_white.png) !important;
}
.main.dark-page .app-footer .elexislogo,
.main.login-page .app-footer .elexislogo {
   background-image: url(/assets/img/logo_elexis_white.png) !important;
}
.main.dark-page .app-footer .githublogo,
.main.login-page .app-footer .githublogo {
   background-image: url(/assets/img/github-white.png) !important;
}
.main.dark-page .container h1 {
   color: #ffffff;
}
.main.dark-page .container > div {
   background: #FFFFFF;
   box-shadow: 0px 0px 30px rgba(92, 32, 170, 0.7);
   border-radius: 16px;
   padding: 2em;
}
</style>
