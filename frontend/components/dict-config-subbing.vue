<template>
<div class="dict-config-subbing">
   <LoadingOverlay v-if="loading || saving"/>
   <DictNav :links="[['config', 'Configure'], ['config-subbing', 'Subentries']]"/>
   <h1>Subentries</h1>
   <template v-if="ready">
      <DictConfigButtons :dict-id="dictId" :save-data="() => save(draft)" :disabled="saving"/>

      <div v-for="element in activeSubentries" :key="element.id" class="element-info" :class="{ 'text-red': !element.valid }">
         <div class="header">
            <h5>{{ element.name }} {{ element.valid ? '' : '(unknown element)' }}</h5>
            <button type="button" class="btn btn-small red lighten-1" :aria-label="`Remove ${element.name} from subentries`"
               style="margin-right: 15px;" @click="delete draft[element.id]"><i class="material-symbols-outlined">delete</i></button>
         </div>

         <span class="helper-text">Optional attributes this element must have to become a subentry</span>

         <div v-for="attribute in element.attributes" :key="attribute.name" class="att">
            <label :for="`subbing-${element.id}-${attribute.name}`" class="name">@{{ attribute.name }}</label>
            <FormSelect v-if="attribute.options.length" v-model="draft[element.id].attributes[attribute.name]" class="value"
               :id="`subbing-${element.id}-${attribute.name}`" :options="attribute.options" :aria-label="attribute.name"/>
            <input v-else v-model="draft[element.id].attributes[attribute.name]" :id="`subbing-${element.id}-${attribute.name}`"
               type="text" class="value" placeholder="Value">
            <button type="button" class="btn btn-small red lighten-1" :aria-label="`Remove required attribute ${attribute.name}`"
               @click="delete draft[element.id].attributes[attribute.name]"><i class="material-symbols-outlined">delete</i></button>
         </div>

         <div v-if="element.availableAttributes.length" class="att-new">
            <FormSelect v-model="newAttribute[element.id]" class="name" aria-label="Required subentry attribute"
               placeholder="Choose an attribute" :options="element.availableAttributes"/>
            <button class="btn btn-small" type="button" :disabled="!newAttribute[element.id]"
               @click="addAttribute(element.id)" aria-label="Add required subentry attribute"><i class="material-symbols-outlined">add</i></button>
         </div>

         <div v-if="element.headwords.length > 1" class="att-new">
            <label :for="`headword-${element.id}`" class="name">Headword element</label>
            <FormSelect :id="`headword-${element.id}`" class="value" aria-label="Headword element"
               v-model="draft[element.id].titling.headword" :options="element.headwords"/>
            <span class="helper-text">Select which descendant element of <b>{{ element.name }}</b> to use as the headword.</span>
         </div>
      </div>

      <div v-if="availableSubentries.length" class="row" style="margin-top: 15px;">
         <div class="input-field col s6">
            <FormSelect id="new-element" v-model="newElement" :options="availableSubentries"
               aria-label="Subentry element" placeholder="Choose an element"/>
            <span class="helper-text">Elements listed here function as subentries which can be shared by multiple entries.</span>
         </div>
         <div class="input-field col s1">
            <button type="button" class="btn btn-small" :disabled="!newElement" @click="addSubentry" aria-label="Add subentry element">
               <i class="material-symbols-outlined">add</i>
            </button>
         </div>
      </div>
   </template>
   <p v-else-if="!loading">Settings could not be loaded. <button class="btn-flat" type="button" @click="load">Retry</button></p>
</div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { activeDictionary } from '../js/dictionary-workspace.ts'
import { useDictionarySetting } from '../js/use-dictionary-setting.ts'
import DictConfigButtons from './dict-config-buttons.vue'
import DictNav from './dict-nav.vue'
import FormSelect from './FormSelect.vue'
import LoadingOverlay from './loading-overlay.vue'

type SubentryDraft = { attributes: Record<string, string>; titling: { headword: string } }
const props = defineProps<{ dictId: string }>()
const draft = ref<Record<string, SubentryDraft>>({})
const newElement = ref('')
const newAttribute = ref<Record<string, string>>(Object.create(null))
const xemaElements = computed(() => activeDictionary.config?.xema.elements ?? {})
const { loading, ready, saving, load, save } = useDictionarySetting(() => props.dictId, 'subbing', content => {
   newElement.value = ''
   newAttribute.value = Object.create(null)
   draft.value = Object.fromEntries(Object.entries(content).map(([id, entry]) => [id, {
      attributes: entry?.attributes ?? {},
      titling: { headword: entry?.titling?.headword ?? '' }
   }]))
})

const availableSubentries = computed(() => Object.entries(xemaElements.value)
   .filter(([id]) => !Object.hasOwn(draft.value, id))
   .map(([value, element]) => ({ value, label: element.elementName || value })))

const activeSubentries = computed(() => Object.entries(draft.value).map(([id, entry]) => {
   const schema = xemaElements.value[id]
   const attributes = schema?.attributes ?? {}
   return {
      id,
      valid: Boolean(schema),
      name: schema?.elementName || id,
      attributes: Object.entries(entry.attributes).map(([name, current]) => {
         const values = attributes[name]?.values ?? []
         const options = values.length
            ? [{ value: '', label: '[any value]' }, ...values.filter(option => option.value !== '')
               .map(({ value }) => ({ value, label: value }))]
            : []
         if (options.length && !options.some(option => option.value === current)) {
            options.push({ value: current, label: current })
         }
         return { name, options }
      }),
      availableAttributes: Object.keys(attributes).filter(name => !Object.hasOwn(entry.attributes, name))
         .map(value => ({ value, label: value })),
      headwords: headwordOptions(id, entry.titling.headword)
   }
}))

function headwordOptions(id: string, current: string) {
   const elements = xemaElements.value
   const seen = new Set([id])
   const options = [{ value: '', label: '(not set)' }]
   const visit = (name: string) => {
      const element = elements[name]
      if (!element || seen.has(name)) return
      seen.add(name)
      options.push({ value: name, label: element.elementName || name })
      element.children?.forEach(child => visit(child.name))
   }
   elements[id]?.children?.forEach(child => visit(child.name))
   if (current && !options.some(option => option.value === current)) options.push({ value: current, label: current })
   return options
}

function addSubentry() {
   const id = newElement.value
   if (id && Object.hasOwn(xemaElements.value, id) && !Object.hasOwn(draft.value, id)) {
      draft.value = { ...draft.value, [id]: { attributes: {}, titling: { headword: '' } } }
      newElement.value = ''
   }
}

function addAttribute(id: string) {
   const name = newAttribute.value[id]
   if (!name || Object.hasOwn(draft.value[id].attributes, name)) return
   draft.value[id].attributes = { ...draft.value[id].attributes, [name]: '' }
   newAttribute.value[id] = ''
}
</script>

<style>
.dict-config-subbing .element-info {
   display: flex;
   flex-direction: column;

   border: 1px solid #CCC;
   margin: 15px 0;
   border-radius: 3px;
   padding: 15px 30px;
}

.dict-config-subbing .element-info > .header {
   display: flex;
   flex-direction: row;
   flex-wrap: nowrap;
   align-items: baseline;
   justify-content: space-between;
   border-bottom: 1px solid #9e9e9e;
   margin-bottom: 25px;
}
.dict-config-subbing .element-info > .helper-text {
   margin-left: 25px;
}

.dict-config-subbing .element-info > .att,
.dict-config-subbing .element-info > .att-new {
   margin-left: 25px;
   padding-top: 25px;
   display: flex;
   flex-direction: row;
   align-items: baseline;
   flex-wrap: nowrap;
   width: 66.66%;
}

.dict-config-subbing .att > * {
   margin-right: 15px!important;
   flex: none;
}
.dict-config-subbing .att > .name {
   min-width: 16.667%
}
.dict-config-subbing .att > .value {
   flex: auto;
}

.dict-config-subbing .att + .att-new {
   border-top: 1px solid #9e9e9e;
}
.dict-config-subbing .element-info > .att-new {
   flex-wrap: wrap;
   justify-content: stretch;
}
.dict-config-subbing .att-new > * {
   margin-right: 15px!important;
   flex: none;
}
.dict-config-subbing .att-new > .name,
.dict-config-subbing .att-new > .value {
   flex: auto;
}
</style>
