<template>
<div class="dict-config-subbing">
   <LoadingOverlay v-if="loading || saving"/>
   <DictNav :links="[['config', 'Configure'], ['config-subbing', 'Subentries']]"/>
   <h1>Subentries</h1>
   <DictConfigButtons :dict-id="dictId" :save-data="() => save(draft)" :disabled="saving || !ready"/>
   <div v-if="ready" class="config-form">
      <p>Elements configured as subentries can be shared by multiple entries.</p>
      <section v-for="element in activeSubentries" :key="element.id">
         <div class="config-section-heading">
            <h2>{{ element.name }}{{ element.valid ? '' : ' (unknown element)' }}</h2>
            <button type="button" class="btn btn-flat" :aria-label="`Remove ${element.name} from subentries`"
               @click="delete draft[element.id]"><i class="material-symbols-outlined">delete</i></button>
         </div>

         <div v-if="element.attributes.length || element.availableAttributes.length" class="config-field">
            <h3>Required attributes</h3>
            <p class="helper-text">Add attributes that this element must match to become a subentry.</p>
            <div v-for="attribute in element.attributes" :key="attribute.name" class="config-control-row">
               <label :for="`subbing-${element.id}-${attribute.name}`" class="subentry-attribute">@{{ attribute.name }}</label>
               <FormSelect v-if="attribute.options.length" v-model="draft[element.id].attributes[attribute.name]"
                  :id="`subbing-${element.id}-${attribute.name}`" :options="attribute.options"/>
               <input v-else v-model="draft[element.id].attributes[attribute.name]" :id="`subbing-${element.id}-${attribute.name}`"
                  type="text" placeholder="Any value">
               <button type="button" class="btn btn-flat" :aria-label="`Remove required attribute ${attribute.name}`"
                  @click="delete draft[element.id].attributes[attribute.name]"><i class="material-symbols-outlined">delete</i></button>
            </div>
            <div v-if="element.availableAttributes.length" class="config-control-row">
               <FormSelect v-model="newAttribute[element.id]" aria-label="Required subentry attribute"
                  placeholder="Choose an attribute" :options="element.availableAttributes"/>
               <button class="btn" type="button" :disabled="!newAttribute[element.id]" @click="addAttribute(element.id)">
                  Add attribute
               </button>
            </div>
         </div>

         <div v-if="element.headwords.length > 1" class="config-field">
            <label :for="`headword-${element.id}`">Headword element</label>
            <FormSelect :id="`headword-${element.id}`"
               v-model="draft[element.id].titling.headword" :options="element.headwords"/>
            <span class="helper-text">Choose a descendant of <b>{{ element.name }}</b> to use as its headword.</span>
         </div>
      </section>

      <div v-if="availableSubentries.length" class="config-field">
         <label for="new-element">Subentry element</label>
         <div class="config-control-row">
            <FormSelect id="new-element" v-model="newElement" :options="availableSubentries" placeholder="Choose an element"/>
            <button type="button" class="btn" :disabled="!newElement" @click="addSubentry">Add subentry</button>
         </div>
      </div>
   </div>
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
import '../css/dict-config-form.css'
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

<style scoped>
h3 {
   font-size: 1rem;
   margin: 0;
}
.subentry-attribute {
   flex: 0 1 30%;
   font-family: monospace;
   text-transform: none;
   overflow-wrap: anywhere;
}
.config-field + .config-field {
   margin-top: 1rem;
}
</style>
