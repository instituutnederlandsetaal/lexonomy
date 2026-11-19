<template>
<dict-list>
   <LoadingOverlay v-if="state.isLoading || myDictionaries.loading"/>
   <template v-if="!myDictionaries.loading">
      <div v-if="myDictionaries.items.length">
         <h1>Your dictionaries</h1>
         <div style="display: flex; align-items: center; flex-wrap: wrap;">
            <span v-if="myDictionaries.items.length"
                  class="searchBox input-field">
                  <i class="material-symbols-outlined prefix">search</i>
               <input id="searchBox" placeholder="search"
                     v-model="state.query">
               <i @click="onClearFilterClick"
                  class="material-symbols-outlined clearFilterIcon clickable">close</i>
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
                     <span class="dict-lang grey-text">{{ dict.size }} {{ dict.size === 1 ? 'entry' : 'entries' }}</span>
                  <a v-if="dict.currentUserCanDelete"
                        class="secondary-content clickable"
                        title="delete dictionary"
                        @click="doDeleteDict(dict.id, $event)">
                     <i class="material-symbols-outlined">delete</i>
                  </a>
                  <a class="secondary-content clickable"
                        title="clone dictionary"
                        @click="doCloneDict(dict.id, $event)">
                     <i class="material-symbols-outlined">control_point_duplicate</i>
                  </a>
                  <a  v-if="dict.currentUserCanDelete"
                        class="secondary-content clickable"
                        title="config dictionary"
                        @click="doConfigDict(dict.id, $event)">
                     <i class="material-symbols-outlined">settings</i>
                  </a>
                  <a v-if="dict.currentUserCanEdit"
                        class="secondary-content clickable"
                        :data-dict-id="dict.id"
                        title="edit dictionary"
                        @click="doEditDict(dict.id, $event)">
                     <i class="material-symbols-outlined">edit</i>
                  </a>
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
</dict-list>
</template>

<script>
import { myDictionaries, cloneDictionary, deleteDictionary } from '../js/my-dictionaries.ts'
import LoadingOverlay from './loading-overlay.vue'
import FuzzySort from '../libs/fuzzysort/fuzzysort.js'
import FuzzyHighlight from './FuzzyHighlight.js'

export default {
   setup: () => ({ myDictionaries }),
   components: { LoadingOverlay, FuzzyHighlight },

   data() {
      return {
         state: { isLoading: false, query: '' }
      }
   },

   computed: {
      visibleDictionaries() {
         const dictionaries = myDictionaries.items
         if (!this.state.query) {
            return dictionaries.map(dict => ({ dict }))
         }
         return FuzzySort.go(this.state.query, dictionaries, { keys: ['title'] })
            .sort((a, b) => b.score - a.score || a.obj.title.localeCompare(b.obj.title))
            .map(result => ({ dict: result.obj, match: result[0] }))
      }
   },

   methods: {
      onClearFilterClick() {
         this.state.query = ''
      },

      doEditDict(dictId) {
         this.$router.push({ name: 'edit', params: { dictId } })
      },

      doConfigDict(dictId) {
         this.$router.push({ name: 'config', params: { dictId } })
      },

      async doCloneDict(dictId) {
         this.state.isLoading = true
         const clonedDictId = await cloneDictionary(dictId)
         this.state.isLoading = false
         if (clonedDictId) this.$router.push({ name: 'dictionary', params: { dictId: clonedDictId } })
      },

      async doDeleteDict(dictId) {
         const dictTitle = myDictionaries.items.find(dict => dict.id === dictId)?.title || dictId
         if (confirm("Are you sure you want to delete dictionary " + dictTitle + "? You will not be able to undo this.")) {
            this.state.isLoading = true
            await deleteDictionary(dictId)
            this.state.isLoading = false
         }
      }
   }
}
</script>

<style>
   dict-list .searchBox{
      max-width: 200px;
      display: inline-block;
      margin: 0 15px 0 0;
      border-bottom: 2px solid #004494;
   }
   dict-list .searchBox input{
      padding-right: 27px;
      border: unset;
      background-color: #F0F8FF !important;
   }
dict-list .searchBox input:focus{
      border: unset !important;
      outline: unset !important;
}
dict-list .searchBox input::placeholder{
      color: #004494;
}
   dict-list .clearFilterIcon{
      position: absolute;
      right: 5px;
      top: 11px;
   }
   dict-list .dict-lang {
      padding-left: 0.5em;
   }
   dict-list ul li{
      position: relative;
   }
   dict-list ul li:hover{
      background-color: #f8f8f8f2!important;
   }
   dict-list .title{
      padding-left: 35px;
   }
</style>
