<template>
<app-header>
   <div ref="dropdownMenus">
      <ul
            id="dropdown-menu-dict"
            class="dropdown-content">
         <li v-if="activeDictionary.userAccess?.canEdit">
            <RouterLink :to="{ name: 'dictionary', params: { dictId: activeDictionary.dictId } }">View</RouterLink>
         </li>
         <li v-if="activeDictionary.userAccess?.canEdit">
            <RouterLink :to="{ name: 'edit', params: { dictId: activeDictionary.dictId } }">Edit</RouterLink>
         </li>
         <li v-if="activeDictionary.userAccess?.canConfig">
            <RouterLink :to="{ name: 'config', params: { dictId: activeDictionary.dictId } }">Configure</RouterLink>
         </li>
         <li v-if="activeDictionary.userAccess?.canDownload">
            <RouterLink :to="{ name: 'download', params: { dictId: activeDictionary.dictId } }">Download</RouterLink>
         </li>
         <li v-if="activeDictionary.userAccess?.canUpload">
            <RouterLink :to="{ name: 'upload', params: { dictId: activeDictionary.dictId } }">Upload</RouterLink>
         </li>
         <li v-if="activeDictionary.dictId">
            <RouterLink :to="{ name: 'links', params: { dictId: activeDictionary.dictId } }">Links</RouterLink>
         </li>
      </ul>
      <ul
            id="dropdown-menu-anon"
            class="dropdown-content">
         <li>
            <RouterLink :to="{ name: 'home' }">Log in</RouterLink>
         </li>
         <li>
            <RouterLink :to="{ name: 'register' }">Get an account</RouterLink>
         </li>
         <li>
            <RouterLink :to="{ name: 'forgot' }">Forgot your password?</RouterLink>
         </li>
      </ul>
      <ul
            id="dropdown-menu-user"
            class="dropdown-content">
         <li>
            <a :href="$router.resolve({ name: 'home' }).href"
                  @click="doLogout">Log out</a>
         </li>
         <li>
            <RouterLink :to="{ name: 'userprofile' }">Your profile</RouterLink>
         </li>
      </ul>
   </div>

   <nav class="white">
      <div class="nav-wrapper">
         <RouterLink :to="{ name: 'home' }"
               class="brand-logo">
            <span class="site-logo" />
         </RouterLink>
         <ul class="right hide-on-med-and-down">
            <li v-if="session && activeDictionary.config && activeDictionary.userAccess">
               <a class="dropdown-trigger"
                     href="#"
                     data-target="dropdown-menu-dict">
                  Dictionary {{ activeDictionary.title }}
                  <i class="material-symbols-outlined right">arrow_drop_down</i>
               </a>
            </li>
            <li v-if="!session">
               <a class="dropdown-trigger"
                     href="#"
                     data-target="dropdown-menu-anon">
                  anonymous user
                  <i class="material-symbols-outlined right">arrow_drop_down</i>
               </a>
            </li>
            <li v-if="session">
               <a class="dropdown-trigger"
                     href="#"
                     data-target="dropdown-menu-user">
                  {{ session.email }}
                  <i class="material-symbols-outlined right">arrow_drop_down</i>
               </a>
            </li>
         </ul>
      </div>
   </nav>

   <ul class="sidenav">
      <template v-if="session && activeDictionary.config && activeDictionary.userAccess">
         <li class="sideNavSection">
            <span>Dictionary</span>
         </li>
         <li v-if="activeDictionary.userAccess?.canEdit">
            <RouterLink :to="{ name: 'dictionary', params: { dictId: activeDictionary.dictId } }">View</RouterLink>
         </li>
         <li v-if="activeDictionary.userAccess?.canEdit">
            <RouterLink :to="{ name: 'edit', params: { dictId: activeDictionary.dictId } }">Edit</RouterLink>
         </li>
         <li v-if="activeDictionary.userAccess?.canConfig">
            <RouterLink :to="{ name: 'config', params: { dictId: activeDictionary.dictId } }">Configure</RouterLink>
         </li>
         <li v-if="activeDictionary.userAccess?.canDownload">
            <RouterLink :to="{ name: 'download', params: { dictId: activeDictionary.dictId } }">Download</RouterLink>
         </li>
         <li v-if="activeDictionary.userAccess?.canUpload">
            <RouterLink :to="{ name: 'upload', params: { dictId: activeDictionary.dictId } }">Upload</RouterLink>
         </li>
         <li>
            <RouterLink :to="{ name: 'links', params: { dictId: activeDictionary.dictId } }">Links</RouterLink>
         </li>
      </template>
      <template v-if="!session">
         <li>
            <RouterLink :to="{ name: 'home' }">Log in</RouterLink>
         </li>
         <li>
            <RouterLink :to="{ name: 'register' }">Get an account</RouterLink>
         </li>
         <li>
            <RouterLink :to="{ name: 'forgot' }">Forgot your password?</RouterLink>
         </li>
      </template>
      <template v-if="session">
         <li class="sideNavSection">
            <span>User</span>
         </li>
         <li>
            <a :href="$router.resolve({ name: 'home' }).href"
                  @click="doLogout">Log out</a>
         </li>
         <li>
            <RouterLink :to="{ name: 'userprofile' }">Your profile</RouterLink>
         </li>
      </template>
   </ul>
</app-header>
</template>

<script>
import Materialize from '../libs/materialize/materialize.min.js'
import { activeDictionary } from '../js/dictionary-workspace.ts'
import { logout, session } from '../js/auth.ts'
import { confirmEntryNavigation, unsavedEntry } from './entry-editor/unsaved.js'

export default {
   setup: () => ({ activeDictionary, session }),

   updated() {
      this.initializeMenus()
   },

   beforeMount() {
      const size = document.cookie.split('; ').find(cookie => cookie.startsWith('fontSize='))?.slice(9)
      if (Number(size) > 0) document.documentElement.style.fontSize = `${Number(size)}px`
   },

   mounted() {
      this.initializeMenus()
      Materialize.Sidenav.init(this.$el.querySelector('.sidenav'))
   },

   beforeUnmount() {
      this.menuTriggers?.forEach(element => Materialize.Dropdown.getInstance(element)?.destroy())
      Materialize.Sidenav.getInstance(this.$el.querySelector('.sidenav'))?.destroy()
   },

   methods: {
      initializeMenus() {
         const triggers = [...this.$el.querySelectorAll('.dropdown-trigger')]
         this.menuTriggers?.forEach(element => {
            if (!triggers.includes(element)) Materialize.Dropdown.getInstance(element)?.destroy()
         })
         for (const element of triggers) {
            if (!Materialize.Dropdown.getInstance(element)) {
               Materialize.Dropdown.init(element, {
                  container: this.$refs.dropdownMenus,
                  coverTrigger: false,
                  constrainWidth: false
               })
            }
         }
         this.menuTriggers = triggers
      },

      async doLogout(event) {
         event.preventDefault()
         if (this.loggingOut || !confirmEntryNavigation()) return
         this.loggingOut = true
         try {
            await logout()
            unsavedEntry.value = false
            await this.$router.replace({ name: 'home' })
         } catch {
            Materialize.toast({ html: 'Could not log out.' })
         } finally {
            this.loggingOut = false
         }
      }
   }
}
</script>

<style>
app-header .brand-logo{
   padding: 0 20px 0 40px;
}
app-header .site-logo{
   height: 40px;
   position: relative;
   top: 20px;
   width: 223px;
   background-image: url(/img/logo_lexonomy.png);
   background-size: contain;
   display: inline-block;
   background-repeat: no-repeat;
}
app-header .sidenav-trigger i{
   font-size: 36px;
}
app-header .sideNavSection{
   text-transform: uppercase;
   color: #767676;
   border-bottom: 1px solid #e0e0e0;
}
app-header .sideNavSection span{
   padding-left: 1rem;
}
app-header nav{
   border-bottom: 1px solid black;
   box-shadow: none;
}
</style>
