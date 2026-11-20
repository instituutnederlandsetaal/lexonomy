<template>
<div class="dict-edit">
   <LoadingOverlay v-if="myDictionaries.loading || activeDictionary.isDictionaryLoading"/>
   <DictNav :links="[['edit', 'Edit']]"/>
   <h1 class="header">
      {{ activeDictionary.title }}
      <span v-if="activeDictionary.entryCount"
            class="totalEntries">total {{ activeDictionary.entryCount }} entries</span>
   </h1>
   <template v-if="activeDictionary.dictId && activeDictionary.config && !myDictionaries.loading">
      <div v-if="activeDictionary.doctypes.length > 1"
            class="doctypes">
         <ul class="tabs">
            <li v-for="type in activeDictionary.doctypes" :key="type" :active="type === activeDictionary.doctype" class="tab col s2">
               <button type="button" :aria-pressed="type === activeDictionary.doctype" @click="changeDoctype(type)">
                  {{ type }}
               </button>
            </li>
         </ul>
      </div>
      <div id="dictEditContainer" >
         <div ref="entryColumn" class="dictLeftCol"
               :style="{ width: columnWidth ? columnWidth + 'px' : `max(${flags.length ? '25vw' : '20vw'}, 250px)` }">
            <DictEntryFilter :flags="flags"/>
            <template v-if="activeDictionary.entryList">
               <DictEntryPagination :entry-count="activeDictionary.entryCount" :page-size="entryPageSize"
                  :page="activeDictionary.currentPage" :loading="activeDictionary.isEntryListLoading"
                  @previous="dictionaryWorkspace.previousPage()" @next="dictionaryWorkspace.nextPage()"/>
               <ul ref="entryList" class="entry-list collection" aria-label="Entries" @keydown="onListKeyDown">
                  <DictEntryRow v-for="(entry, idx) in activeDictionary.entryList" :key="entry.id"
                     :entry="entry" :index="idx" :locate-entry="locateEntry"
                     :selected="entry.id === activeDictionary.entryId"
                     :can-change-flag="canEdit" :flags="flags"
                     @select="selectEntry" @update:flag="setFlag(entry.id, $event)"/>
                  <li v-if="!activeDictionary.entryList.length && !activeDictionary.isEntryListLoading"
                        style="padding-top: 10vh;">
                     <h2 class="grey-text center-align">No entries</h2>
                  </li>
               </ul>
            </template>
            <LoadingOverlay v-if="activeDictionary.isEntryListLoading"/>
         </div>
         <div class="resizeHandle" role="separator" aria-label="Resize entry list" aria-orientation="vertical"
              tabindex="0" :aria-valuenow="columnWidth" @pointerdown="startResize" @pointermove="resizeColumn"
              @lostpointercapture="endResize" @keydown.left.prevent.stop="resizeBy(-10)"
              @keydown.right.prevent.stop="resizeBy(10)"></div>
         <div class="dictRightCol">
            <DictEditEntry :key="activeDictionary.dictId" ref="entryEditor" :dictionary-config="activeDictionary.config"
               :dict-id="activeDictionary.dictId" :doctype="activeDictionary.doctype" :entry-id="activeDictionary.entryId"
               :mode="activeDictionary.mode" :can-edit="canEdit" :user-dicts="myDictionaries.items"/>
         </div>
      </div>
   </template>
</div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { stringifyQuery, useRouter, type LocationQuery, type RouteLocationRaw } from 'vue-router'
import { activeDictionary, dictionaryWorkspace, entryPageSize } from '../js/dictionary-workspace.ts'
import { myDictionaries } from '../js/my-dictionaries.ts'
import DictEditEntry from './dict-edit-entry.vue'
import DictEntryFilter from './dict-entry-filter.vue'
import DictEntryPagination from './dict-entry-pagination.vue'
import DictEntryRow from './dict-entry-row.vue'
import DictNav from './dict-nav.vue'
import LoadingOverlay from './loading-overlay.vue'

const router = useRouter()
const entryEditor = ref<InstanceType<typeof DictEditEntry> | null>(null)
const entryColumn = ref<HTMLElement | null>(null)
const entryList = ref<HTMLUListElement | null>(null)
const columnWidth = ref<number>()
const entrySteps: Partial<Record<string, number>> = {
   ArrowUp: -1, ArrowDown: 1, PageUp: -10, PageDown: 10, Home: -Infinity, End: Infinity
}
let selectFirst: { dictId: string; doctype: string } | undefined
let resizeStart: { x: number; width: number; userSelect: string } | undefined

const canEdit = computed(() => Boolean(activeDictionary.userAccess?.canEdit))
const flags = computed(() => activeDictionary.config?.flagging.flags ?? [])
const entryQuery = computed<LocationQuery>(previous => {
   const query = router.currentRoute.value.query
   return previous && stringifyQuery(previous) === stringifyQuery(query) ? previous : query
})
const locateEntry = computed(() => {
   const { dictId, doctype, mode } = activeDictionary
   const query = entryQuery.value
   return (entryId: number): RouteLocationRaw => ({ name: 'edit', params: { dictId, doctype, entryId, mode }, query })
})

watch([() => activeDictionary.dictId, () => activeDictionary.doctype], ([dictId, doctype], [previousDictId]) => {
   if (selectFirst && (selectFirst.dictId !== dictId || selectFirst.doctype !== doctype)) selectFirst = undefined
   if (dictId !== previousDictId) {
      columnWidth.value = undefined
      endResize()
   }
})
watch([entryList, () => activeDictionary.entryId, () => activeDictionary.entryList], () => {
   revealSelection()
   const entries = activeDictionary.entryList
   if (selectFirst && entries && selectFirst.dictId === activeDictionary.dictId && selectFirst.doctype === activeDictionary.doctype) {
      selectFirst = undefined
      if (entries[0]) void selectEntry(entries[0].id)
   }
}, { flush: 'post' })

onMounted(() => {
   document.addEventListener('keydown', onEditorShortcut)
})
onBeforeUnmount(() => {
   document.removeEventListener('keydown', onEditorShortcut)
   endResize()
})

function setFlag(id: number, flag: string) {
   if (canEdit.value && entryEditor.value?.allowFlagChange(id) !== false) {
      void dictionaryWorkspace.setEntryFlag(id, flag)
   }
}

function selectEntry(entryId: number) {
   if (entryId !== activeDictionary.entryId && !activeDictionary.entryList?.some(item => item.id === entryId && item.isSaving)) {
      return router.push(locateEntry.value(entryId))
   }
}

function onEditorShortcut(event: KeyboardEvent) {
   if (event.defaultPrevented || !(event.ctrlKey || event.metaKey) || !event.shiftKey) return
   const key = event.key.toLowerCase()
   if (key !== 'e' && key !== 's') return
   if (document.activeElement?.closest('.editor-dialog, .graphical-action-menu, .form-select-content')) return
   event.preventDefault()
   if (key === 'e') entryEditor.value?.toggleEditing()
   else entryEditor.value?.save()
}

function onListKeyDown(event: KeyboardEvent) {
   const link = event.target
   if (event.defaultPrevented || event.ctrlKey || event.metaKey || event.altKey ||
       !(link instanceof HTMLAnchorElement) || !link.classList.contains('headword-link')) return
   const step = entrySteps[event.key]
   if (step !== undefined) {
      event.preventDefault()
      const links = Array.from(entryList.value?.querySelectorAll<HTMLAnchorElement>(
         ':scope > li > .headword-link:is([href], :focus)') ?? [])
      links[Math.max(0, Math.min(links.length - 1, links.indexOf(link) + step))]?.focus()
      return
   }
   const flag = event.key === 'Delete' && flags.value.length ? '' : flags.value.find(item => item.key === event.key)?.name
   const row = link.closest<HTMLElement>('.dict-entry-row')
   const entry = activeDictionary.entryList?.[Number(row?.dataset.idx)]
   if (!entry || flag === undefined) return
   event.preventDefault()
   setFlag(entry.id, flag)
}

async function changeDoctype(doctype: string) {
   const { dictId } = activeDictionary
   if (!dictId || doctype === activeDictionary.doctype) return
   const intent = { dictId, doctype }
   selectFirst = intent
   const failure = await router.push({ name: 'edit', params: { dictId, doctype, entryId: '', mode: '' } })
   if (failure && selectFirst === intent) selectFirst = undefined
}

function revealSelection() {
   const list = entryList.value
   const selected = list?.querySelector<HTMLElement>('.dict-entry-row.selected')
   if (!list || !selected) return
   const top = selected.offsetTop
   const bottom = top + selected.offsetHeight - list.clientHeight
   if (top < list.scrollTop) list.scrollTop = top
   else if (bottom > list.scrollTop) list.scrollTop = bottom
}

function startResize(event: PointerEvent) {
   if (event.button !== 0 || !entryColumn.value) return
   const width = entryColumn.value.getBoundingClientRect().width
   resizeStart = { x: event.clientX, width, userSelect: document.body.style.userSelect }
   document.body.style.userSelect = 'none'
   ;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId)
}

function resizeColumn(event: PointerEvent) {
   if (resizeStart) columnWidth.value = Math.max(200, Math.round(resizeStart.width + event.clientX - resizeStart.x))
}

function endResize() {
   if (!resizeStart) return
   document.body.style.userSelect = resizeStart.userSelect
   resizeStart = undefined
}

function resizeBy(amount: number) {
   if (entryColumn.value) columnWidth.value = Math.max(200, Math.round(entryColumn.value.getBoundingClientRect().width + amount))
}
</script>

<style>
.dict-edit #dictEditContainer{
   display: flex;
}
.dict-edit .totalEntries{
   font-size: 0.85rem;
   color: #b8b8b8;
   margin-left: 1.3rem;
   text-transform: none;
}
.dict-edit .doctypes button {
   color: inherit;
   border: 0;
   width: 100%;
   height: 100%;
   background: transparent;
   line-height: inherit;
   text-transform: inherit;
   cursor: pointer;
}
.dict-edit .doctypes button[aria-pressed="true"] {
   font-weight: bold;
}
.dict-edit .resizeHandle{
   cursor: ew-resize;
   touch-action: none;
   width: 5px;
   min-height: 100%;
   background-color: whitesmoke;
   margin: 0 10px;
}
.dict-edit .resizeHandle:hover{
   background-color: #cfcfcf;
}
.dict-edit .entry-list {
   position: relative;
   max-height: 80vh;
   overflow-y: auto;
   margin: 0;
}
.dict-edit .dictLeftCol{
   min-width: 200px;
   min-height: 50vh;
   position: relative;
   display: flex;
   flex-direction: column;
   gap: 0.25rem;
}
.dict-edit .dictRightCol{
   min-width: 500px;
   flex: 1;
}
</style>
