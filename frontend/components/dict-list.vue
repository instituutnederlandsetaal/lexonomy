<template>
<div class="dict-list">
   <LoadingOverlay v-if="mutating || myDictionaries.loading"/>
   <p v-if="myDictionaries.failed" role="alert">
      Your dictionaries could not be loaded.
      <button type="button" class="btn-flat" @click="loadMyDictionaries">Retry</button>
   </p>
   <template v-if="!myDictionaries.loading && (!myDictionaries.failed || myDictionaries.items.length)">
      <div v-if="myDictionaries.items.length">
         <h1>Your dictionaries</h1>
         <div style="display: flex; align-items: center; flex-wrap: wrap;">
            <span v-if="myDictionaries.items.length"
                  class="searchBox input-field">
                  <i class="material-symbols-outlined prefix">search</i>
               <input id="searchBox" ref="searchInput" placeholder="search"
                     v-model="query" aria-label="Search your dictionaries">
               <button v-if="query" type="button" class="material-symbols-outlined clearFilterIcon"
                     aria-label="Clear dictionary search" @click="clearSearch">close</button>
            </span>
            <span style="margin-left: auto; margin-right: 1em;">
               <RouterLink :to="{ name: 'public-list' }" style="color:#004494">Public dictionaries</RouterLink>
            </span>
            <span>
               <RouterLink :to="{ name: 'new' }"
                     class="btn waves-effect waves-light">
                  create a dictionary
                  <i class="material-symbols-outlined right">edit_note</i>
               </RouterLink>
            </span>
         </div>
         <ul v-if="visibleDictionaries.length"
               class="collection">
            <li v-for="{ dict, match } in visibleDictionaries"
                  :key="dict.id" class="collection-item">
               <div>
                  <RouterLink :to="{ name: 'dictionary', params: { dictId: dict.id } }" class="title">
                     <FuzzyHighlight :match="match" :text="dict.title"/>
                  </RouterLink>
                  <span v-if="dict.lang"
                        class="dict-lang">{{ dict.lang }}</span>
                     <span v-if="dict.size != null" class="dict-lang grey-text">
                     {{ dict.size }} {{ dict.size === 1 ? 'entry' : 'entries' }}
                  </span>
                  <span v-else-if="dict.broken" class="dict-lang grey-text">Unavailable</span>
                  <button v-if="dict.currentUserCanDelete" type="button"
                        class="secondary-content dictionary-action" :aria-label="'Delete ' + dict.title"
                        title="Delete dictionary" :disabled="mutating" @click="remove(dict.id, dict.title)">
                     <i class="material-symbols-outlined" aria-hidden="true">delete</i>
                  </button>
                  <button v-if="dict.currentUserCanDelete && !dict.broken" type="button"
                        class="secondary-content dictionary-action" :aria-label="'Clone ' + dict.title"
                        title="Clone dictionary" :disabled="mutating" @click="clone(dict.id)">
                     <i class="material-symbols-outlined" aria-hidden="true">control_point_duplicate</i>
                  </button>
                  <RouterLink v-if="dict.currentUserCanDelete"
                        :to="{ name: 'config', params: { dictId: dict.id } }"
                        class="secondary-content" :aria-label="'Configure ' + dict.title" title="Configure dictionary">
                     <i class="material-symbols-outlined" aria-hidden="true">settings</i>
                  </RouterLink>
                  <RouterLink v-if="dict.currentUserCanEdit"
                        :to="{ name: 'edit', params: { dictId: dict.id } }" class="secondary-content"
                        :data-dict-id="dict.id" :aria-label="'Edit ' + dict.title" title="Edit dictionary">
                     <i class="material-symbols-outlined" aria-hidden="true">edit</i>
                  </RouterLink>
               </div>
            </li>
         </ul>
         <div v-if="!visibleDictionaries.length"
               class="center"
               style="margin: 10vh auto;">
            <h1 class="grey-text lighten-2">Nothing found</h1>
         </div>
      </div>
      <div v-if="!myDictionaries.items.length"
            class="grey-text center-align">
         <h1>no dictionaries</h1>
         <div>
            You have no dictionary yet. Create one using button below.
            <br>
            <RouterLink :to="{ name: 'public-list' }" style="color:#004494">View public dictionaries</RouterLink>
         </div>
         <br>
         <RouterLink :to="{ name: 'new' }"
               class="btn waves-effect waves-light">
            <i class="material-symbols-outlined left">edit_note</i>
            create new dictionary
         </RouterLink>
      </div>
   </template>
</div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import fuzzysort from 'fuzzysort'
import { myDictionaries, loadMyDictionaries, cloneDictionary, deleteDictionary } from '../js/my-dictionaries.ts'
import LoadingOverlay from './loading-overlay.vue'
import FuzzyHighlight from './FuzzyHighlight.ts'

const router = useRouter()
const searchInput = ref<HTMLInputElement | null>(null)
const query = ref('')
const mutating = ref(false)

const visibleDictionaries = computed(() => {
   const term = query.value.trim()
   const dictionaries = myDictionaries.items
   if (!term) return dictionaries.map(dict => ({ dict, match: null }))
   return [...fuzzysort.go(term, dictionaries, { key: 'title' })]
      .sort((a, b) => b.score - a.score || a.obj.title.localeCompare(b.obj.title))
      .map(match => ({ dict: match.obj, match }))
})

function clearSearch() {
   query.value = ''
   searchInput.value?.focus()
}

async function clone(dictId: string) {
   if (mutating.value) return
   mutating.value = true
   const originalRoute = router.currentRoute.value
   try {
      const clonedDictId = await cloneDictionary(dictId)
      if (clonedDictId && router.currentRoute.value === originalRoute) {
         await router.push({ name: 'dictionary', params: { dictId: clonedDictId } })
      }
   } finally {
      mutating.value = false
   }
}

async function remove(dictId: string, title: string) {
   if (mutating.value || !confirm('Are you sure you want to delete dictionary ' + title + '? You will not be able to undo this.')) return
   mutating.value = true
   try {
      await deleteDictionary(dictId)
   } finally {
      mutating.value = false
   }
}
</script>

<style>
   .dict-list .searchBox{
      max-width: 200px;
      display: inline-block;
      margin: 0 15px 0 0;
      border-bottom: 2px solid #004494;
   }
   .dict-list .searchBox input{
      padding-right: 27px;
      border: unset;
      background-color: #F0F8FF !important;
   }
.dict-list .searchBox input:focus{
      border: unset !important;
      outline: unset !important;
}
.dict-list .searchBox input::placeholder{
      color: #004494;
}
   .dict-list .clearFilterIcon{
      position: absolute;
      right: 5px;
      top: 11px;
   }
   .dict-list button.dictionary-action, .dict-list .clearFilterIcon {
      border: 0;
      background: transparent;
      padding: 0;
      cursor: pointer;
   }
   .dict-list .dict-lang {
      padding-left: 0.5em;
   }
   .dict-list ul li{
      position: relative;
   }
   .dict-list ul li:hover{
      background-color: #f8f8f8f2!important;
   }
   .dict-list .title{
      padding-left: 35px;
   }
</style>
