<template>
<div class="dict-config-autonumber">
   <LoadingOverlay v-if="loading || saving || busy"/>
   <DictNav :links="[['config', 'Configure'], ['config-autonumber', 'Auto-numbering']]"/>
   <h1>Auto-numbering</h1>
   <div :inert="saving || busy">
      <DictConfigButtons :dict-id="dictId" :save-data="saveData" :disabled="!ready || saving || busy">
         <button type="button" class="btn waves-effect waves-light" @click="addNumbers"
            :disabled="!ready || saving || busy || !Object.keys(draft).length">
            Save &amp; autonumber
            <i class="material-symbols-outlined right">add</i>
         </button>
      </DictConfigButtons>
      <div v-if="ready" class="config-form">
         <p>Choose an element to number and where to store the value. For example, add a <code>number</code> attribute to <code>sense</code> in Entry structure, then select <code>sense</code> and <code>@number</code> below.</p>

         <section v-for="config in Object.values(draft)" :key="config.element">
            <div class="config-section-heading">
               <h2>{{ config.element }}</h2>
               <button type="button" class="btn btn-flat" :aria-label="'Remove numbering for ' + config.element"
                  @click="deleteElement(config.element)"><i class="material-symbols-outlined">delete</i></button>
            </div>

            <div class="numbering-settings">
               <div class="config-fields">
                  <div class="config-field">
                     <label :for="'number-element-' + config.element">Element to number</label>
                     <FormSelect :id="'number-element-' + config.element" :model-value="config.element"
                        :options="[option(config.element), ...availableElements]" @update:model-value="changeElement(config, $event)"/>
                  </div>
                  <div class="config-field">
                     <label :for="'number-target-' + config.element">Store values in</label>
                     <FormSelect :id="'number-target-' + config.element" v-model="config.target" :options="targetOptions(config)"/>
                  </div>
               </div>

               <div class="config-fields">
                  <fieldset class="numbering-options">
                     <legend>When to apply</legend>
                     <label>
                        <input :name="'number-apply-' + config.element" type="radio" class="with-gap"
                           :checked="config.auto_apply" @change="config.auto_apply = true"/>
                        <span>Automatically when saving an entry</span>
                     </label>
                     <label>
                        <input :name="'number-apply-' + config.element" type="radio" class="with-gap"
                           :checked="!config.auto_apply" @change="config.auto_apply = false"/>
                        <span>Only when run manually</span>
                     </label>
                  </fieldset>

                  <fieldset class="numbering-options">
                     <legend>Existing values</legend>
                     <label>
                        <input :name="'number-overwrite-' + config.element" type="radio" class="with-gap"
                           :checked="!config.overwrite_existing" @change="config.overwrite_existing = false"/>
                        <span>Keep existing values</span>
                     </label>
                     <label>
                        <input :name="'number-overwrite-' + config.element" type="radio" class="with-gap"
                           :checked="config.overwrite_existing" @change="config.overwrite_existing = true"/>
                        <span>Overwrite existing values</span>
                     </label>
                  </fieldset>
               </div>

               <fieldset class="numbering-options inline-options">
                  <legend>New values</legend>
                  <label>
                     <input :name="'number-type-' + config.element" type="radio" class="with-gap" value="number" v-model="config.type"/>
                     <span>Use numbers</span>
                  </label>
                  <label>
                     <input :name="'number-type-' + config.element" type="radio" class="with-gap" value="string" v-model="config.type"/>
                     <span>Use text</span>
                  </label>
               </fieldset>

               <fieldset v-if="config.type === 'number'" class="numbering-options inline-options">
                  <legend>Counting</legend>
                  <label>
                     <input :name="'number-scope-' + config.element" type="radio" class="with-gap"
                        :checked="!config.number_globally" @change="config.number_globally = false"/>
                     <span>Start at 0 in each entry</span>
                  </label>
                  <label>
                     <input :name="'number-scope-' + config.element" type="radio" class="with-gap"
                        :checked="config.number_globally" @change="config.number_globally = true"/>
                     <span>Count across entries</span>
                  </label>
               </fieldset>

               <div v-if="config.type === 'number' && config.number_globally" class="config-field next-number">
                  <label :for="'number-next-' + config.element">Next number</label>
                  <div class="config-control-row">
                     <input :id="'number-next-' + config.element" type="number" :value="config.number_next"
                        @change="setNextNumber(config, $event)"/>
                     <button type="button" class="btn waves-effect waves-light" @click="findNext(config)"
                        :disabled="busy || saving">Find next number</button>
                  </div>
               </div>
               <div v-if="config.type === 'string'" class="config-field">
                  <label :for="'number-template-' + config.element">Text template</label>
                  <input :id="'number-template-' + config.element" type="text" v-model="config.string_template" placeholder="%(headword)-%(pos)"/>
               </div>
            </div>
         </section>

         <div v-if="availableElements.length" class="config-field">
            <label for="newElement">New numbering rule</label>
            <div class="config-control-row">
               <FormSelect id="newElement" v-model="newElement" :options="availableElements" placeholder="Choose an element"/>
               <button type="button" class="btn waves-effect waves-light" @click="addElement" :disabled="!newElement || busy || saving">Add rule</button>
            </div>
         </div>

         <div v-if="info" class="message messageInfo" role="status">{{ info }}</div>
      </div>
   </div>
   <p v-if="!loading && !ready">Settings could not be loaded. <button class="btn-flat" type="button" @click="load">Retry</button></p>
</div>
</template>

<script setup lang="ts">
import { useDictionarySetting } from '../js/use-dictionary-setting.ts'
import DictConfigButtons from './dict-config-buttons.vue'
import DictNav from './dict-nav.vue'
import LoadingOverlay from './loading-overlay.vue'
import { computed, ref, watch } from 'vue'
import { activeDictionary } from '../js/dictionary-workspace.ts'
import { applyAutonumbering, findNextNumber, type DictionarySettings } from '../js/dictionary-config-api.ts'
import FormSelect from './FormSelect.vue'
import '../css/dict-config-form.css'

type Numbering = DictionarySettings['autonumbering'][string]
const props = defineProps<{ dictId: string }>()
const draft = ref<Record<string, Numbering>>({})
const newElement = ref('')
const info = ref('')
const busy = ref(false)
const { scope, loading, ready, saving, load, save } = useDictionarySetting(() => props.dictId, 'autonumbering', content => {
   draft.value = Object.fromEntries(Object.entries(content).map(([id, settings]) => [id, {
      ...settings, target: settings.target ?? '', type: settings.type ?? 'number'
   }]))
})
watch(scope, () => {
   newElement.value = ''
   info.value = ''
   busy.value = false
})

const elements = computed(() => activeDictionary.config?.xema.elements ?? {})
const tagName = (id: string) => elements.value[id]?.elementName || id
const option = (value: string) => ({ value, label: value })
const availableElements = computed(() => [...new Set(Object.keys(elements.value).map(tagName))]
   .filter(id => !Object.hasOwn(draft.value, id)).map(option))

function targetOptions(config: Numbering) {
   const fields = Object.entries(elements.value).filter(([id]) => tagName(id) === config.element)
      .flatMap(([, element]) => [
         ...Object.keys(element.attributes ?? {}).map(name => '@' + name),
         ...(element.children ?? []).map(child => tagName(child.name))
      ])
   if (config.target) fields.push(config.target)
   return [{ value: '', label: config.element + ' itself' }, ...[...new Set(fields)].map(option)]
}

function changeElement(config: Numbering, id: string) {
   if (!availableElements.value.some(element => element.value === id)) return
   delete draft.value[config.element]
   draft.value = { ...draft.value, [id]: { ...config, element: id, target: '' } }
}

function deleteElement(id: string) {
   delete draft.value[id]
}

function addElement() {
   const id = newElement.value
   if (!availableElements.value.some(element => element.value === id)) return
   draft.value = { ...draft.value, [id]: {
      element: id, target: '', type: 'number', number_next: 1,
      overwrite_existing: false, auto_apply: false, number_globally: true,
      string_template: '%(headword)-%(pos)'
   } }
   newElement.value = ''
}

function setNextNumber(config: Numbering, event: Event) {
   if (!(event.target instanceof HTMLInputElement)) return
   const number = event.target.valueAsNumber
   if (Number.isSafeInteger(number)) config.number_next = number
   else event.target.value = String(config.number_next ?? '')
}

async function findNext(config: Numbering) {
   if (busy.value || saving.value) return
   const current = scope.value
   const { element, target } = config
   info.value = ''
   busy.value = true
   try {
      const next = await findNextNumber(current.dictId, element, target)
      if (!current.active || draft.value[element] !== config || config.target !== target) return
      if (typeof next === 'number') config.number_next = next
      else info.value = 'No existing numbers were found for that target.'
   } catch {
      if (current.active) info.value = 'Could not find the next number.'
   } finally {
      if (current.active) busy.value = false
   }
}

function saveData() {
   return save(draft.value)
}

async function addNumbers() {
   if (busy.value || saving.value || !confirm('Save settings and start auto-numbering?')) return
   const current = scope.value
   busy.value = true
   info.value = ''
   try {
      if (!await saveData() || !current.active) return
      info.value = 'Working on it…'
      const result = await applyAutonumbering(current.dictId)
      if (!current.active) return
      if (result.success) {
         await load()
         if (current.active) info.value = `Auto-numbering finished, ${result.processed} entries updated.`
      } else {
         info.value = 'Auto-numbering failed.'
      }
   } catch {
      if (current.active) info.value = 'Auto-numbering failed.'
   } finally {
      if (current.active) busy.value = false
   }
}
</script>

<style scoped>
.dict-config-buttons {
   flex-wrap: wrap;
}
.numbering-settings {
   display: grid;
   gap: .85rem;
}
.numbering-options {
   min-width: 0;
   border: 0;
   margin: 0;
   padding: 0;
}
.numbering-options legend {
   color: #004494;
   font-size: .9rem;
   text-transform: uppercase;
   padding: 0;
}
.numbering-options label {
   display: block;
}
.numbering-options label > span {
   height: auto;
   min-height: 25px;
   text-transform: none;
}
.inline-options > label {
   display: inline-block;
   margin-right: 1rem;
}
.next-number .config-control-row {
   flex-wrap: wrap;
}
.next-number input {
   flex: 0 1 7rem;
}
</style>
