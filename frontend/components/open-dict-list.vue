<template>
<div class="open-dict-list">
	<nav v-if="session" class="nav-breadcrumbs">
      <div class="nav-wrapper">
         <RouterLink :to="{ name: 'home' }"
               class="breadcrumb">Dictionaries</RouterLink>
         <RouterLink :to="{ name: 'public-list' }"
               class="breadcrumb">Public dictionaries</RouterLink>
      </div>
	</nav>
   <h1>Public dictionaries</h1>
   <LoadingOverlay v-if="loading"/>
   <p v-else-if="failed" class="message messageError" role="alert">Dictionary list could not be loaded.</p>
   <div v-else>
      <div>
         <div class="input-field"
               style="display: inline-block; margin-right: 40px;">
           <i class="material-symbols-outlined prefix grey-text">search</i>
           <input id="search"
               type="text"
               v-model="query" ref="searchInput"
               style="width: 200px;">
           <label for="search">Find</label>
         </div>
         <div class="language-filter">
            <label for="languageSelect">
               <span class="material-symbols-outlined grey-text" aria-hidden="true">translate</span>
               Language
            </label>
            <FormSelect id="languageSelect" v-model="language" :options="languages"/>
         </div>
      </div>
      <div v-if="!visibleDictionaries.length"
            class="center"
            style="margin: 20vh auto;">
         <h1 class="grey-text lighten-2">Nothing found</h1>
      </div>
      <table v-if="visibleDictionaries.length"
            class="striped highlight"
            style="margin: 0 15px;">
         <thead>
            <tr>
               <th>Title</th>
               <th>Language</th>
               <th>Number of entries</th>
               <th>Licence</th>
               <th></th>
            </tr>
         </thead>
         <tbody>
            <tr v-for="{ row, matches } in visibleDictionaries" :key="row.id">
               <td>
                  <RouterLink :to="{ name: 'dictionary', params: { dictId: row.id } }">
                     <FuzzyHighlight :match="matches?.[0]" :text="row.title"/>
                  </RouterLink>
               </td>
               <td><FuzzyHighlight :match="matches?.[1]" :text="row.lang"/></td>
               <td>{{ row.size }}</td>
               <td><FuzzyHighlight :match="matches?.[2]" :text="row.licence"/></td>
               <td>
                  <RouterLink v-if="row.isAdmin"
                        :to="{ name: 'edit', params: { dictId: row.id } }"
                        title="edit dictionary">
                     <i class="material-symbols-outlined">edit</i>
                  </RouterLink>
               </td>
            </tr>
         </tbody>
      </table>
   </div>
</div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, shallowRef } from 'vue'
import fuzzysort from 'fuzzysort'
import { fetchPublicDictionaries, type PublicDictionary } from '../js/public-dictionary-api.ts'
import { session } from '../js/auth.ts'
import FormSelect from './FormSelect.vue'
import LoadingOverlay from './loading-overlay.vue'
import FuzzyHighlight from './FuzzyHighlight.ts'

const searchInput = ref<HTMLInputElement | null>(null)
const language = ref('')
const query = ref('')
const dictionaries = shallowRef<PublicDictionary[]>([])
const loading = ref(true)
const failed = ref(false)

const languages = computed(() => {
   const names = new Set(dictionaries.value.flatMap(row => row.lang ? [row.lang] : []))
   return [{ value: '', label: 'All languages' }, ...[...names].sort().map(name => ({ value: name, label: name }))]
})

const visibleDictionaries = computed(() => {
   const rows = language.value ? dictionaries.value.filter(row => row.lang === language.value) : dictionaries.value
   const term = query.value.trim()
   if (!term) return rows.map(row => ({ row, matches: null }))
   return [...fuzzysort.go(term, rows, { keys: ['title', 'lang', 'licence'] })]
      .sort((a, b) => b.score - a.score || a.obj.title.localeCompare(b.obj.title))
      .map(matches => ({ row: matches.obj, matches }))
})

onMounted(async () => {
   try {
      dictionaries.value = await fetchPublicDictionaries()
   } catch {
      failed.value = true
   } finally {
      loading.value = false
   }
   await nextTick()
   searchInput.value?.focus()
})
</script>

<style scoped>
.language-filter {
   display: inline-block;
   width: 200px;
}
.language-filter label {
   display: flex;
   align-items: center;
   gap: .4rem;
}
</style>
