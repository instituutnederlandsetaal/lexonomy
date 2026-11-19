<template>
   <PopupDisplay class="linking-element-selector" :z-index="zIndex" :model-value="modelValue"
                 :title="`Link selected ${name}`" :save-disabled="saving || !selection" @cancel="emit('update:modelValue', false)" @save="linkToElement">
      <h2>Link selected {{ name }} to:</h2>
      <div class="popup-header">
         <label for="link-dictionary" class="text--md">Dictionary:</label>
         <FormSelect id="link-dictionary" v-model="dictionary" :options="dictionaries" aria-label="Dictionary"/>
         <input v-model="searchTerm" placeholder="Filter" type="search" aria-label="Filter link targets">
      </div>
      <p v-if="loading" role="status">Loading targets…</p>
      <p v-else-if="failure" role="alert">Could not load link targets.</p>
      <p v-else-if="!displayedLinks.length">No matching link targets.</p>
      <div v-else class="links">
         <label v-for="(target, index) in displayedLinks" :key="index" class="link" :class="{ selected: selection === target }">
            <input type="radio" v-model="selection" :value="target" name="link-target" class="browser-default"/>
            <span>{{ target.element }}: {{ target.link }} {{ target.preview ? `(${target.preview})` : '' }}</span>
         </label>
      </div>
   </PopupDisplay>
</template>

<script setup lang="ts">
import { editorContextKey, notifyLinksChangedKey } from '../editor-context.ts'
import { computed, inject, ref, watch } from 'vue'
import Materialize from '../../../libs/materialize/materialize.min.js'
import { entryEditorApi, type LinkTarget } from '../../../js/entry-editor-api.ts'
import { xmlElementName } from '../../../js/xema.ts'
import FormSelect from '../../FormSelect.vue'
import PopupDisplay from './PopupDisplay.vue'

const props = withDefaults(defineProps<{
   modelValue: boolean
   zIndex?: string
   elementName: string
   sourceId?: string | number
}>(), { zIndex: '100' })
const emit = defineEmits<{ 'update:modelValue': [open: boolean] }>()
const editor = inject(editorContextKey)!
const notifyLinksChanged = inject(notifyLinksChangedKey)!
const name = computed(() => xmlElementName(editor.config.xema, props.elementName))
const dictionaries = computed(() => editor.userDicts.filter(dict => dict.hasLinks)
   .map(dict => ({ value: dict.id, label: dict.title })))
const dictionary = ref(dictionaries.value[0]?.value)
const searchTerm = ref('')
const availableLinks = ref<LinkTarget[]>([])
const selection = ref<LinkTarget>()
const loading = ref(false)
const failure = ref(false)
const saving = ref(false)
const displayedLinks = computed(() => {
   const term = searchTerm.value.toLowerCase()
   return availableLinks.value.filter(link =>
      [link.element, link.link, link.preview].some(value => value?.toLowerCase().includes(term))
   ).slice(0, 40)
})

watch(dictionaries, options => {
   if (!options.some(option => option.value === dictionary.value)) dictionary.value = options[0]?.value
})
watch(searchTerm, () => { selection.value = undefined })
watch([dictionary, () => props.modelValue], async ([target, open], _, onCleanup) => {
   availableLinks.value = []
   selection.value = undefined
   failure.value = false
   loading.value = Boolean(target && open)
   if (!target || !open) return
   let current = true
   onCleanup(() => { current = false })
   try {
      const { links } = await entryEditorApi.linkTargets(target)
      if (current) availableLinks.value = links
   } catch {
      if (current) failure.value = true
   } finally {
      if (current) loading.value = false
   }
}, { immediate: true })

async function linkToElement() {
   const target = selection.value
   if (!target || !dictionary.value || !props.sourceId || saving.value) return
   saving.value = true
   try {
      const { success } = await entryEditorApi.addLink(editor.dictId, {
         source_el: name.value,
         source_id: String(props.sourceId),
         target_dict: dictionary.value,
         target_el: target.element,
         target_id: target.link
      })
      if (!success) throw new Error('Link rejected')
      notifyLinksChanged()
      Materialize.toast({ html: 'Linked!' })
      emit('update:modelValue', false)
   } catch {
      Materialize.toast({ html: 'Could not add the link.' })
   } finally {
      saving.value = false
   }
}
</script>

<style scoped>
.popup-header { display: flex; align-items: center; gap: 12px; }
.popup-header .form-select-trigger { max-width: 260px; }
.popup-header input { max-width: 400px; margin: 0; }
.links { margin: 24px 0; max-height: calc(100% - 165px); overflow-y: auto; }
.link {
   display: flex;
   align-items: center;
   gap: 8px;
   color: inherit;
   text-align: left;
   padding: 4px;
   cursor: pointer;
}
.link.selected { background: #dedede; }
.link + .link { border-top: 1px solid #637383; }
.link input[type="radio"] { appearance: auto; opacity: 1; position: static; pointer-events: auto; }
</style>
