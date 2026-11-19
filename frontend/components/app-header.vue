<template>
<header class="app-header">
   <nav class="white" aria-label="Main navigation">
      <div class="nav-wrapper">
         <RouterLink :to="{ name: 'home' }" class="brand-logo" aria-label="Lexonomy home">
            <span class="site-logo" aria-hidden="true"/>
         </RouterLink>
         <ul class="right hide-on-med-and-down">
            <li v-if="dictionaryLinks.length">
               <HeaderMenu :groups="[dictionaryLinks]">
                  <span class="menu-label">Dictionary {{ activeDictionary.title }}</span>
                  <span class="material-symbols-outlined" aria-hidden="true">arrow_drop_down</span>
               </HeaderMenu>
            </li>
            <li>
               <HeaderMenu :groups="[accountLinks]">
                  <span class="menu-label">{{ session?.email ?? 'anonymous user' }}</span>
                  <span class="material-symbols-outlined" aria-hidden="true">arrow_drop_down</span>
               </HeaderMenu>
            </li>
         </ul>
         <div class="right hide-on-large-only">
            <HeaderMenu :groups="menuGroups" label="Open navigation">
               <span class="material-symbols-outlined" aria-hidden="true">menu</span>
            </HeaderMenu>
         </div>
      </div>
   </nav>
</header>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import Materialize from '../libs/materialize/materialize.min.js'
import { activeDictionary } from '../js/dictionary-workspace.ts'
import { logout, session } from '../js/auth.ts'
import HeaderMenu, { type NavigationItem } from './HeaderMenu.vue'
import { confirmEntryNavigation, unsavedEntry } from './entry-editor/unsaved.js'

const router = useRouter()
const loggingOut = ref(false)

const dictionaryLinks = computed<NavigationItem[]>(() => {
   const { dictId, config, userAccess } = activeDictionary
   if (!session.value || !dictId || !config || !userAccess) return []
   const params = { dictId }
   const links: NavigationItem[] = []
   if (userAccess.canEdit) links.push(
      { label: 'View', to: { name: 'dictionary', params } },
      { label: 'Edit', to: { name: 'edit', params } }
   )
   if (userAccess.canConfig) links.push({ label: 'Configure', to: { name: 'config', params } })
   if (userAccess.canDownload) links.push({ label: 'Download', to: { name: 'download', params } })
   if (userAccess.canUpload) links.push({ label: 'Upload', to: { name: 'upload', params } })
   links.push({ label: 'Links', to: { name: 'links', params } })
   return links
})

const accountLinks = computed<NavigationItem[]>(() => session.value
   ? [{ label: 'Log out', action: doLogout }, { label: 'Your profile', to: { name: 'userprofile' } }]
   : [
      { label: 'Log in', to: { name: 'home' } },
      { label: 'Get an account', to: { name: 'register' } },
      { label: 'Forgot your password?', to: { name: 'forgot' } }
   ]
)

const menuGroups = computed(() => dictionaryLinks.value.length
   ? [dictionaryLinks.value, accountLinks.value] : [accountLinks.value]
)

onMounted(() => {
   const size = document.cookie.split('; ').find(cookie => cookie.startsWith('fontSize='))?.slice(9)
   if (Number(size) > 0) document.documentElement.style.fontSize = `${Number(size)}px`
})

async function doLogout() {
   if (loggingOut.value || !confirmEntryNavigation()) return
   loggingOut.value = true
   try {
      await logout()
      unsavedEntry.value = false
      await router.replace({ name: 'home' })
   } catch {
      Materialize.toast({ html: 'Could not log out.' })
   } finally {
      loggingOut.value = false
   }
}
</script>

<style>
.app-header .brand-logo {
   padding: 0 20px 0 40px;
}
.app-header .site-logo {
   height: 40px;
   position: relative;
   top: 20px;
   width: min(223px, 48vw);
   background-image: url(/assets/img/logo_lexonomy.png);
   background-size: contain;
   display: inline-block;
   background-repeat: no-repeat;
}
.app-header nav {
   border-bottom: 1px solid black;
   box-shadow: none;
}
.app-header nav .nav-wrapper {
   color: #000;
}
</style>
