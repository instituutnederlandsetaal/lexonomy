<template>
<open-dict-list>
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
   <div v-else>
      <div>
         <div class="input-field"
               style="display: inline-block; margin-right: 40px;">
           <i class="material-symbols-outlined prefix grey-text">search</i>
           <input id="search"
               type="text"
               v-model="state.query"
               style="width: 200px;">
           <label for="search">Find</label>
         </div>
         <div class="input-field"
               style="display: inline-block;">
            <i class="material-symbols-outlined prefix grey-text">translate</i>
            <select id="languageSelect" ref="languageSelect"
                  @change="state.language = $event.target.value" style="width: 200px;">
               <option value="">All languages</option>
               <option v-for="language in languages"
                     :key="language" :value="language">{{ language }}</option>
            </select>
            <label>Language</label>
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
</open-dict-list>
</template>

<script>
import Materialize from '../libs/materialize/materialize.min.js'
import LoadingOverlay from './loading-overlay.vue'
import { api } from '../js/api.ts'
import { session } from '../js/auth.ts'
import FuzzySort from '../libs/fuzzysort/fuzzysort.js'
import FuzzyHighlight from './FuzzyHighlight.js'

export default {
   components: { LoadingOverlay, FuzzyHighlight },
   setup: () => ({ session }),

   data() {
      return { state: { language: '', query: '' }, dictionaries: [], loading: true }
   },

   computed: {
      languages() {
         return [...new Set(this.dictionaries.map(row => row.lang).filter(Boolean))]
      },

      visibleDictionaries() {
         let rows = this.dictionaries
         if (this.state.language) {
            rows = rows.filter(row => row.lang === this.state.language)
         }
         if (!this.state.query) {
            return rows.map(row => ({ row }))
         }
         return FuzzySort.go(this.state.query, rows, { keys: ['title', 'lang', 'licence'] })
            .sort((a, b) => b.score - a.score || a.obj.title.localeCompare(b.obj.title))
            .map(matches => ({ row: matches.obj, matches }))
      }
   },

   async mounted() {
      try {
         const { entries } = await api.get('publicdicts.json')
         this.dictionaries = entries || []
      } catch {
         Materialize.toast({ html: 'Dictionary list could not be loaded.' })
      } finally {
         this.loading = false
      }
      await this.$nextTick()
      if (!this.$refs.languageSelect) return
      Materialize.FormSelect.init(this.$refs.languageSelect, { dropdownOptions: { constrainWidth: false } })
      this.$el.querySelector('#search')?.focus()
   },

   beforeUnmount() {
      if (this.$refs.languageSelect) {
         Materialize.FormSelect.getInstance(this.$refs.languageSelect)?.destroy()
      }
   }
}
</script>
