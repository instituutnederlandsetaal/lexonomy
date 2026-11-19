<template>
<div class="dict-config-autonumber">
   <LoadingOverlay v-if="loading || saving || busy"/>
   <DictNav :links="[['config', 'Configure'], ['config-autonumber', 'Auto-numbering']]"/>
   <h1>Auto-numbering of elements</h1>
   <div v-if="ready" :inert="saving || busy">
      <DictConfigButtons :dict-id="dictId" :save-data="saveData" :disabled="saving || busy">
         <button type="button" class="btn waves-effect waves-light" @click="addNumbers" :disabled="saving || busy || !Object.keys(draft).length">
            <i class="material-symbols-outlined right">add</i>Save &amp; autonumber
         </button>
      </DictConfigButtons>
      <div class="row">
         <p>If you need to number some of entry elements automatically, Lexonomy can do that for you. First, go to Entry structure and add element/attribute where you want to store the number. Eg. in element <code>sense</code> add attribute <code>number</code>. When you're ready, select element to number (eg. <code>sense</code>) and element/attribute to store the number (eg. <code>@number</code>). Lexonomy will fill the numbers where missing.</p>
      </div>
      <hr>
      <template v-for="config in Object.values(draft)" :key="config.element">
         <div class="row">
            <div class="input-field col s4">
               <FormSelect :model-value="config.element" :options="[option(config.element), ...availableElements]"
                  aria-label="Element to number" @update:model-value="changeElement(config, $event)"/>
            </div>
            <!-- child/attribute selection -->
            <div class="input-field col s4">
               <FormSelect v-model="config.target" :options="targetOptions(config)" aria-label="Add numbers to"/>
            </div>
            <div class="input-field col s4">
               <button type="button" class="btn waves-effect waves-light" @click="deleteElement(config.element)" style="height:3rem;">Remove</button>
            </div>

            <div class="col s12">
               <label>
                  <input :name="(config.element) + ('_autoApply')" type="radio" class="with-gap" value="false" :checked="config.auto_apply" @change="config.auto_apply = true"/>
                  <span>Apply numbers automatically</span>
               </label>
               <br>
               <label>
                  <input :name="(config.element) + ('_autoApply')" type="radio" class="with-gap" value="true" :checked="!config.auto_apply" @change="config.auto_apply = false"/>
                  <span>Only run numbering manually</span>
               </label>
            </div>

            <h3 class="col s12" style="margin-top: 2rem;">What to do with existing values</h3>
            <div class="col s12" style="padding-left: 2.75rem;">
               <label>
                  <input :name="(config.element) + ('_existingValues')" type="radio" class="with-gap" value="false" :checked="!config.overwrite_existing" @change="config.overwrite_existing = false"/>
                  <span><b>Keep</b> existing values</span>
               </label>
               <br>
               <label>
                  <input :name="(config.element) + ('_existingValues')" type="radio" class="with-gap" value="true" :checked="config.overwrite_existing" @change="config.overwrite_existing = true"/>
                  <span><b>Overwrite</b> existing values</span>
               </label>
            </div>

            <h3 class="col s12" style="margin-top: 2rem;">New values</h3>
            <div class="col s12" style="padding-left: 2.75rem;">
               <label>
                  <input :name="(config.element) + ('_newValues')" type="radio" class="with-gap" value="number" :checked="config.type == 'number'" @change="config.type = 'number'" />
                  <span>Use numbers</span>
               </label>
               <br>

               <label style="margin-left: 3rem; margin-top: 0.75rem;">
                  <input :name="(config.element) + ('_useNumbers')" type="radio" class="with-gap" :disabled="config.type !== 'number'" :checked="!config.number_globally" @change="config.number_globally = false"/>
                  <span>Start at 0 in every entry</span>
               </label>
               <div style="margin-left: 3rem; display: flex; flex-wrap: wrap; align-items: baseline;">
                  <label style="white-space: nowrap;">
                     <input style="margin-left: 0.75rem;" :name="(config.element) + ('_useNumbers')" type="radio" class="with-gap" :disabled="config.type !== 'number'" :checked="config.number_globally" @change="config.number_globally = true"/>
                     <span>Keep counting up, starting from</span>
                  </label>
                  <input type="number" aria-label="First number" :disabled="config.type !== 'number' || !config.number_globally"
                     style="margin-left: 0.75rem; flex-basis: 5ch; flex-grow: 1;" :value="config.number_next" @change="setNextNumber(config, $event)"/>
                  <button type="button" class="btn waves-effect waves-light" style="height: 3rem; flex-shrink: 0; margin-left: 0.75rem;" @click="findNext(config)" :disabled="config.type !== 'number' || !config.number_globally || busy || saving">Find next number</button>
               </div>

               <label>
                  <input :name="(config.element) + ('_newValues')" type="radio" class="with-gap" :checked="config.type == 'string'" @change="config.type = 'string'"/>
                  <span>Use text</span>
               </label>

               <input style="margin-left: 3rem;" :disabled="config.type !== 'string'" type="text" placeholder="%(headword)-%(pos)" v-model="config.string_template" aria-label="Text to generate"/>
            </div>

         </div>
         <hr>
      </template>

      <div v-if="availableElements.length">
         <FormSelect id="newElement" v-model="newElement" :options="availableElements"
            aria-label="Add auto-numbering to another element" placeholder="Choose an element"/>
         <button type="button" class="btn waves-effect waves-light" @click="addElement" :disabled="!newElement || busy || saving">Add</button>
      </div>

      <div v-if="info"
            class="section">
         <div class="message messageInfo">
            {{ info }}
         </div>
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
