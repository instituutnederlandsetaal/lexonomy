<template>
<div class="dict-public">
   <DictNav/>
   <LoadingOverlay v-if="activeDictionary.isDictionaryLoading || activeDictionary.isEntryListLoading"/>
   <template v-if="activeDictionary.config">
      <h1 class="header">{{ activeDictionary.title }}</h1>
      <div v-if="session" class="dictBtns buttons">
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
         <RouterLink v-if="activeDictionary.public || activeDictionary.userAccess" :to="{ name: 'links', params: { dictId: activeDictionary.dictId } }"
               class="btn">links</RouterLink>
      </div>

      <div>
         <div class="firstRowContainer">
            <div class="firstRowCol description">
               <h3>Description</h3>
               <RawHtml :content="activeDictionary.blurb"/>
            </div>
            <template v-if="activeDictionary.public || activeDictionary.userAccess">
               <div class="sectionDivider"></div>
               <div class="firstRowCol">
                  <h3>Search</h3>
                  <DictEntryFilter :flags="activeDictionary.config.flagging.flags ?? []"/>
                  <div v-if="!activeDictionary.isEntryListLoading && showFoundEntries && activeDictionary.entryList"
                        class="searchResult">
                     <ul v-if="activeDictionary.entryList.length"
                           class="entry-list found-entries">
                        <li v-for="entry in activeDictionary.entryList" :key="entry.id">
                           <RouterLink :to="entryLocation(entry)">
                              <RawHtml :content="entry.title"/>
                           </RouterLink>
                        </li>
                     </ul>
                     <div v-if="activeDictionary.entryCount > activeDictionary.entryList.length"
                           class="searchResultNote grey-text">
                           Showing {{ activeDictionary.entryList.length }} of {{ activeDictionary.entryCount }} entries.
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
            <button v-if="examples?.more || examplesFailed" type="button" aria-label="Refresh random entries"
                  :disabled="examplesLoading"
                  class="refreshExamplesBtn btn btn-floating waves-effect waves-light right"
                  @click="loadExamples">
               <i class="material-symbols-outlined" aria-hidden="true">autorenew</i>
            </button>
            <h3>Random entries</h3>
            <div v-if="examplesLoading"
                  class="loadingExamples grey-text">
               Loading...
            </div>
            <p v-if="examplesFailed" role="alert">Could not load random entries.</p>
            <p v-else-if="examples && !examples.entries.length && !examplesLoading">No entries.</p>
            <ul v-if="!examplesLoading && examples?.entries.length"
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
</div>
</template>

<script setup lang="ts">
import { computed, ref, shallowRef, watch } from 'vue'
import { useRoute, type RouteLocationRaw } from 'vue-router'
import { activeDictionary } from '../js/dictionary-workspace.ts'
import { fetchExamples, type Examples } from '../js/public-dictionary-api.ts'
import { session } from '../js/auth.ts'
import DictEntryFilter from './dict-entry-filter.vue'
import DictNav from './dict-nav.vue'
import LoadingOverlay from './loading-overlay.vue'
import RawHtml from './raw-html.vue'

const route = useRoute()
const examples = shallowRef<Examples | null>(null)
const requestingExamples = shallowRef<Promise<Examples> | null>(null)
const examplesFailed = ref(false)
const publicDictionaryId = computed(() =>
   activeDictionary.public && activeDictionary.dictId === route.params.dictId ? activeDictionary.dictId : null
)
const showFoundEntries = computed(() => route.query.s !== undefined || Boolean(route.query.f))
const examplesLoading = computed(() => requestingExamples.value !== null)

watch(publicDictionaryId, (dictId, _, onCleanup) => {
   examples.value = null
   examplesFailed.value = false
   if (!dictId) return
   onCleanup(() => { requestingExamples.value = null })
   void loadExamples()
}, { immediate: true })

async function loadExamples() {
   const dictId = publicDictionaryId.value
   if (!dictId || requestingExamples.value) return
   examplesFailed.value = false
   const request = fetchExamples(dictId)
   requestingExamples.value = request
   try {
      const response = await request
      if (requestingExamples.value === request) examples.value = response
   } catch {
      if (requestingExamples.value === request) examplesFailed.value = true
   } finally {
      if (requestingExamples.value === request) requestingExamples.value = null
   }
}

function entryLocation(entry: { id: number; doctype: string }): RouteLocationRaw {
   const { dictId, doctype, userAccess } = activeDictionary
   const params = { dictId, entryId: entry.id }
   return userAccess?.canEdit
      ? { name: 'edit', params: { ...params, doctype: entry.doctype || doctype, mode: 'view' }, query: route.query }
      : { name: 'entry', params, query: route.query }
}
</script>

<style>
.dict-public .dictBtns{
   margin-top: 5px;
}
.dict-public .firstRowContainer{
   display: flex;
}
.dict-public .sectionDivider{
   width: 1px;
   border-left: 1px solid #e0e0e0;
   padding-left: 30px;
   margin-left: 30px;
}
.dict-public .firstRowCol{
   flex: 1;
   padding-bottom: 30px;
}
.dict-public .description{
   word-break: break-word;
}
.dict-public .dict-entry-filter{
   max-width: 500px;
}
.dict-public .searchResult{
   min-height: max(15vh, 200px);
}
.dict-public .searchResultNote{
   font-size: 0.8rem;
   margin-left: 10px;
}
.dict-public .noEntries{
   padding-top: 30px;
}
.dict-public .entry-list {
   display: grid;
   grid-template-columns: repeat(auto-fill, minmax(min(100%, 12rem), 1fr));
}
.dict-public .entry-list li {
   min-width: 0;
   overflow-wrap: anywhere;
   padding: 3px 10px;
}
.dict-public .entry-list li a:hover {
   text-decoration: underline;
}
.dict-public .refreshExamplesBtn{
   margin-top: 15px;
}
.dict-public .loadingExamples{
   min-height: 20px;
   margin: 15px 10px;
}
.dict-public .licence{
   opacity: .5;
}
</style>
