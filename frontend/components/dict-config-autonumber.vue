<template>
<dict-config-autonumber>
   <LoadingOverlay v-if="state.isSaving"/>
   <DictNav :links="[['config', 'Configure'], ['config-autonumber', 'Auto-numbering']]"/>
   <h1>Auto-numbering of elements</h1>
   <DictConfigButtons :save-data="saveData">
      <a class="btn waves-effect waves-light" @click="addNumbers">
         <i class="material-symbols-outlined right">add</i>Save &amp; autonumber
      </a>
   </DictConfigButtons>
   <div class="row">
      <p>If you need to number some of entry elements automatically, Lexonomy can do that for you. First, go to Entry structure and add element/attribute where you want to dictionaryWorkspace the number. Eg. in element <code>sense</code> add attribute <code>number</code>. When you're ready, select element to number (eg. <code>sense</code>) and element/attribute to dictionaryWorkspace numbering (eg. <code>@number</code>). Lexonomy will fill the numbers where missing.</p>
   </div>
   <hr>
   <template v-for="config in Object.values(state.data)" :key="config.element">
      <div class="row">
         <div class="input-field col s4">
            <select @change="changeElement(config, $event)" class="browser-default">
               <option selected :value="config.element">{{ config.element }}</option>
               <option v-for="el in getUnusedElements()" :value="el">{{ el }}</option>
            </select>
            <label>Element to number</label>
         </div>
         <!-- child/attribute selection -->
         <div class="input-field col s4">
            <select :name="(config.element) + ('_children')" @change="setWithEvent(config, 'target', $event)" class="browser-default">
               <option value="" :selected="config.target === ''">{{ config.element }} itself</option>
               <option v-for="attribute in getAttributesForElement(config.element)" :value="('@') + (attribute)" :selected="config.target === '@' + attribute">@{{ attribute }}</option>
               <option v-for="childElement in getChildElementsForElement(config.element)" :value="childElement" :selected="config.target === childElement">{{ childElement }}</option>
            </select>
            <label :for="(config.element) + ('children')">Add numbers to</label>
         </div>
         <div class="input-field col s4">
            <button type="button" class="btn waves-effect waves-light" @click="deleteElement(config.element)" style="height:3rem;">Remove</button>
         </div>

         <div class="col s12">
            <label>
               <input :name="(config.element) + ('_autoApply')" type="radio" class="with-gap" value="false" :checked="config.auto_apply" @change="set(config, 'auto_apply', true)"/>
               <span>Apply numbers automatically</span>
            </label>
            <br>
            <label>
               <input :name="(config.element) + ('_autoApply')" type="radio" class="with-gap" value="true" :checked="!config.auto_apply" @change="set(config, 'auto_apply', false)"/>
               <span>Only run numbering manually</span>
            </label>
         </div>

         <h3 class="col s12" style="margin-top: 2rem;">What to do with existing values</h3>
         <div class="col s12" style="padding-left: 2.75rem;">
            <label>
               <input :name="(config.element) + ('_existingValues')" type="radio" class="with-gap" value="false" :checked="!config.overwrite_existing" @change="set(config, 'overwrite_existing', false)"/>
               <span><b>Keep</b> existing values</span>
            </label>
            <br>
            <label>
               <input :name="(config.element) + ('_existingValues')" type="radio" class="with-gap" value="true" :checked="config.overwrite_existing" @change="set(config, 'overwrite_existing', true)"/>
               <span><b>Overwrite</b> existing values</span>
            </label>
         </div>

         <h3 class="col s12" style="margin-top: 2rem;">New values</h3>
         <div class="col s12" style="padding-left: 2.75rem;">
            <label>
               <input :name="(config.element) + ('_newValues')" type="radio" class="with-gap" value="number" :checked="config.type == 'number'" @change="setWithEvent(config, 'type', $event)" />
               <span>Use numbers</span>
            </label>
            <br>

            <label style="margin-left: 3rem; margin-top: 0.75rem;">
               <input :name="(config.element) + ('_useNumbers')" type="radio" class="with-gap" :disabled="config.type !== 'number'" :checked="!config.number_globally" @change="set(config, 'number_globally', false)"/>
               <span>Start at 0 in every entry</span>
            </label>
            <div style="margin-left: 3rem; display: flex; flex-wrap: wrap; align-items: baseline;">
               <label style="white-space: nowrap;">
                  <input style="margin-left: 0.75rem;" :name="(config.element) + ('_useNumbers')" type="radio" class="with-gap" :disabled="config.type !== 'number'" :checked="config.number_globally" @change="set(config, 'number_globally', true)"/>
                  <span>Keep counting up, starting from</span>
               </label>
               <input type="text" style="margin-left: 0.75rem; flex-basis: 5ch; flex-grow: 1;" :value="config.number_next" @change="setWithEvent(config, 'number_next', $event)"/>
               <button type="button" class="btn waves-effect waves-light" style="height: 3rem; flex-shrink: 0; margin-left: 0.75rem;" @click="findNext(config)">Find next number</button>
            </div>

            <label>
               <input :name="(config.element) + ('_newValues')" type="radio" class="with-gap" :checked="config.type == 'string'" @change="set(config, 'type', 'string')"/>
               <span>Use text</span>
            </label>

            <input style="margin-left: 3rem;" :disabled="config.type !== 'string'" type="text" placeholder="%(headword)-%(pos)" :value="config.string_template" @change="setWithEvent(config, 'string_template', $event)"/>
         </div>

      </div>
      <hr>
   </template>

   <div>
      <i class="material-symbols-outlined right">add</i>Add autonumbering to another element
      <select class="browser-default" id="newElement">
         <option v-for="el in getUnusedElements()" :value="el">{{ el }}</option>
      </select>
      <button type="button" class="btn waves-effect waves-light" @click="addElement">Add</button>
   </div>

   <div v-if="state.info"
         class="section">
      <div class="message messageInfo">
         {{ state.info }}
      </div>
   </div>
</dict-config-autonumber>
</template>

<script>
import Materialize from '../libs/materialize/materialize.min.js'
import { activeDictionary, dictionaryWorkspace } from '../js/dictionary-workspace.ts'
import DictConfigButtons from './dict-config-buttons.vue'
import DictNav from './dict-nav.vue'
import LoadingOverlay from './loading-overlay.vue'
import { api } from '../js/api.ts'

export default {
   setup: () => ({ activeDictionary }),
   components: { DictConfigButtons, DictNav, LoadingOverlay },
   data() {
      return {
         state: {
            isLoading: true,
            isSaving: false,
            info: "",
            data: {
            }
         }
      }
   },

   async mounted() {
      const response = await dictionaryWorkspace.loadDictionaryConfig('autonumbering')
      if (response) {
         this.state.data = response.content
      }
      this.state.isLoading = false
      Materialize.updateTextFields()
   },

   methods: {
      setWithEvent(config, prop, event) {
         if (typeof (config[prop]) === 'number') {
            const prev = config[prop]
            try {
               config[prop] = parseInt(event.target.value, 10);
               if (isNaN(config[prop])) config[prop] = prev;
            } catch (e) {
               // ?
               config[prop] = prev;
            }
         } else {
            config[prop] = event.target.value;
         }

      },

      set(config, prop, value) {
         config[prop] = value;

      },

      changeElement(config, event) {
         const oldElement = config.element;
         const newElement = event.target.value;
         if (!oldElement || !newElement || oldElement === newElement) return;

         this.state.data[newElement] = config;
         config.element = newElement;
         config.target = '';
         delete this.state.data[oldElement];

      },

      deleteElement(element) {
         if (!element) return;
         delete this.state.data[element];

      },

      addElement() {
         const element = document.getElementById('newElement').value
         if (!element) return;
         this.state.data[element] = this.getInitialConfig(element);

      },

      getInitialConfig(element) {
         return {
            overwrite_existing: false,
            auto_apply: false,
            number_next: 1,
            number_globally: true,
            string_template: '%(headword)-%(pos)',
            element,
            attribute: 'xml:id',
            type: 'number',
            target: ''
         }
      },

      getUnusedElements() {
         const xema = this.activeDictionary && this.activeDictionary.config && this.activeDictionary.config.xema;
         if (xema && xema.elements) {
            return Object.keys(xema.elements).map(key => xema.elements[key].elementName || key).filter(el => !this.state.data[el]);
         }

         return [];
      },

      getAttributesForElement(element) {
         const xema = this.activeDictionary && this.activeDictionary.config && this.activeDictionary.config.xema;
         return xema ? Object.keys(xema.elements[element]?.attributes || {}) : [];
      },

      getChildElementsForElement(element) {
         const xema = this.activeDictionary && this.activeDictionary.config && this.activeDictionary.config.xema;
         return xema ? (xema.elements[element]?.children || []).map(c => xema.elements[c.name]?.elementName || c.name) : [];
      },

      async addNumbers() {
         if (!confirm('Save config and start autonumbering?')) return
         const dictId = this.activeDictionary.dictId
         if (!await this.saveData() || this.activeDictionary.dictId !== dictId) return

         this.state.isSaving = true
         this.state.info = 'Working on it...'
         try {
            const response = await api.post(`${encodeURIComponent(dictId)}/autonumber.json`)
            this.state.info = response.success
               ? `Auto-numbering finished, ${response.processed} entries updated.`
               : 'Autonumbering failed.'
         } catch {
            this.state.info = 'Autonumbering failed.'
         } finally {
            this.state.isSaving = false
         }
      },

      async findNext(config) {
         if (!config?.element) return
         this.state.isSaving = true
         try {
            const { next } = await api.post(`${encodeURIComponent(this.activeDictionary.dictId)}/next_autonumber.json`, {
               element: config.element,
               target: config.target
            })
            config.number_next = next
         } catch {
            Materialize.toast({ html: 'Could not find the next number.' })
         } finally {
            this.state.isSaving = false
         }
      },

      async saveData() {
         this.state.isSaving = true
         const response = await dictionaryWorkspace.updateDictionaryConfig('autonumbering', this.state.data)
         this.state.isSaving = false
         return response?.success
      }
   }
}
</script>
