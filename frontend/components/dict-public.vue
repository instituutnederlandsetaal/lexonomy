<template>
<dict-public>
   <DictNav/>
   <LoadingOverlay v-if="activeDictionary.isDictionaryLoading || activeDictionary.isEntryListLoading"/>
   <template v-if="activeDictionary.config">
      <h1 class="header">
         {{ activeDictionary.title }}
         <div class="dictBtns buttons">
            <RouterLink v-if="activeDictionary.userAccess?.canEdit"
                  :to="{ name: 'edit', params: { dictId: activeDictionary.dictId } }"
                  class="btn">edit</RouterLink>
            <RouterLink v-if="activeDictionary.userAccess?.canConfig"
                  :to="{ name: 'config', params: { dictId: activeDictionary.dictId } }"
                  class="btn">config</RouterLink>
            <RouterLink v-if="activeDictionary.userAccess?.canUpload"
                  :to="{ name: 'upload', params: { dictId: activeDictionary.dictId } }"
                  class="btn">upload</RouterLink>
            <RouterLink v-if="activeDictionary.userAccess?.canDownload"
                  :to="{ name: 'download', params: { dictId: activeDictionary.dictId } }"
                  class="btn">download</RouterLink>
            <RouterLink v-if="session" :to="{ name: 'links', params: { dictId: activeDictionary.dictId } }"
                  class="btn">links</RouterLink>
         </div>
      </h1>

      <div>
         <div class="firstRowContainer">
            <div class="firstRowCol description">
               <h3>Description</h3>
               <RawHtml :content="activeDictionary.blurb"></RawHtml>
            </div>
            <template v-if="activeDictionary.public || activeDictionary.userAccess">
               <div class="sectionDivider"></div>
               <div class="firstRowCol">
                  <h3>Search</h3>
                  <DictEntryFilter @search="searchEntriesFromRoute"/>
                  <div v-if="!activeDictionary.isEntryListLoading && showFoundEntries && activeDictionary.entryList"
                        class="searchResult">
                     <ul v-if="activeDictionary.entryList.length"
                           class="entry-list found-entries">
                        <li v-for="entry in activeDictionary.entryList" :key="entry.id">
                           <RouterLink :to="entryLocation(entry)">
                              <RawHtml :content="entry.title"></RawHtml>
                           </RouterLink>
                        </li>
                     </ul>
                     <div v-if="activeDictionary.entryCount > 20"
                           class="searchResultNote grey-text">
                           Showing first 20 entries of {{ activeDictionary.entryCount }}.
                     </div>
                     <div v-if="!activeDictionary.entryList.length"
                           class="noEntries">
                         <h2 class="grey-text center-align">No entries</h2>
                     </div>
                  </div>
               </div>
            </template>
         </div>

         <div v-if="activeDictionary.public">
            <div class="divider"></div>
            <a v-if="examples?.more"
                  class="refreshExamplesBtn btn btn-floating waves-effect waves-light right"
                  @click="loadExamples">
               <i class="material-symbols-outlined">autorenew</i>
            </a>
            <h3>Random entries</h3>
            <div v-if="examplesLoading"
                  class="loadingExamples grey-text">
               Loading...
            </div>
            <ul v-if="!examplesLoading && examples"
                  class="entry-list random-entries">
               <li v-for="entry in examples.entries" :key="entry.id">
                  <RouterLink :to="{ name: 'entry', params: { dictId: activeDictionary.dictId, entryId: entry.id } }">{{ entry.titlePlain }}</RouterLink>
               </li>
            </ul>
            <div class="divider"></div>
            <div class="licence section right">
               {{ activeDictionary.licence }}
            </div>
         </div>
      </div>
   </template>
</dict-public>
</template>

<script>
import Materialize from '../libs/materialize/materialize.min.js'
import { activeDictionary } from '../js/dictionary-workspace.ts'
import { searchEntriesFromRoute } from '../js/entry-search.ts'
import DictEntryFilter from './dict-entry-filter.vue'
import DictNav from './dict-nav.vue'
import LoadingOverlay from './loading-overlay.vue'
import RawHtml from './raw-html.vue'
import { api } from '../js/api.ts'
import { session } from '../js/auth.ts'

export default {
   components: { DictEntryFilter, DictNav, LoadingOverlay, RawHtml },
   setup: () => ({ activeDictionary, searchEntriesFromRoute, session }),

   data() {
      return { examples: null, examplesLoading: false }
   },

   computed: {
      showFoundEntries() {
         return this.$route.query.s !== undefined || Boolean(this.$route.query.f)
      }
   },

   watch: {
      'activeDictionary.public': {
         immediate: true,
         handler(isPublic) { if (isPublic) this.loadExamples() }
      }
   },

   updated() {
      // Preserve evenly sized columns across each set of results.
      this.$el.querySelectorAll('.entry-list').forEach(list => {
         const items = [...list.children]
         items.forEach(item => { item.style.width = '' })
         const maxWidth = Math.max(0, ...items.map(item => item.getBoundingClientRect().width))
         items.forEach(item => { item.style.width = Math.min(300, maxWidth) + 'px' })
      })
   },

   methods: {
      async loadExamples() {
         if (this.examplesLoading) return
         this.examplesLoading = true
         try {
            this.examples = await api.post(`${encodeURIComponent(this.activeDictionary.dictId)}/random.json`)
         } catch {
            Materialize.toast({ html: 'Could not load the examples.' })
         } finally {
            this.examplesLoading = false
         }
      },

      entryLocation(entry) {
         const { dictId, doctype, userAccess } = this.activeDictionary
         const params = { dictId, entryId: entry.id }
         const query = this.$route.query
         return userAccess?.canEdit
            ? { name: 'edit', params: { ...params, doctype: entry.doctype || doctype, mode: 'view' }, query }
            : { name: 'entry', params, query }
      }
   }
}
</script>

<style>
dict-public .dictBtns{
   margin-top: 5px;
}
dict-public .firstRowContainer{
   display: flex;
}
dict-public .sectionDivider{
   width: 1px;
   border-left: 1px solid #e0e0e0;
   padding-left: 30px;
   margin-left: 30px;
}
dict-public .firstRowCol{
   flex: 1;
   padding-bottom: 30px;
}
dict-public .description{
   word-break: break-word;
}
dict-public dict-entry-filter{
   max-width: 500px;
}
dict-public .searchResult{
   min-height: max(15vh, 200px);
}
dict-public .searchResultNote{
   font-size: 0.8rem;
   margin-left: 10px;
}
dict-public .noEntries{
   padding-top: 30px;
}
dict-public .entry-list li {
   display: inline-block;
   padding: 3px 10px;
}
dict-public .entry-list li a:hover {
   text-decoration: underline;
}
dict-public .refreshExamplesBtn{
   margin-top: 15px;
}
dict-public .loadingExamples{
   min-height: 20px;
   margin: 15px 10px;
}
dict-public .licence{
   opacity: .5;
}
</style>
