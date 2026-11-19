<template>
<dict-config-subbing>
   <LoadingOverlay v-if="state.isLoading || state.isSaving"/>
   <DictNav :links="[['config', 'Configure'], ['config-subbing', 'Subentries']]"/>
   <h1>Subentries</h1>
   <template v-if="!state.isLoading">
      <DictConfigButtons :save-data="saveData" :show-save="true"></DictConfigButtons>

      <div v-for="element in activeSubentries" :key="element.name" :data-element="element.name" :class="element.valid ? 'element-info' : 'element-info text-red'" >
         <div class="header">
            <h5>{{ element.name }} {{ element.valid ? ''  : '(unknown element)!' }}</h5>
            <button type="button" class="btn btn-small red lighten-1" :title="('Remove ') + (element.name) + (' from subentries')" style="margin-right: 15px;" @click="doDeleteEl"><i class="material-symbols-outlined">delete</i></button>
         </div>

         <span class="helper-text">(Optional) - Attributes this element should have to be a subentry: </span>

         <div v-for="att in element.activeAttributes" :key="att.name" :data-attribute="att.name" class="att">
            <label :for="`${att.name}-value`" class="name blue-text">@{{ att.name }}</label>
            <select v-if="att.values" class="value" @change="changeAttribute" :value="att.value" :name="`${att.name}-value`">
               <option value="" :selected="!att.value">[any value]</option>
               <option v-for="v in att.values" :key="v.value" :value="v.value" :selected="v.value === att.value">{{ v.value }}</option>
            </select>
            <input v-if="!att.values" type="text" class="value" :value="att.value" @change="changeAttribute" placeholder="Value">
            <button type="button" class="btn btn-small red lighten-1" :title="('Remove ') + (att.name) + (' from required attributes')" @click="deleteAttribute"><i class="material-symbols-outlined">delete</i></button>
         </div>

         <div v-if="element.inactiveAttributes.length" class="att-new">
            <select class="name new-attribute" name="new-attribute">
               <option v-for="att in element.inactiveAttributes" :key="att.name" :value="att.name">{{ att.name }}</option>
            </select>
            <button class="btn btn-small" type="button" @click="addAttribute" title="Add required subentry attribute"><i class="material-symbols-outlined">add</i></button>
         </div>

         <!-- Headword element selection for subentry titling -->
         <div class="att-new" v-if="getSubentryDescendants(element.name).length">
            <label :for="`headword-${element.name}`" class="name">Headword element</label>
            <select class="value" :name="`headword-${element.name}`" @change="e => setSubentryHeadword(element.name, e.target.value)">
               <option value="" :selected="!getSubentryHeadword(element.name)">(not set)</option>
               <option v-for="desc in getSubentryDescendants(element.name)" :key="desc.id" :value="desc.id" :selected="getSubentryHeadword(element.name) === desc.id">{{ desc.displayName }}</option>
            </select>
            <span class="helper-text">Select which descendant element of <b>{{ element.name }}</b> should be used as the headword/title for subentries of this type.</span>
         </div>
      </div>

      <div class="row" v-if="inactiveSubentries.length" style="margin-top: 15px;">
         <div class="input-field col s6">
            <select id="new-element">
               <option v-for="elementName in inactiveSubentries" :key="elementName" :value="elementName">{{ elementName }}</option>
            </select>
            <label for="new-element">Subentry element</label>
            <span class="helper-text">Elements listed here function as subentries which can be shared by multiple entries.</span>
         </div>
         <div class="input-field col s1">
            <button class="btn btn-small" @click="doAddEl" title="Add subentry element"><i class="material-symbols-outlined">add</i></button>
         </div>
      </div>

   </template>

</dict-config-subbing>
</template>

<script>
import { activeDictionary, dictionaryWorkspace } from '../js/dictionary-workspace.ts'
import DictConfigButtons from './dict-config-buttons.vue'
import DictNav from './dict-nav.vue'
import LoadingOverlay from './loading-overlay.vue'
import { materializeSelects } from './form-select.js'
// @ts-check

export default {
   setup: () => ({ activeDictionary }),
   components: { DictConfigButtons, DictNav, LoadingOverlay },
   mixins: [materializeSelects],

   data() {
      return {
         state: {
            isLoading: true,
            isSaving: false,
         },
         configData: {}
      }
   },

   async mounted() {
      const response = await dictionaryWorkspace.loadDictionaryConfig('subbing')
      this.configData = response?.content || {}
      this.state.isLoading = false
   },

   computed: {
      xema() { return this.activeDictionary?.config?.xema; },

      elements() { return Object.keys(this.xema?.elements || {}); },

      activeSubentries() {
         if (!this.xema) return [];
         return Object
            .entries(this.configData)
            .map(([elementName, value]) => ({
               name: elementName,
               valid: !!this.xema.elements[elementName], // mark invalid subentry configurations (element is not in the entry schema - maybe it changed?)
               activeAttributes: Object
                  .entries(value.attributes || {})
                  .map(([attributeName, attributeValue]) => ({
                     name: attributeName,
                     value: attributeValue,
                     values: this.xema.elements[elementName]?.attributes?.[attributeName]?.values
                  })),
               inactiveAttributes: Object
                  .entries(this.xema.elements[elementName]?.attributes || {})
                  .filter(([name]) => !(name in (value.attributes || {})))
                  .map(([attributeName, {values}]) => ({
                     name: attributeName,
                     values
                  }))
               })
            )
      },

      inactiveSubentries() {
         return this.elements.filter(name => !this.configData[name])
      }
   },

   methods: {
      addAttribute(event) {
         const context = event.target.closest('[data-element]');
         const elementName = context.getAttribute('data-element');
         const attributeName = context.querySelector('.new-attribute').value
         if (!attributeName) return;
         this.configData[elementName].attributes = this.configData[elementName].attributes || {}; // init if the config is old format
         this.configData[elementName].attributes[attributeName] = ""

      },

      deleteAttribute(event) {
         const elementName = event.target.closest('[data-element]').getAttribute('data-element');
         const attributeName = event.target.closest('[data-attribute]').getAttribute('data-attribute');
         delete this.configData[elementName].attributes[attributeName];

      },

      changeAttribute(event) {
         const elementName = event.target.closest('[data-element]').getAttribute('data-element');
         const attributeName = event.target.closest('[data-attribute]').getAttribute('data-attribute');
         const newValue = event.target.value;
         this.configData[elementName].attributes[attributeName] = newValue;

      },

      doDeleteEl(event) {
         const elementName = event.target.closest('[data-element]').getAttribute('data-element');
         delete this.configData[elementName]

      },

      doAddEl() {
         const elementName = this.$el.querySelector('#new-element').value;
         if (!elementName) return;
         this.configData[elementName] = { attributes: {} }

      },

      async saveData() {
         this.state.isSaving = true
         await dictionaryWorkspace.updateDictionaryConfig("subbing", this.configData)
         this.state.isSaving = false
      },

      getSubentryDescendants(elementName) {
         // Returns array of {id, displayName} for all descendants (including children, grandchildren, etc) of this subentry element
         const xema = this.xema;
         if (!xema?.elements?.[elementName]) return [];
         const seen = new Set();
         const descendants = [];
         const visit = elId => {
            if (!xema.elements[elId] || seen.has(elId)) return;
            seen.add(elId);
            const elConfig = xema.elements[elId];
            descendants.push({ id: elId, displayName: elConfig.elementName || elId });
            elConfig.children?.forEach(child => visit(child.name));
         };
         xema.elements[elementName].children?.forEach(child => visit(child.name));
         return descendants;
      },

      getSubentryHeadword(elementName) {
         return this.configData[elementName]?.titling?.headword || '';
      },

      setSubentryHeadword(elementName, value) {
         if (!this.configData[elementName].titling) this.configData[elementName].titling = {};
         this.configData[elementName].titling.headword = value;

      }
   }
}
</script>

<style>
dict-config-subbing .element-info {
   display: flex;
   flex-direction: column;

   border: 1px solid #CCC;
   margin: 15px 0;
   border-radius: 3px;
   padding: 15px 30px;
}

dict-config-subbing .element-info > .header {
   display: flex;
   flex-direction: row;
   flex-wrap: nowrap;
   align-items: baseline;
   justify-content: space-between;
   border-bottom: 1px solid #9e9e9e;
   margin-bottom: 25px;
}
dict-config-subbing .element-info > .helper-text {
   margin-left: 25px;
}

dict-config-subbing .element-info > .att,
dict-config-subbing .element-info > .att-new {
   margin-left: 25px;
   padding-top: 25px;
   display: flex;
   flex-direction: row;
   align-items: baseline;
   flex-wrap: nowrap;
   width: 66.66%;
}

dict-config-subbing .att > * {
   margin-right: 15px!important;
   flex: none;
}
dict-config-subbing .att > .name {
   min-width: 16.667%
}
dict-config-subbing .att > .value,
dict-config-subbing .att > .select-wrapper {
   flex: auto;
}

dict-config-subbing .att + .att-new {
   border-top: 1px solid #9e9e9e;
}
dict-config-subbing .element-info > .att-new {
   flex-wrap: wrap;
   justify-content: stretch;
}
dict-config-subbing .att-new > * {
   margin-right: 15px!important;
   flex: none;
}
dict-config-subbing .att-new > .name,
dict-config-subbing .att-new > .select-wrapper {
   flex: auto;
}
</style>
