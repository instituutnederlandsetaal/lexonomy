<script setup lang="ts">
import { computed, ref, shallowRef, useTemplateRef, watch } from 'vue'
import { useRoute } from 'vue-router'
import { fetchDictionaryLinks, type LinkedDictionary } from '../js/dictionary-links-api.ts'
import { linkedEntryLocation } from '../js/linked-entry-location.ts'
import DictNav from './dict-nav.vue'
import LoadingOverlay from './loading-overlay.vue'
import RawHtml from './raw-html.vue'

const route = useRoute()
const dictId = computed(() => typeof route.params.dictId === 'string' ? route.params.dictId : '')
const loading = ref(false)
const failed = ref(false)
const dictionaries = shallowRef<LinkedDictionary[]>([])
const modalDictionary = shallowRef<LinkedDictionary | null>(null)
const dictionaryModal = useTemplateRef<HTMLDialogElement>('dictionaryModal')

watch(dictId, async (id, _, onCleanup) => {
   let current = true
   onCleanup(() => { current = false })
   dictionaries.value = []
   failed.value = false
   dictionaryModal.value?.close()
   modalDictionary.value = null
   loading.value = Boolean(id)
   if (!id) return
   try {
      const groups = await fetchDictionaryLinks(id)
      if (current) dictionaries.value = groups
   } catch {
      if (current) failed.value = true
   } finally {
      if (current) loading.value = false
   }
}, { immediate: true })

function openDictInfo(dict: LinkedDictionary) {
   modalDictionary.value = dict
   dictionaryModal.value?.showModal()
}

function showDict(id: string) {
   const heading = document.getElementById(`dictLinks-${id}`)
   heading?.scrollIntoView()
   heading?.focus({ preventScroll: true })
}
</script>

<template>
<section class="dict-links-page">
   <LoadingOverlay v-if="loading"></LoadingOverlay>
   <DictNav :links="[['links', 'Links']]"/>
   <h1>Links</h1>
   <p v-if="failed" role="alert">Dictionary links could not be loaded.</p>
   <template v-else-if="!loading">
      <div v-if="!dictionaries.length"
            class="grey-text">
         <h2>No links</h2>
      </div>
      <div v-for="dict in dictionaries" :key="dict.dictId">
         <div>
            <button type="button" class="dictionary-jump" @click="showDict(dict.dictId)">{{ dict.title }}</button>
         </div>
      </div>
      <div v-for="dict in dictionaries" :key="dict.dictId">
         <div>
            <h2 class="dictName" :id="`dictLinks-${dict.dictId}`" tabindex="-1">
               {{ dict.title }}
               <button v-if="dict.blurb" type="button" class="dictionary-jump material-symbols-outlined"
                     :aria-label="`About ${dict.title}`" @click="openDictInfo(dict)">
                  info
               </button>
               <RouterLink v-if="!dict.isExternal"
                     :to="{ name: 'dictionary', params: { dictId: dict.dictId } }"
                     class="btn right">open</RouterLink>
            </h2>
         </div>
         <div class="dictLinks">
            <div>
               <h3 class="title">Outgoing links</h3>
               <div v-if="!dict.to.length">
                  <h4 class="grey-text">No links</h4>
               </div>
               <table v-if="dict.to.length">
                  <tbody>
                     <tr v-for="link in dict.to" :key="link.link_id">
                        <td>
                           <RouterLink :to="linkedEntryLocation(link, 'source')">
                              {{ link.source_hw || link.source_id }}
                           </RouterLink>
                        </td>
                        <td class="grey-text">
                           {{ link.source_hw ? (link.source_el + ' ' + link.source_id) : '' }}
                           {{ link.source_preview ? (link.source_preview+'...') : '' }}
                        </td>
                        <td class="arrowCell">
                           <i class="material-symbols-outlined">arrow_forward</i>
                        </td>
                        <td>
                           <RouterLink v-if="!dict.isExternal"
                                 :to="linkedEntryLocation(link, 'target')">
                              {{ link.target_hw || (link.target_el + ' ' + link.target_id) }}
                           </RouterLink>
                           <span v-if="dict.isExternal">
                              {{ link.target_hw || (link.target_el + ' ' + link.target_id) }}
                           </span>
                        </td>
                        <td class="grey-text">
                           {{ link.target_hw ? (link.target_el + ' ' + link.target_id) : '' }}
                           {{ link.target_preview ? (link.target_preview+'...') : '' }}
                        </td>
                     </tr>
                  </tbody>
               </table>
            </div>

            <div>
               <h3 class="title">Incoming links</h3>
               <div v-if="!dict.from.length">
                     <h4 class="grey-text">No links</h4>
                  </div>
               <table v-if="dict.from.length">
                  <tbody>
                     <tr v-for="link in dict.from" :key="link.link_id">
                        <td>
                           <RouterLink :to="linkedEntryLocation(link, 'source')">
                              {{ link.source_hw || (link.source_el + ' ' + link.source_id) }}
                           </RouterLink>
                        </td>
                        <td class="grey-text">
                           {{ link.source_hw ? (link.source_el + ' ' + link.source_id) : '' }}
                           {{ link.source_preview ? (link.source_preview+'...') : '' }}
                        </td>
                        <td style="padding: 0 20px;"
                              class="grey-text">
                           <i class="material-symbols-outlined">arrow_forward</i>
                        </td>
                        <td>
                           <RouterLink :to="linkedEntryLocation(link, 'target')">
                              {{ link.target_hw || link.target_id }}
                           </RouterLink>
                        </td>
                        <td class="grey-text">
                           {{ link.target_hw ? (link.target_el + ' ' + link.target_id) : '' }}
                           {{ link.target_preview ? (link.target_preview+'...') : '' }}
                        </td>
                     </tr>
                  </tbody>
               </table>
            </div>
         </div>
      </div>
   </template>
   <dialog ref="dictionaryModal" class="dictionary-info" aria-labelledby="linked-dictionary-title">
      <h2 id="linked-dictionary-title">{{ modalDictionary?.title }}</h2>
      <RawHtml :content="modalDictionary?.blurb"/>
      <form method="dialog">
         <button class="btn waves-effect waves-green">Close</button>
      </form>
   </dialog>
</section>
</template>

<style>
.dict-links-page .dictName{
   border-bottom: 1px solid #d9d9d8;
}
.dict-links-page .dictName button{
   margin-left: 10px;
}
.dict-links-page .dictLinks{
   display: flex;
   column-gap: 6vw;
   padding-left: 10px;
}
.dict-links-page .arrowCell{
   color: #cbcbcb ;
   padding: 0 20px;
}
.dict-links-page .dictionary-jump {
   border: 0;
   background: transparent;
   color: #007dae;
   cursor: pointer;
   padding: 0;
}
.dict-links-page .dictionary-info {
   width: min(760px, calc(100vw - 36px));
   padding: 24px;
   border: 0;
}
.dict-links-page .dictionary-info::backdrop {
   background: #0008;
}
.dict-links-page .dictionary-info form {
   margin-top: 1rem;
   text-align: right;
}
</style>
