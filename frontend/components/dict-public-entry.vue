<template>
<dict-public-entry @click="followCrossReference">
   <LoadingOverlay v-if="activeDictionary.isDictionaryLoading || (activeDictionary.isEntryListLoading && !activeDictionary.entryList)"/>
   <DictNav :links="[['entry', 'View', { entryId: $route.params.entryId }]]"/>
   <h1 v-if="activeDictionary.title"
         class="header">
      {{ activeDictionary.title }}
   </h1>
   <div v-if="activeDictionary.public && activeDictionary.entryList">
      <div class="row">
         <div class="col s4 leftCol">
            <LoadingOverlay v-if="activeDictionary.isEntryListLoading"/>
            <DictEntryFilter @search="searchEntriesFromRoute"/>
            <div v-if="activeDictionary.entryCount > activeDictionary.entryList.length" class="entriesCountInfo">
               Showing {{ activeDictionary.entryList.length }} of {{ activeDictionary.entryCount }} entries.
            </div>
            <div class="entry-list collection">
               <div v-for="(entry, idx) in activeDictionary.entryList" :key="entry.id"
                     class="collection-item" :class="{ selected: entry.id == activeDictionary.entryId }">
                  <span class="lineNum">{{ idx + 1 }}.</span>
                  <RouterLink :to="{ name: 'entry', params: { dictId: activeDictionary.dictId, entryId: entry.id }, query: $route.query }"
                        class="headword-link" :class="{ 'red-text': entry.id == activeDictionary.entryId }">
                     <RawHtml :content="entry.title || '&amp;nbsp;'"/>
                  </RouterLink>
               </div>
               <div v-if="!activeDictionary.entryList.length" class="noEntries">
                  <h2 class="grey-text center-align">No entries</h2>
               </div>
            </div>
         </div>
         <div class="col s8">
            <div class="divider"></div>
            <EntryView/>
         </div>
      </div>
      <div class="divider"></div>
      <div class="section">
         {{ activeDictionary.licence }}
      </div>
   </div>
</dict-public-entry>
</template>

<script>
import { activeDictionary } from '../js/dictionary-workspace.ts'
import { searchEntriesFromRoute } from '../js/entry-search.ts'
import DictEntryFilter from './dict-entry-filter.vue'
import DictNav from './dict-nav.vue'
import EntryView from './entry-view.vue'
import LoadingOverlay from './loading-overlay.vue'
import RawHtml from './raw-html.vue'

export default {
   setup: () => ({ activeDictionary, searchEntriesFromRoute }),
   components: { DictEntryFilter, DictNav, EntryView, LoadingOverlay, RawHtml },

   methods: {
      async followCrossReference(event) {
         const link = event.target.closest('#viewer a.xref[data-text]')
         if (!link || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return

         event.preventDefault()
         const { dictId } = this.activeDictionary
         const request = searchEntriesFromRoute({ searchtext: link.dataset.text, modifier: 'substring' })
         const path = this.$route.path
         const results = await request
         if (results?.length && path === this.$route.path) {
            const params = { dictId, entryId: results[0].id }
            this.$router.push({ name: 'entry', params, query: this.$route.query })
         }
      }
   }
}
</script>

<style>
dict-public-entry .infoIcon{
   margin-left: 1.5rem;
}
dict-public-entry .infoIcon a{
   font-size: 1.8rem;
}
dict-public-entry .leftCol{
   position: relative;
   display: block;
   min-height: calc(100vh - 260px);
}
dict-public-entry .entry-list {
   max-height: 80vh;
   overflow-y: auto;
   margin: 0;
}
dict-public-entry .collection-item{
   position: relative;
   display: flex;
   border-left: 5px solid white;
   padding-left: 0.2rem;
}
dict-public-entry .collection-item .headword-link{
   text-decoration: none;
   font-size: 1.2rem;
   letter-spacing: 1px;
   margin-right: auto;
}
dict-public-entry .collection-item.selected{
   border-left-color: #000;
}
dict-public-entry .collection-item.focused{
   background-color: #eceff1;
}
dict-public-entry .lineNum{
   font-size: 0.8rem;
   color: #b8b8b8;
   margin-right: 10px;
   min-width: 30px;
   text-align: right;
}
dict-public-entry .noEntries{
   padding-top: 10vh;
}
</style>
