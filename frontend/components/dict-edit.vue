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
               <div ref="entryList" class="entry-list collection">
                  <div v-for="(entry, idx) in activeDictionary.entryList" :key="entry.id"
                        :data-idx="idx" class="collection-item"
                        :class="{ saving: entry.isSaving, selected: entry.id == activeDictionary.entryId, focused: idx + 1 === cursorPosition }"
                        @click="onHeadwordClick(entry.id, $event)">
                     <span class="lineNum">{{ idx + 1 }}.</span>
                     <RouterLink :to="{ name: 'edit', params: { dictId: activeDictionary.dictId, doctype: activeDictionary.doctype, entryId: entry.id, mode: activeDictionary.mode }, query: $route.query }"
                                 custom v-slot="{ href, navigate }">
                        <a :href="entry.isSaving ? undefined : href" :aria-disabled="entry.isSaving || undefined"
                           class="headword-link" :class="{ 'red-text': entry.id === activeDictionary.entryId }"
                           @click.stop="onHeadwordLinkClick($event, Boolean(entry.isSaving), navigate)">
                           <RawHtml :content="entry.title || '&amp;nbsp;' "/>
                        </a>
                     </RouterLink>
                     <DropdownMenuRoot v-if="flags.length" :modal="false">
                        <DropdownMenuTrigger type="button" class="flag" :class="entry.flag ? 'badge' : 'noFlag'"
                                             :style="getFlagStyle(entry.flag)" :disabled="!canFlag(entry.id)"
                                             :title="entryEditor?.protectedEntryId === entry.id ? 'Finish editing before changing the flag' : undefined"
                                             :aria-label="'Flag for entry ' + entry.id"
                                             @click.stop>
                           {{ flagsByName.get(entry.flag)?.label || entry.flag || 'No flag' }}
                        </DropdownMenuTrigger>
                        <DropdownMenuPortal>
                           <DropdownMenuContent class="entry-flag-menu" align="end" :side-offset="4" :collision-padding="8">
                              <DropdownMenuItem @select="setFlag(entry.id, '')">
                                 <i class="material-symbols-outlined grey-text" aria-hidden="true">label_outline</i>
                                 <span>No flag</span>
                                 <kbd>Delete</kbd>
                              </DropdownMenuItem>
                              <DropdownMenuItem v-for="flag in flags" :key="flag.name"
                                                @select="setFlag(entry.id, flag.name)">
                                 <i class="material-symbols-outlined" :style="{ color: flag.color }" aria-hidden="true">label</i>
                                 <span>{{ flag.label }}</span>
                                 <kbd v-if="flag.key">{{ flag.key }}</kbd>
                              </DropdownMenuItem>
                           </DropdownMenuContent>
                        </DropdownMenuPortal>
                     </DropdownMenuRoot>
                  </div>
                  <div v-if="!activeDictionary.entryList.length && !activeDictionary.isEntryListLoading"
                        style="padding-top: 10vh;">
                     <h2 class="grey-text center-align">No entries</h2>
                  </div>
               </div>
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
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
   DropdownMenuContent, DropdownMenuItem, DropdownMenuPortal, DropdownMenuRoot, DropdownMenuTrigger
} from 'reka-ui'
import { flagTextColor } from './entry-flags.js'
import { activeDictionary, dictionaryWorkspace, entryPageSize } from '../js/dictionary-workspace.ts'
import { myDictionaries } from '../js/my-dictionaries.ts'
import DictEditEntry from './dict-edit-entry.vue'
import DictEntryFilter from './dict-entry-filter.vue'
import DictEntryPagination from './dict-entry-pagination.vue'
import DictNav from './dict-nav.vue'
import LoadingOverlay from './loading-overlay.vue'
import RawHtml from './raw-html.vue'

const router = useRouter()
const entryEditor = ref<InstanceType<typeof DictEditEntry> | null>(null)
const entryColumn = ref<HTMLElement | null>(null)
const entryList = ref<HTMLElement | null>(null)
const focused = ref(false)
const columnWidth = ref<number>()
const cursorPosition = ref<number>()
let selectFirst: { dictId: string; doctype: string } | undefined
let resizeStart: { x: number; width: number; userSelect: string } | undefined

const canEdit = computed(() => Boolean(activeDictionary.userAccess?.canEdit))
const flags = computed(() => activeDictionary.config?.flagging.flags ?? [])
const flagsByName = computed(() => new Map(flags.value.map(flag => [flag.name, flag])))

watch([() => activeDictionary.dictId, () => activeDictionary.doctype], ([dictId, doctype], [previousDictId]) => {
   if (selectFirst && (selectFirst.dictId !== dictId || selectFirst.doctype !== doctype)) selectFirst = undefined
   if (dictId !== previousDictId) {
      focused.value = false
      columnWidth.value = undefined
      endResize()
   }
})
watch([() => activeDictionary.entryId, () => activeDictionary.entryList], ([id, entries]) => {
   const index = id && entries?.findIndex(entry => entry.id === id)
   cursorPosition.value = typeof index === 'number' && index >= 0 ? index + 1 : undefined
   void scrollCursorIntoView()
   if (selectFirst && entries && selectFirst.dictId === activeDictionary.dictId && selectFirst.doctype === activeDictionary.doctype) {
      selectFirst = undefined
      if (entries[0]) void selectEntry(entries[0].id)
   }
}, { immediate: true })

onMounted(() => {
   document.addEventListener('click', onDocumentClick)
   document.addEventListener('keydown', onDocumentKeyDown)
})
onBeforeUnmount(() => {
   document.removeEventListener('click', onDocumentClick)
   document.removeEventListener('keydown', onDocumentKeyDown)
   endResize()
})

function getFlagStyle(flag: string) {
   const backgroundColor = flagsByName.value.get(flag)?.color ?? 'initial'
   return { color: flagTextColor(backgroundColor), backgroundColor }
}

function canFlag(id: number) {
   return canEdit.value && entryEditor.value?.protectedEntryId !== id
}

function setFlag(id: number, flag: string) {
   if (canFlag(id)) void dictionaryWorkspace.setEntryFlag(id, flag)
}

function onHeadwordClick(entryId: number, event: MouseEvent) {
   onDocumentClick(event)
   if (!(event.ctrlKey || event.metaKey || event.shiftKey || event.altKey)) void selectEntry(entryId)
}

function onHeadwordLinkClick(event: MouseEvent, isSaving: boolean, navigate: (event: MouseEvent) => unknown) {
   if (isSaving) {
      event.preventDefault()
      return
   }
   onDocumentClick(event)
   void navigate(event)
}

function selectEntry(entryId: number) {
   const { dictId, doctype, mode } = activeDictionary
   if (entryId !== activeDictionary.entryId && !activeDictionary.entryList?.some(item => item.id === entryId && item.isSaving)) {
      return router.push({ name: 'edit', params: { dictId, doctype, entryId, mode }, query: router.currentRoute.value.query })
   }
}

function onDocumentClick(event: MouseEvent) {
   if (!(event.target instanceof Element) || !entryList.value) return
   focused.value = entryList.value.contains(event.target)
   const index = focused.value ? event.target.closest<HTMLElement>('.collection-item')?.dataset.idx : undefined
   cursorPosition.value = index === undefined ? undefined : Number(index) + 1
   void scrollCursorIntoView()
}

function onDocumentKeyDown(event: KeyboardEvent) {
   if (event.defaultPrevented) return
   const key = event.key.toLowerCase()
   if ((event.ctrlKey || event.metaKey) && event.shiftKey && ['e', 's'].includes(key)) {
      if (document.activeElement?.closest('.editor-dialog, .graphical-action-menu, .form-select-content')) return
      event.preventDefault()
      if (key === 'e') entryEditor.value?.toggleEditing()
      else entryEditor.value?.save()
      return
   }
   if (!focused.value || !activeDictionary.entryList?.length ||
       (event.target instanceof Element && event.target.closest('input, textarea, select, button, [contenteditable], [role=menu]'))) return
   const entry = activeDictionary.entryList[(cursorPosition.value ?? 0) - 1]
   switch (event.key) {
      case 'ArrowUp': moveCursor(-1); break
      case 'ArrowDown': moveCursor(1); break
      case 'PageUp': moveCursor(-10); break
      case 'PageDown': moveCursor(10); break
      case 'Enter': if (entry) void selectEntry(entry.id); break
      default: {
         const flag = event.key === 'Delete' && flags.value.length ? '' : flags.value.find(item => item.key === event.key)?.name
         if (!entry || flag === undefined) return
         setFlag(entry.id, flag)
      }
   }
   event.preventDefault()
}

async function changeDoctype(doctype: string) {
   const { dictId } = activeDictionary
   if (!dictId || doctype === activeDictionary.doctype) return
   const intent = { dictId, doctype }
   selectFirst = intent
   const failure = await router.push({ name: 'edit', params: { dictId, doctype, entryId: '', mode: '' } })
   if (failure && selectFirst === intent) selectFirst = undefined
}

function moveCursor(step: number) {
   const count = activeDictionary.entryList?.length ?? 0
   if (!count) return
   if (cursorPosition.value == null) cursorPosition.value = step > 0 ? 1 : count
   else cursorPosition.value = Math.max(1, Math.min(count, cursorPosition.value + step))
   void scrollCursorIntoView()
}

async function scrollCursorIntoView() {
   await nextTick()
   const list = entryList.value
   const selected = list?.querySelector<HTMLElement>('.focused')
   if (!list || !selected) return
   const rowTop = selected.offsetTop
   const max = list.scrollTop + list.clientHeight - selected.clientHeight
   if (rowTop < list.scrollTop) list.scrollTop = rowTop
   else if (rowTop > max) list.scrollTop = rowTop - list.clientHeight + selected.clientHeight
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
.dict-edit .collection-item{
   position: relative;
   display: flex;
   border-left: 5px solid white;
   padding-left: 0.2rem;
}
.dict-edit .collection-item.selected{
   border-left-color: #000;
}
.dict-edit .collection-item .headword-link{
   text-decoration: none;
   font-size: 1.2rem;
   letter-spacing: 1px;
   margin-right: auto;
}
.dict-edit .collection-item .flag {
   border: 0;
   background: transparent;
   cursor: pointer;
}
.dict-edit .collection-item .flag:disabled { cursor: default; opacity: 0.7; }
.entry-flag-menu {
   background: #fff;
   color: #333;
   box-shadow: 0 2px 8px #0002;
   min-width: 150px;
   max-height: var(--reka-dropdown-menu-content-available-height);
   overflow: auto;
   z-index: 1000;
}
.entry-flag-menu [role="menuitem"] {
   cursor: pointer;
   display: flex;
   align-items: center;
   gap: 8px;
   padding: 8px 12px;
   outline: none;
}
.entry-flag-menu [data-highlighted] { background: #eee; }
.entry-flag-menu kbd { margin-left: auto; }
.dict-edit .collection-item .badge{
   font-weight: bold;
   font-size: 1rem;
   color: #fff;
   white-space: nowrap;
   min-width: auto;
   border-radius: 2px;
   box-shadow: 0 2px 2px 0 rgb(0 0 0 / 14%),
      0 3px 1px -2px rgb(0 0 0 / 12%),
      0 1px 5px 0 rgb(0 0 0 / 20%);
}
.dict-edit .collection-item .noFlag{
   font-size: 1rem;
   color: grey;
}
.dict-edit .collection-item.saving::before{
   content: '';
   position: absolute;
   left: 0;
   right: 0;
   top: 0;
   bottom: 0;
   background-color: #ffffffe8;
   line-height: 100%;
   z-index: 500;
}
.dict-edit .collection-item.saving::after{
   content: 'saving...';
   position: absolute;
   transform: translateX(-50%) translateY(-50%);
   left: 50%;
   top: 50%;
   color: #6e6e6e;
   z-index: 501;
   font-size: 1.3rem;
   text-transform: uppercase;
}
.dict-edit .collection-item.focused{
   background-color: #eceff1;
}
.dict-edit .lineNum{
   font-size: 0.8rem;
   color: #b8b8b8;
   margin-right: 10px;
   min-width: 30px;
   text-align: right;
}
</style>
