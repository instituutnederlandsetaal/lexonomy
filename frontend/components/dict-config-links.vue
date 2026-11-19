<template>
<dict-config-links>
   <LoadingOverlay v-if="state.isLoading || state.isSaving"/>
   <DictNav :links="[['config', 'Configure'], ['config-links', 'Linking']]"/>
   <h1>Manual linking between entries</h1>
   <DictConfigButtons :save-data="saveData"></DictConfigButtons>

   <div>
      <p>Elements listed here can be used as target of cross-reference link. For each element, specify unique identifier in the form of placeholders <code>'%(element)'</code>. Eg. element <code>entry</code> can have identifier <code>%(lemma)-%(pos)</code>, element <code>sense</code> can have identifier <code>%(lemma)-%(number)</code>. Optionally, specify element you want to show as preview when selecting links.</p>
      <template v-if="!state.isLoading">
         <table v-if="state.elements.length">
            <thead>
               <tr>
                  <th>Linking element</th>
                  <th>Identifier</th>
                  <th>Preview</th>
                  <th></th>
               </tr>
            </thead>
            <tbody>
               <tr v-for="(element, index) in state.elements" :key="index">
                  <td>
                     <div class="input-field">
                        <select v-model="element.linkElement">
                           <option :value="element.linkElement">{{ element.linkElement }}</option>
                           <option v-for="option in unusedElements" :key="option" :value="option">{{ option }}</option>
                        </select>
                     </div>
                  </td>
                  <td>
                     <div class="input-field">
                        <input type="text"
                              name="identifier" v-model.lazy="element.identifier" />
                     </div>
                  </td>
                  <td>
                     <div class="input-field">
                        <input type="text"
                              name="preview" v-model.lazy="element.preview"/>
                     </div>
                  </td>
                  <td>
                     <a class="btn btn-floating right"
                           :data-element="element.linkElement"
                           @click="doDeleteEl(element.linkElement)">
                        <i class="material-symbols-outlined">delete</i>
                     </a>
                  </td>
               </tr>
            </tbody>
         </table>
         <div class="buttons">
            <button type="button" class="btn" :disabled="!unusedElements.length"
                  @click="doAddEl">
               add element
               <i class="material-symbols-outlined right">add</i>
            </button>
         </div>
      </template>
   </div>
</dict-config-links>
</template>

<script>
import { activeDictionary, dictionaryWorkspace } from '../js/dictionary-workspace.ts'
import DictConfigButtons from './dict-config-buttons.vue'
import DictNav from './dict-nav.vue'
import LoadingOverlay from './loading-overlay.vue'
import { materializeSelects } from './form-select.js'
export default {
   setup: () => ({ activeDictionary }),
   components: { DictConfigButtons, DictNav, LoadingOverlay },
   mixins: [materializeSelects],

   data() {
      return {
         state: {
            isLoading: true,
            isSaving: false,
            elements: []
         }
      }
   },

   async mounted() {
      const response = await dictionaryWorkspace.loadDictionaryConfig('links')
      if (response) {
         this.state.elements = Object.values(response.content).filter(el => el.linkElement != undefined)
      }
      this.state.isLoading = false
   },

   computed: {
      unusedElements() {
         const used = new Set(this.state.elements.map(element => element.linkElement))
         return Object.keys(this.activeDictionary.config?.xema?.elements || {}).filter(element => !used.has(element))
      }
   },

   methods: {
      doDeleteEl(name) {
         this.state.elements = this.state.elements.filter(element => element.linkElement !== name)
      },

      doAddEl() {
         const linkElement = this.unusedElements[0]
         if (linkElement) this.state.elements.push({linkElement, identifier: '', preview: ''})
      },

      async saveData() {
         var data = {}
         this.state.elements.forEach(item => {
            data[item.linkElement] = item
         })
         this.state.isSaving = true
         await dictionaryWorkspace.updateDictionaryConfig("links", data)
         this.state.isSaving = false
      }
   }
}
</script>

<style>
dict-config-links tbody tr{
   border-bottom: none;
}
dict-config-links th, dict-config-links td{
   padding: 10px 10px 0 0;
}
dict-config-links td{
   vertical-align: top;
}
dict-config-links td .input-field{
   margin: 0;
}
</style>
