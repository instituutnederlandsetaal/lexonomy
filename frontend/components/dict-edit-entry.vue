<template>
<div class="dict-edit-entry">
   <div class="row editorContainer">
      <div class="xonomy-envelope">
         <div id="toolbar" class="buttons">
            <button v-if="canEdit" id="butNew" class="btn btn-secondary" @click="leaveEntry('edit')">
               New<i class="material-icons right">add</i>
            </button>
            <span v-if="canEdit" class="divider"></span>
            <label for="idbox">ID</label>
            <input id="idbox" v-model="idInput" type="text" inputmode="numeric"
                   @keydown.stop @keyup.esc="idInput = entry?.id ? String(entry.id) : ''" @keyup.enter="openById">
            <button id="butOpen" class="btn btn-secondary" aria-label="Open entry" @click="openById">
               <i class="material-icons">send</i>
            </button>
            <span class="divider"></span>
            <button v-if="isEditing && canEdit" id="butSave" class="btn btn-secondary"
                    title="Ctrl + Shift + S" :disabled="mutating" @click="save">
               Save<span v-show="dirty" class="star">*</span><i class="material-icons right">save</i>
            </button>
            <button v-if="surface === 'view' && canEdit" id="butEdit" class="btn btn-secondary"
                    title="Ctrl + Shift + E" @click="toggleEditing">
               Edit<i class="material-icons right">edit</i>
            </button>
            <button v-if="isEditing && (!entry?.id || hasViewer)"
                    :id="entry?.id ? 'butView' : 'butNonew'" class="btn btn-secondary"
                    :disabled="mutating" @click="toggleEditing">
               Cancel<i v-if="entry?.id" class="material-icons right">cancel</i>
            </button>
            <button v-if="canEdit && entry?.id && (surface === 'view' || isEditing)"
                    id="butClone" class="btn btn-secondary" :disabled="mutating" @click="clone">
               Clone<i class="material-icons right">content_copy</i>
            </button>
            <button v-if="canEdit && entry?.id && (surface === 'view' || isEditing)"
                    id="butDelete" class="btn btn-secondary" :disabled="mutating" @click="remove">
               Delete<i class="material-icons right">delete</i>
            </button>
            <span v-if="invalidSource" id="errorMessage" role="alert">Invalid source code</span>
            <div class="toolbar-space"></div>
            <button v-if="isEditing && canEdit || surface === 'source'"
                    id="butSourceCode" class="btn btn-secondary right" :class="{ 'btn-flat': surface !== 'source' }"
                    title="Source code" :disabled="mutating" @click="toggleSource">
               <i class="material-icons">code</i>
            </button>
            <button v-if="canEdit && historyId && !reading" id="butHistory" class="btn btn-secondary right"
                    :class="{ 'btn-flat': surface !== 'history' }" title="History"
                    :disabled="mutating" @click="toggleHistory">
               <i class="material-icons">history</i>
            </button>
         </div>
         <div ref="container" id="container" :class="{
            empty: !editorEntry && !viewerEntry && surface !== 'source',
            withHistory: surface === 'history',
            withSourceCode: surface === 'source'
         }" :inert="mutating">
            <div v-if="editorEntry" :key="revision" :id="graphical ? 'editor' : undefined">
               <GraphicalEditor v-if="graphical" ref="graphicalEditor"
                  :xml="entry?.content || initialXml" :config="config" :dict-id="dictId" :user-dicts="userDicts"
                  @dirty-change="markDirty" @links-changed="refreshLinks"/>
               <CustomEntryEditor v-else-if="extensionSource" ref="customEditor" :source="extensionSource"
                  :entry="editorEntry" :config="config" :dict-id="dictId" :initial-xml="initialXml"
                  :read-only="!isEditing || !canEdit"
                  @dirty-change="markDirty" @open-entry="openRelatedEntry" @mount-failed="fallBackToBuiltIn"/>
               <LegacyEditor v-else-if="dictId" ref="legacyEditor" :entry="editorEntry" :config="config" :dict-id="dictId" :user-dicts="userDicts"
                  :readonly="!isEditing || !canEdit"
                  :initial-xml="editorEntry.content || initialXml"
                  @use-graphical="useGraphical = true" @dirty-change="markDirty"
                  @links-changed="refreshLinks" @status="showStatus" @open-entry="openRelatedEntry"/>
               <EntryLinks v-if="isEditing && entry?.id && dictId" ref="entryLinks" :entry-id="entry.id"
                           :dict-id="dictId" :can-delete="canEdit"/>
            </div>
            <div v-else-if="viewerEntry" id="viewer" class="viewer" :key="revision" @click="followHeadword">
               <RawHtml :content="viewerHtml"/>
               <EntryLinks v-if="surface === 'view' && entry?.id && dictId" :entry-id="entry.id" :dict-id="dictId"/>
            </div>
            <div v-else-if="surface === 'source'" id="sourceCode">
               <textarea ref="sourceInput" :value="source" aria-label="Entry XML" spellcheck="false"
                         @keydown.stop @input="markDirty(($event.target as HTMLTextAreaElement).value !== sourceInputValue)"></textarea>
            </div>
         </div>
         <div v-if="surface === 'history'" id="history">
            <template v-for="(item, index) in revisions" :key="item.revision_id">
               <div v-if="item.action !== 'delete' && item.action !== 'purge'" class="revision"
                    :class="{ current: selectedRevision === item, pretty: selectedRevision === item && previewHistory }"
>
                  <button v-if="hasViewer" type="button" class="pretty" aria-label="Show formatted revision"
                          @click="selectRevision(item, true)"></button>
                  <button v-if="index && canEdit" type="button" class="revive"
                          @click="reviveRevision(item)">Revive</button>
                  <button type="button" class="label" @click="selectRevision(item)">
                     Version {{ revisions.length - index }}
                  </button>
               </div>
               <div class="interRevision">
                  <div class="arrowTop"></div><div class="arrowMiddle"></div><div class="arrowBottom"></div>
                  <div class="revision-detail">
                     <b>{{ revisionAction[item.action] }}</b>
                     <template v-if="item.historiography.uploadStart"> while uploading</template>
                     <template v-if="item.historiography.viaApi"> through API</template>
                     <template v-if="item.historiography.refactoredFrom">
                        as a subentry of
                        <RouterLink :to="entryRoute(item.historiography.refactoredFrom, 'view')">
                           {{ item.historiography.refactoredFrom }}
                        </RouterLink>
                     </template>
                  </div>
                  <div v-if="item.email" class="revision-detail"><b>By:</b> {{ item.email }}</div>
                  <div class="revision-detail"><b>When:</b> {{ item.when }}</div>
               </div>
            </template>
         </div>
         <div id="statusbar" role="status">
            <div v-show="alert" class="alertmessage yellow">
               <span class="text">{{ alert }}</span>
               <button type="button" class="right clickable closeIcon" aria-label="Dismiss alert" @click="alert = ''">
                  <i class="material-symbols-outlined" aria-hidden="true">close</i>
               </button>
            </div>
            <span class="statusmessage">
               <span v-if="statusStyle" :class="statusStyle"></span>{{ status }}
            </span>
         </div>
      </div>
      <div id="editorStyle"><component :is="'style'" v-if="editing._css">{{ editing._css }}</component></div>
   </div>
</div>
</template>

<script setup lang="ts">
import { editorLockedKey } from './graphical-editor/editor-context.ts'
import { computed, defineAsyncComponent, nextTick, onBeforeUnmount, provide, readonly, ref, watch } from 'vue'
import { isNavigationFailure, NavigationFailureType, useRoute, useRouter } from 'vue-router'
import { entryEditorApi, type EntryDraft, type EntryRevision } from '../js/entry-editor-api.ts'
import { dictionaryWorkspace, type WorkspaceConfig } from '../js/dictionary-workspace.ts'
import type { MyDictionary } from '../js/my-dictionaries.ts'
import { crossReferenceHref, searchEntriesFromRoute } from '../js/entry-search.ts'
import { parseXml } from '../js/xml.ts'
import { initialDocument, parseDTD } from '../libs/xonomy-tools/dtdconvert/dtd2xonomy.js'
import { createInitialXml } from '../widgets/xematron.ts'
import { entryHtml } from '../widgets/xemplatron.ts'
import CustomEntryEditor from './entry-editor/CustomEntryEditor.vue'
import EntryLinks from './entry-editor/EntryLinks.vue'
import { confirmEntryNavigation, unsavedEntry } from './entry-editor/unsaved.js'
import GraphicalEditor from './graphical-editor/GraphicalEditor.vue'
import { xemaElementId, xmlElementName } from '../js/xema.ts'
import { readFormattingFields } from '../js/xemplate.ts'
import RawHtml from './raw-html.vue'
import './entry-editor/editor.css'

type EntryMode = 'edit' | 'view'
type Surface = EntryMode | 'empty' | 'source' | 'history'

const props = defineProps<{
   dictionaryConfig: WorkspaceConfig
   dictId: string
   doctype: string | null
   entryId: number | null
   mode: EntryMode
   canEdit: boolean
   userDicts: readonly MyDictionary[]
}>()
const LegacyEditor = defineAsyncComponent(() => import('./entry-editor/LegacyEditor.vue'))
const revisionAction = { create: 'Created', update: 'Changed', delete: 'Deleted', purge: 'Bulk-deleted', autonumber: 'Auto-numbered' }
const route = useRoute()
const router = useRouter()

const container = ref<HTMLElement | null>(null)
const sourceInput = ref<HTMLTextAreaElement | null>(null)
const customEditor = ref<InstanceType<typeof CustomEntryEditor> | null>(null)
const legacyEditor = ref<InstanceType<typeof LegacyEditor> | null>(null)
const graphicalEditor = ref<InstanceType<typeof GraphicalEditor> | null>(null)
const entryLinks = ref<InstanceType<typeof EntryLinks> | null>(null)
const entry = ref<EntryDraft | null>(null)
const idInput = ref('')
const surface = ref<Surface>('empty')
const revisions = ref<EntryRevision[]>([])
const selectedRevision = ref<EntryRevision | null>(null)
const previewHistory = ref(false)
const status = ref('Ready.')
const statusStyle = ref('')
const alert = ref('')
const reading = ref(false)
const mutating = ref(false)
provide(editorLockedKey, readonly(mutating))
const useGraphical = ref(false)
const baseDirty = ref(false)
const source = ref('')
const invalidSource = ref(false)

let requestedKey: string | undefined
let draftVersion = 0
const revision = ref(0)
const failedExtensionRevision = ref<number>()
const config = computed(() => {
   const { xema } = props.dictionaryConfig
   const { doctype } = props
   const schemaId = surface.value === 'history' && selectedRevision.value?.schemaId || entry.value?.schemaId
   const root = schemaId && xema.elements[schemaId] && (!doctype || xmlElementName(xema, schemaId) === doctype)
      ? schemaId : doctype ? xemaElementId(xema, doctype) : xema.root
   return { ...props.dictionaryConfig, xema: { ...xema, root } }
})
const editing = computed(() => config.value.editing)
const sourceInputValue = computed(() => source.value.replace(/\r\n?/g, '\n'))
const isEditing = computed(() => surface.value === 'edit')
const dirty = unsavedEntry
const historyId = computed(() => entry.value?.id || props.entryId || parseEntryId(idInput.value))
const hasViewer = computed(() => {
   const { xema, xemplate } = config.value
   const { shown } = readFormattingFields(xemplate, xema.root, xmlElementName(xema, xema.root))
   return Boolean(xemplate._xsl || xemplate._css || shown === true || shown === 'true')
})
const initialXml = computed(() => {
   const { xema } = config.value
   return xema._newXml || xema.newXml || (xema._dtd && initialDocument(parseDTD(xema._dtd))) || createInitialXml(xema)
})
const extensionSource = computed(() => editing.value.editorApiVersion === 1 && failedExtensionRevision.value !== revision.value
   ? editing.value._js : undefined)
const graphical = computed(() => isEditing.value && props.canEdit && editing.value.xonomyMode === 'graphical' &&
   !extensionSource.value && (!editing.value._js || editing.value.editorApiVersion != null || useGraphical.value))
const editorEntry = computed(() => {
   if (surface.value === 'history') return previewHistory.value ? null : selectedRevision.value
   return isEditing.value ? entry.value ?? { content: '' } : null
})
const viewerEntry = computed(() => {
   if (surface.value === 'history') return previewHistory.value ? selectedRevision.value : null
   return surface.value === 'view' ? entry.value : null
})
const viewerHtml = computed(() => viewerEntry.value ? entryHtml(viewerEntry.value, config.value, crossReferenceHref) : '')

watch([() => props.dictId, () => props.doctype, () => props.entryId, () => props.mode],
   ([, , id, mode]) => showRequestedEntry(id, mode), { immediate: true })
watch([viewerHtml, () => route.query.link], showLinkTarget, { flush: 'post' })
onBeforeUnmount(() => {
   revision.value++
   unsavedEntry.value = false
})
defineExpose({ toggleEditing, save, allowFlagChange })

function showLinkTarget() {
   if (surface.value !== 'view') return
   const target = route.query.link
   for (const link of container.value?.querySelectorAll<HTMLElement>('#viewer .linkable[name]') ?? []) {
      const name = link.getAttribute('name')
      link.style.display = name === target ? 'inline' : ''
      if (name === target) link.scrollIntoView()
   }
}

function showStatus(text = 'Ready.', style = '') {
   status.value = text
   statusStyle.value = style
}

function allowFlagChange(id: number) {
   const protectedEntry = isEditing.value || surface.value === 'source' || reading.value || mutating.value
   if (!protectedEntry || id !== (entry.value?.id ?? props.entryId)) return true
   showStatus('Finish editing before changing the flag.', 'warn')
   return false
}

function fallBackToBuiltIn() {
   failedExtensionRevision.value = revision.value
   showStatus('The custom editor failed to open. Using the built-in editor.', 'warn')
}

function markDirty(value = true) {
   draftVersion++
   dirty.value = baseDirty.value || value
}

function show(nextEntry: EntryDraft | null, nextSurface: Surface, isDirty = false) {
   revision.value++
   entry.value = nextEntry
   surface.value = nextSurface
   baseDirty.value = isDirty
   reading.value = false
   mutating.value = false
   useGraphical.value = false
   invalidSource.value = false
   alert.value = ''
   markDirty(isDirty)
}

function entryKey(id: number | null, mode: EntryMode) {
   return JSON.stringify([props.dictId, props.doctype, id, mode])
}

function entryRoute(entryId?: number, mode?: EntryMode) {
   const { dictId, doctype } = props
   return { name: 'edit', params: { dictId, doctype, entryId: entryId ?? '', mode: mode ?? '' }, query: route.query }
}

function openRelatedEntry(entryId: number, entryType?: string) {
   const { dictId, doctype, mode } = props
   void router.push({ name: 'edit', params: { dictId, doctype: entryType || doctype, entryId, mode }, query: route.query })
}

async function leaveEntry(nextSurface: Surface) {
   if (mutating.value) return
   const failure = await router.push(entryRoute())
   if (failure && !(isNavigationFailure(failure, NavigationFailureType.duplicated) && confirmEntryNavigation())) return
   show(null, nextSurface)
   idInput.value = ''
   showStatus()
}

function showRequestedEntry(id: number | null, mode: EntryMode) {
   const key = entryKey(id, mode)
   if (requestedKey === key) return
   requestedKey = key
   if (id) void loadEntry(id, mode)
   else {
      show(null, 'empty')
      idInput.value = ''
      showStatus()
   }
}

function parseEntryId(text: string) {
   const value = text.trim()
   const id = Number(value)
   return /^\d+$/.test(value) && Number.isSafeInteger(id) && id > 0 ? id : null
}

function openById() {
   if (mutating.value) return
   if (!idInput.value.trim()) {
      void leaveEntry('empty')
      return
   }
   const id = parseEntryId(idInput.value)
   if (id) void openEntry(id, entry.value?.id && isEditing.value ? 'edit' : 'view')
   else showStatus('No such item.', 'warn')
}

async function openEntry(id: number, mode: EntryMode) {
   if (dictionaryWorkspace.pendingFlagSave(props.dictId, id)) {
      showStatus('Wait for the flag change to finish.', 'warn')
      return
   }
   const failure = await router.push(entryRoute(id, mode))
   if (isNavigationFailure(failure, NavigationFailureType.duplicated) && confirmEntryNavigation()) {
      await loadEntry(id, mode)
   }
}

async function loadEntry(id: number, mode: EntryMode) {
   const dictionary = props.dictId
   show(null, 'empty')
   idInput.value = String(id)
   reading.value = true
   showStatus('Getting item...', 'wait')
   const requestRevision = revision.value
   try {
      const pendingFlag = dictionaryWorkspace.pendingFlagSave(dictionary, id)
      if (pendingFlag) {
         await pendingFlag
         if (requestRevision !== revision.value) return
      }
      const result = await entryEditorApi.read(dictionary, id)
      if (requestRevision !== revision.value) return
      if (result.success) {
         entry.value = result
         const nextSurface = !hasViewer.value || (mode === 'edit' && props.canEdit) ? 'edit' : 'view'
         show(result, nextSurface)
         showStatus()
      } else showStatus('No such item.', 'warn')
   } catch {
      if (requestRevision === revision.value) showStatus('Failed to load entry.', 'warn')
   } finally {
      if (requestRevision === revision.value) reading.value = false
   }
}

function toggleEditing() {
   if (mutating.value) return
   const id = entry.value?.id
   if (surface.value === 'view' && props.canEdit && id) void openEntry(id, 'edit')
   else if (isEditing.value && id && hasViewer.value) void openEntry(id, 'view')
   else if (isEditing.value && !id) void leaveEntry('empty')
}

async function harvest() {
   const requestRevision = revision.value
   try {
      const content: unknown = await (customEditor.value || graphicalEditor.value || legacyEditor.value)?.harvest()
      return typeof content === 'string' ? content : null
   } catch {
      if (requestRevision === revision.value) showStatus('Failed to read editor content.', 'warn')
      return null
   }
}

function save() {
   if (isEditing.value && props.canEdit) void persist(entry.value?.id)
}

function clone() {
   if (!mutating.value && props.canEdit && entry.value?.id && confirmEntryNavigation()) void persist()
}

async function persist(id?: number) {
   const dictionary = props.dictId
   if (mutating.value) return
   mutating.value = true
   const requestRevision = revision.value
   try {
      const pendingContent = isEditing.value ? harvest() : entry.value?.content
      const savedVersion = draftVersion
      const content = await pendingContent
      if (!content || requestRevision !== revision.value) return
      showStatus('Saving...', 'wait')
      const result = await entryEditorApi.save(dictionary, content, id)
      if (requestRevision !== revision.value && result.success) void dictionaryWorkspace.refreshEntries(dictionary)
      if (requestRevision !== revision.value) return
      if (!result.success) throw new Error('Entry rejected')
      if (draftVersion !== savedVersion) {
         // Keep the active document, including changes made by a custom editor during the request.
         if (!id && !entry.value?.id) {
            entry.value = { ...entry.value, id: result.id, content: entry.value?.content ?? result.content }
            idInput.value = String(result.id)
         }
         showStatus('Saved an earlier version. Save again to include your latest edits.', 'warn')
         void dictionaryWorkspace.refreshEntries(dictionary)
         return
      }
      const nextSurface = hasViewer.value ? 'view' : 'edit'
      show(result, nextSurface)
      idInput.value = String(result.id)
      requestedKey = entryKey(result.id, nextSurface)
      void router.push(entryRoute(result.id, nextSurface))
      showStatus()
      if (result.feedback?.type === 'saveFeedbackHeadwordExists') {
         alert.value = `WARNING: another entry with this headword exists. ID=${result.feedback.info}`
      } else if (result.feedback) {
         alert.value = result.feedback.type
      }
      void dictionaryWorkspace.refreshEntries(dictionary)
   } catch {
      if (requestRevision === revision.value) showStatus('Failed to save.', 'warn')
   } finally {
      if (requestRevision === revision.value) mutating.value = false
   }
}

async function remove() {
   const dictionary = props.dictId
   const id = entry.value?.id
   if (!id || !props.canEdit || mutating.value || !window.confirm('Careful now! Are you sure?')) return
   const requestRevision = revision.value
   mutating.value = true
   showStatus('Deleting...', 'wait')
   try {
      const result = await entryEditorApi.remove(dictionary, id)
      if (result.success) void dictionaryWorkspace.refreshEntries(dictionary)
      if (requestRevision !== revision.value) return
      if (!result.success) throw new Error('Deletion rejected')
      show(null, 'empty')
      idInput.value = ''
      showStatus()
      await router.replace(entryRoute())
   } catch {
      if (requestRevision === revision.value) showStatus('Failed to delete.', 'warn')
   } finally {
      if (requestRevision === revision.value) mutating.value = false
   }
}

function refreshLinks() {
   void entryLinks.value?.load()
}

async function toggleSource() {
   if (mutating.value) return
   if (surface.value === 'source' && sourceInput.value) {
      const changed = sourceInput.value.value !== sourceInputValue.value
      const content = changed ? sourceInput.value.value : source.value
      if (!parseXml(content)) {
         invalidSource.value = true
         return
      }
      show({ ...entry.value, content }, 'edit', baseDirty.value || changed)
      return
   }
   const requestRevision = revision.value
   const pendingContent = harvest()
   const sourceVersion = draftVersion
   const content = await pendingContent
   if (content == null || requestRevision !== revision.value || mutating.value) return
   if (sourceVersion !== draftVersion) {
      showStatus('The entry changed while preparing source. Open source again to include the latest edits.', 'warn')
      return
   }
   source.value = content
   show(entry.value, 'source', dirty.value)
   await nextTick()
   sourceInput.value?.focus()
}

async function toggleHistory() {
   const dictionary = props.dictId
   const id = historyId.value
   if (!id || mutating.value || !confirmEntryNavigation()) return
   if (surface.value === 'history') {
      void openEntry(id, 'view')
      return
   }
   revisions.value = []
   selectedRevision.value = null
   show(entry.value, 'history')
   showStatus('Getting history...', 'wait')
   const requestRevision = revision.value
   try {
      const data = await entryEditorApi.history(dictionary, id)
      if (requestRevision !== revision.value) return
      showStatus()
      revisions.value = data.history
      const latest = revisions.value[0]
      if (latest && latest.action !== 'delete' && latest.action !== 'purge') selectRevision(latest)
   } catch {
      if (requestRevision === revision.value) showStatus('Failed to get history.', 'warn')
   }
}

function selectRevision(item: EntryRevision, pretty = false) {
   selectedRevision.value = item
   previewHistory.value = pretty
   revision.value++
}

async function reviveRevision(item: EntryRevision) {
   const id = item.entry_id
   const previousKey = requestedKey
   const key = entryKey(id, 'edit')
   requestedKey = key
   const failure = await router.push(entryRoute(id, 'edit'))
   if (failure && !isNavigationFailure(failure, NavigationFailureType.duplicated)) {
      if (requestedKey === key) requestedKey = previousKey
      return
   }
   if (requestedKey !== key || route.name !== 'edit' || entryKey(props.entryId, 'edit') !== key) return
   idInput.value = String(id)
   show({ ...item, id }, 'edit', true)
}

async function followHeadword(event: MouseEvent) {
   if (!(event.target instanceof Element)) return
   const link = event.target.closest<HTMLAnchorElement>('a.xref[data-text]')
   if (!link || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return
   event.preventDefault()
   const requestRevision = revision.value
   const results = await searchEntriesFromRoute({ searchtext: link.dataset.text, modifier: 'substring' })
   if (requestRevision === revision.value && results?.[0]) void openEntry(results[0].id, 'view')
}
</script>
