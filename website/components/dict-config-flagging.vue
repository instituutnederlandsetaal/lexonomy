<template>
<dict-config-flagging>
   <LoadingOverlay v-if="state.isLoading || state.isSaving"/>
   <DictNav :links="[['config', 'Configure'], ['config-flagging', 'Entry flags']]"/>
   <h1>Entry flags</h1>
   <DictConfigButtons :save-data="saveData"></DictConfigButtons>
   <template v-if="!state.isLoading">
      <div v-if="!state.data.flags.length"
            class="center-align grey-text">
         <h1>no entry flags</h1>
         <br>
         <a class="btn btn-primary waves-effect waves-light"
               @click="doAddEl">
            add flag
            <i class="material-symbols-outlined right">add</i>
         </a>
      </div>

      <template v-if="state.data.flags.length">
         <table>
            <thead>
               <tr>
                  <th>Keyboard shortcut</th>
                  <th>Value</th>
                  <th>Label</th>
                  <th>Color</th>
                  <th></th>
               </tr>
            </thead>
            <tbody>
               <tr v-for="(flag, index) in state.data.flags" :key="index">
                  <td>
                     <input type="text"
                           v-model="flag.key"
                           placeholder="key"/>
                  </td>
                  <td>
                     <input type="text"
                           v-model="flag.name"
                           placeholder="value"/>
                  </td>
                  <td>
                     <input type="text"
                           v-model="flag.label"
                           placeholder="label"/>
                  </td>
                  <td>
                     <input type="text"
                           v-model="flag.color"
                           placeholder="color"
                           :style="{ color: flagTextColor(flag.color), backgroundColor: flag.color }"/>
                     <input type="color" aria-label="Choose flag color"
                           :value="/^#[a-f0-9]{6}$/i.test(flag.color) ? flag.color : '#000000'"
                           @input="flag.color = $event.target.value"/>
                  </td>
                  <td>
                     <a class="btn btn-flat"
                           @click="doDeleteEl(index)">
                        <i class="material-symbols-outlined">delete</i>
                     </a>
                  </td>
               </tr>
            </tbody>
         </table>
         <div>
            <a class="btn waves-effect waves-light"
                  @click="doAddEl">
               add flag
               <i class="material-symbols-outlined right">add</i>
            </a>
         </div>
         <br>
         <br>
         <div class="input-field"
               style="max-width: 400px;">
            <select id="flag-element" v-model="state.data.flag_element">
               <option v-for="name in flagElements" :key="name" :value="name">{{ name }}</option>
            </select>
            <label for="flag-element">Flag element</label>
            <span class="helper-text">Select the element which the flags should be put into.</span>
         </div>
      </template>
   </template>
   <br><br>
</dict-config-flagging>
</template>

<script>
import Materialize from '../libs/materialize/materialize.min.js'
import { flagTextColor } from './entry-flags.js'
import { activeDictionary, dictionaryWorkspace } from '../js/dictionary-workspace.ts'
import DictConfigButtons from './dict-config-buttons.vue'
import DictNav from './dict-nav.vue'
import LoadingOverlay from './loading-overlay.vue'
import { materializeSelects } from './form-select.js'
export default {
   setup: () => ({ activeDictionary, flagTextColor }),
   components: { DictConfigButtons, DictNav, LoadingOverlay },
   mixins: [materializeSelects],

   data() {
      return {
         state: {
            isLoading: true,
            isSaving: false,
            data: {flag_element: "", flags: []}
         }
      }
   },

   async mounted() {
      const response = await dictionaryWorkspace.loadDictionaryConfig('flagging')
      if (response) {
         this.state.data = response.content
      }
      this.state.isLoading = false
   },

   computed: {
      flagElements() {
         const xema = this.activeDictionary.config?.xema
         return Object.keys(xema?.elements || {}).filter(name => name !== xema.root)
      }
   },

   updated() {
      Materialize.updateTextFields()
   },

   methods: {
      doDeleteEl(idx) {
         this.state.data.flags.splice(idx, 1)
      },

      doAddEl() {
         if (!this.state.data.flag_element) this.state.data.flag_element = this.flagElements[0] || ''
         this.state.data.flags.push({key: "", name: "", label: "", color: ""})
      },

      async saveData() {
         this.state.isSaving = true
         await dictionaryWorkspace.updateDictionaryConfig("flagging", this.state.data)
         this.state.isSaving = false
      }
   }
}
</script>

<style>
dict-config-flagging tr{
   border-bottom: none;
}
dict-config-flagging th, dict-config-flagging td{
   padding: 3px 10px 3px 0;
}
</style>
