<template>
<dict-links>
   <LoadingOverlay v-if="state.isLoading"></LoadingOverlay>
   <DictNav :links="[['links', 'links']]"/>
   <h1>Links</h1>
   <template v-if="!state.isLoading">
      <div v-if="!Object.values(state.dictionaries).length"
            class="grey-text">
         <h2>No links</h2>
      </div>
      <div v-for="dict in Object.values(state.dictionaries)" :key="dict.dictId">
         <div>
            <a @click="showDict(dict.dictId)" style="cursor: pointer;">{{ dict.title }}</a>
         </div>
      </div>
      <div v-for="dict in Object.values(state.dictionaries)" :key="dict.dictId">
         <div>
            <h2 class="dictName" :id="`dictLinks-${dict.dictId}`">
               {{ dict.title }}
               <i v-if="dict.blurb"
                     class="material-symbols-outlined clickable"
                     @click="openDictInfo(dict, $event)">
                  info
               </i>
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
   <div ref="dictionaryModal" id="modalDictionary" class="modal">
      <div class="modal-content">
         <h2>{{ state.modalDictionary?.title }}</h2>
         <RawHtml :content="state.modalDictionary?.blurb"/>
      </div>
      <div class="modal-footer">
         <a class="btn modal-close waves-effect waves-green">Close</a>
      </div>
   </div>
</dict-links>
</template>

<script>
import Materialize from '../libs/materialize/materialize.min.js'
import { activeDictionary } from '../js/dictionary-workspace.ts'
import DictNav from './dict-nav.vue'
import LoadingOverlay from './loading-overlay.vue'
import RawHtml from './raw-html.vue'
import { api } from '../js/api.ts'
import { linkedEntryLocation } from '../js/linked-entry-location.ts'

export default {
   setup: () => ({ activeDictionary, linkedEntryLocation }),
   components: { DictNav, LoadingOverlay, RawHtml },
   data() {
      return {
         state: {
            dictionaries: Object.create(null),
            isLoading: true,
            modalDictionary: null
         }
      }
   },

   async mounted() {
      Materialize.Modal.init(this.$refs.dictionaryModal)
      const dictId = this.activeDictionary.dictId
      try {
         const { links } = await api.get(`${encodeURIComponent(dictId)}/links.json`)
         this.processLinks(links, 'to')
         this.processLinks(links, 'from')
         await Promise.all(Object.values(this.state.dictionaries).map(async dict => {
            if (dict.isExternal) return
            if (dict.dictId === dictId && this.activeDictionary.config && this.activeDictionary.dictId === dictId) {
               Object.assign(dict, { title: this.activeDictionary.title, blurb: this.activeDictionary.blurb })
               return
            }
            try {
               const config = await api.get(`${encodeURIComponent(dict.dictId)}/config.json`)
               if (config.success) {
                  const { title, blurb } = config.publicInfo
                  Object.assign(dict, { title, blurb })
               }
            } catch {
               // The dictionary ID is already shown when its description is unavailable.
            }
         }))
      } catch {
         Materialize.toast({ html: 'Dictionary links could not be loaded.' })
      } finally {
         this.state.isLoading = false
      }
   },

   beforeUnmount() {
      Materialize.Modal.getInstance(this.$refs.dictionaryModal)?.destroy()
   },

   methods: {
      processLinks(links, direction){
         links[direction].forEach(link => {
            let dictId = direction == "from" ? link.source_dict : link.target_dict
            if(!this.state.dictionaries[dictId]){
               this.state.dictionaries[dictId] = {
                  dictId: dictId,
                  title: dictId,
                  isExternal: dictId === "BABELNET",
                  from: [],
                  to: []
               }
            }
            this.state.dictionaries[dictId][direction].push(link)
         })
      },

      openDictInfo(dict){
         this.state.modalDictionary = dict
         Materialize.Modal.getInstance(this.$refs.dictionaryModal).open()
      },

      showDict(dictId){
         document.getElementById(`dictLinks-${dictId}`)?.scrollIntoView()
      }
   }
}
</script>

<style>
dict-links .dictName{
   border-bottom: 1px solid #d9d9d8;
}
dict-links .dictName i{
   margin-left: 10px;
}
dict-links .dictLinks{
   display: flex;
   column-gap: 6vw;
   padding-left: 10px;
}
dict-links .arrowCell{
   color: #cbcbcb ;
   padding: 0 20px;
}
</style>
