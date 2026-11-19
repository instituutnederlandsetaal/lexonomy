<template>
<dict-edit-entry>
   <div class="row editorContainer">
      <div class="xonomy-envelope">
         <div id="toolbar" class="buttons">
            <button v-if="canEdit" id="butNew" class="btn btn-secondary" @click="leaveEntry('edit')">
               New<i class="material-icons right">add</i>
            </button>
            <span v-if="canEdit" class="divider"></span>
            <label for="idbox">ID</label>
            <input id="idbox" v-model="idInput" type="text" inputmode="numeric"
                   @keydown.stop @keyup.esc="idInput = entry?.id ?? ''" @keyup.enter="openById">
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
            <button v-if="idInput && !reading" id="butHistory" class="btn btn-secondary right"
                    :class="{ 'btn-flat': surface !== 'history' }" title="History"
                    :disabled="mutating" @click="toggleHistory">
               <i class="material-icons">history</i>
            </button>
         </div>
         <div id="container" :class="{
            empty: !editorEntry && !viewerEntry && surface !== 'source',
            withHistory: surface === 'history',
            withSourceCode: surface === 'source'
         }" :inert="mutating">
            <div v-if="editorEntry" :key="revision" :id="graphical ? 'editor' : undefined">
               <GraphicalEditor v-if="graphical" ref="graphicalEditor"
                  :entry="graphicalEntry" @dirty-change="markDirty" @links-changed="refreshLinks"/>
               <LegacyEditor v-else ref="legacyEditor" :entry="editorEntry" :config="config"
                  :readonly="!isEditing || !canEdit"
                  :initial-xml="editorEntry.content || initialXml"
                  @use-graphical="useGraphical = true" @dirty-change="markDirty"
                  @links-changed="refreshLinks" @status="showStatus"/>
               <EntryLinks v-if="isEditing && entry?.id" ref="entryLinks" :entry-id="entry.id"
                           :dict-id="activeDictionary.dictId" :can-delete="canEdit"/>
            </div>
            <div v-else-if="viewerEntry" id="viewer" class="viewer" :key="revision" @click="followHeadword">
               <RawHtml :content="viewerHtml"/>
               <EntryLinks v-if="surface === 'view'" :entry-id="viewerEntry.id" :dict-id="activeDictionary.dictId"/>
            </div>
            <div v-else-if="surface === 'source'" id="sourceCode">
               <textarea ref="source" :value="source" aria-label="Entry XML" spellcheck="false"
                         @keydown.stop @input="markDirty($event.target.value !== sourceInputValue)"></textarea>
            </div>
         </div>
         <div v-if="surface === 'history'" id="history">
            <template v-for="(item, index) in revisions" :key="item.revision_id">
               <div v-if="item.action !== 'delete' && item.action !== 'purge'" class="revision"
                    :class="{ current: selectedRevision === item, pretty: selectedRevision === item && previewHistory }"
                    @click="selectRevision(item)">
                  <span v-if="hasViewer" class="pretty" role="button" tabindex="0" aria-label="Show formatted revision"
                        @click.stop="selectRevision(item, true)" @keydown.enter.stop="selectRevision(item, true)"></span>
                  <span v-if="index && canEdit" class="revive" role="button" tabindex="0"
                        @click.stop="reviveRevision(item)" @keydown.enter.stop="reviveRevision(item)">Revive</span>
                  <span class="label">Version {{ revisions.length - index }}</span>
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
               <span class="right clickable closeIcon">
                  <i class="material-symbols-outlined" @click="alert = ''">close</i>
               </span>
            </div>
            <span class="statusmessage">
               <span v-if="statusStyle" :class="statusStyle"></span>{{ status }}
            </span>
         </div>
      </div>
      <div id="editorStyle"><component :is="'style'" v-if="editing._css">{{ editing._css }}</component></div>
   </div>
</dict-edit-entry>
</template>

<script>
import { defineAsyncComponent } from 'vue'
import { api } from '../js/api.ts'
import { activeDictionary, dictionaryWorkspace } from '../js/dictionary-workspace.ts'
import { myDictionaries } from '../js/my-dictionaries.ts'
import { searchEntriesFromRoute } from '../js/entry-search.ts'
import { isNavigationFailure, NavigationFailureType } from 'vue-router'
import { parseXml } from '../js/xml.js'
import { initialDocument, parseDTD } from '../libs/xonomy-tools/dtdconvert/dtd2xonomy.js'
import { Xematron } from '../widgets/xematron.js'
import { entryHtml } from '../widgets/xemplatron.js'
import EntryLinks from './entry-editor/EntryLinks.vue'
import { confirmEntryNavigation, unsavedEntry } from './entry-editor/unsaved.js'
import GraphicalEditor from './graphical-editor/GraphicalEditor.vue'
import RawHtml from './raw-html.vue'
import './entry-editor/editor.css'

const LegacyEditor = defineAsyncComponent(() => import('./entry-editor/LegacyEditor.vue'))
const revisionAction = { create: 'Created', update: 'Changed', delete: 'Deleted', purge: 'Bulk-deleted' }

export default {
   components: { EntryLinks, GraphicalEditor, LegacyEditor, RawHtml },
   props: { dictionaryConfig: { type: Object, required: true } },
   data() {
      return {
         activeDictionary, revisionAction,
         entry: null, idInput: '', surface: 'empty', requestedKey: null,
         revision: 0, revisions: [], selectedRevision: null, previewHistory: false,
         status: 'Ready.', statusStyle: '', alert: '', reading: false, mutating: false,
         useGraphical: false, baseDirty: false, source: '', invalidSource: false,
      }
   },
   computed: {
      requestedEntry() {
         return [activeDictionary.entryId, activeDictionary.mode, activeDictionary.doctype]
      },
      dictPath() {
         return encodeURIComponent(activeDictionary.dictId)
      },
      editing() {
         return this.config.editing
      },
      config() {
         const config = this.dictionaryConfig
         return { ...config, xema: { ...config.xema, root: activeDictionary.doctype || config.xema.root } }
      },
      canEdit() {
         return activeDictionary.userAccess?.canEdit
      },
      sourceInputValue() {
         return this.source.replace(/\r\n?/g, '\n')
      },
      isEditing() {
         return this.surface === 'edit'
      },
      dirty() {
         return unsavedEntry.value
      },
      hasViewer() {
         const { xema, xemplate } = this.config
         return Boolean(xemplate._xsl || xemplate._css ||
            (xemplate[xema.root]?.shown && xemplate[xema.root].shown !== 'false'))
      },
      initialXml() {
         const { xema } = this.config
         if (xema._xonomyDocSpec && xema._newXml) return xema._newXml
         return (xema._dtd && initialDocument(parseDTD(xema._dtd))) || Xematron.xema2xml(xema)
      },
      graphical() {
         return this.isEditing && this.canEdit && this.editing.xonomyMode === 'graphical'
            && (!this.editing._js || this.useGraphical)
      },
      editorEntry() {
         if (this.surface === 'history') return this.previewHistory ? null : this.selectedRevision
         return this.isEditing ? this.entry ?? { id: 0 } : null
      },
      graphicalEntry() {
         return {
            id: this.entry?.id, xml: this.entry?.content || this.initialXml,
            doctype: this.entry?.doctype || activeDictionary.doctype,
            dictId: activeDictionary.dictId, dictConfigs: this.config, userDicts: myDictionaries.items
         }
      },
      viewerEntry() {
         if (this.surface === 'history') return this.previewHistory ? this.selectedRevision : null
         return this.surface === 'view' ? this.entry : null
      },
      viewerHtml() {
         return this.viewerEntry ? entryHtml(this.viewerEntry, this.config) : ''
      }
   },
   watch: {
      requestedEntry([id, mode]) {
         this.showRequestedEntry(id, mode)
      },
      viewerHtml: { flush: 'post', handler: 'showLinkTarget' },
      '$route.query.link': { flush: 'post', handler: 'showLinkTarget' }
   },
   mounted() {
      this.showRequestedEntry(activeDictionary.entryId, activeDictionary.mode)
   },
   beforeUnmount() {
      this.revision++
      unsavedEntry.value = false
   },
   methods: {
      showLinkTarget() {
         if (this.surface !== 'view') return
         const target = this.$route.query.link
         for (const link of this.$el.querySelectorAll('#viewer .linkable[name]')) {
            const name = link.getAttribute('name')
            link.style.display = name === target ? 'inline' : ''
            if (name === target) link.scrollIntoView()
         }
      },
      showStatus(text = 'Ready.', style = '') {
         this.status = text
         this.statusStyle = style
      },
      markDirty(dirty = true) {
         unsavedEntry.value = this.baseDirty || dirty
      },
      show(entry, surface, dirty = false) {
         this.revision++
         this.entry = entry
         this.surface = surface
         this.baseDirty = dirty
         this.reading = false
         this.mutating = false
         this.useGraphical = false
         this.invalidSource = false
         this.markDirty(dirty)
      },
      async leaveEntry(surface) {
         if (this.mutating) return
         const failure = await this.$router.push(this.entryRoute())
         if (failure && !(isNavigationFailure(failure, NavigationFailureType.duplicated) && confirmEntryNavigation())) return
         this.show(null, surface)
         this.idInput = ''
         this.showStatus()
      },
      entryKey(id, mode) {
         return `${activeDictionary.doctype}/${id || ''}/${mode || 'view'}`
      },
      entryRoute(entryId, mode) {
         const { dictId, doctype } = activeDictionary
         return { name: 'edit', params: { dictId, doctype, entryId: entryId || '', mode: mode || '' },
            query: this.$route.query }
      },
      showRequestedEntry(id, mode) {
         const key = this.entryKey(id, mode)
         if (this.requestedKey === key) return
         this.requestedKey = key
         if (id) this.loadEntry(id, mode)
         else {
            this.show(null, 'empty')
            this.idInput = ''
            this.showStatus()
         }
      },
      openById() {
         const id = this.idInput.toString().trim()
         if (!id) {
            this.leaveEntry('empty')
         } else if (/^\d+$/.test(id) && Number.isSafeInteger(Number(id)) && Number(id) > 0) {
            this.openEntry(Number(id), this.entry?.id && this.isEditing ? 'edit' : 'view')
         } else {
            this.showStatus('No such item.', 'warn')
         }
      },
      async openEntry(id, mode) {
         const failure = await this.$router.push(this.entryRoute(id, mode))
         if (isNavigationFailure(failure, NavigationFailureType.duplicated) && confirmEntryNavigation()) {
            this.loadEntry(id, mode)
         }
      },
      async loadEntry(id, mode) {
         const surface = !this.hasViewer || mode === 'edit' && this.canEdit ? 'edit' : 'view'
         this.show(null, 'empty')
         this.idInput = id
         this.reading = true
         this.showStatus('Getting item...', 'wait')
         const revision = this.revision
         const entry = await api.post(`${this.dictPath}/entryread.json`, { id }).catch(() => null)
         if (revision !== this.revision) return
         this.reading = false
         if (!entry?.success) {
            this.showStatus('No such item.', 'warn')
            return
         }
         this.show(entry, surface)
         this.showStatus()
      },
      toggleEditing() {
         if (this.mutating) return
         if (this.surface === 'view' && this.canEdit) this.openEntry(this.entry.id, 'edit')
         else if (this.isEditing && this.entry?.id && this.hasViewer) this.openEntry(this.entry.id, 'view')
         else if (this.isEditing && !this.entry?.id) this.leaveEntry('empty')
      },
      async harvest() {
         try {
            return await (this.$refs.graphicalEditor || this.$refs.legacyEditor)?.harvest()
         } catch {
            this.showStatus('Failed to read editor content.', 'warn')
         }
      },
      async save() {
         if (!this.isEditing || !this.canEdit || this.mutating) return
         const revision = this.revision
         const content = await this.harvest()
         if (content && revision === this.revision) await this.persist(content, this.entry?.id)
      },
      async clone() {
         if (this.mutating || !this.entry?.id) return
         if (!confirmEntryNavigation()) return
         const revision = this.revision
         const content = this.isEditing ? await this.harvest() : this.entry.content
         if (content && revision === this.revision) await this.persist(content)
      },
      async persist(content, id) {
         if (this.mutating) return
         this.mutating = true
         this.showStatus('Saving...', 'wait')
         const revision = this.revision
         const action = id ? 'entryupdate' : 'entrycreate'
         const result = await api.post(`${this.dictPath}/${action}.json`, { id, content }).catch(() => null)
         if (revision !== this.revision) return
         this.mutating = false
         if (!result?.success) {
            this.showStatus('Failed to save.', 'warn')
            return
         }
         const surface = this.hasViewer ? 'view' : 'edit'
         this.show(result, surface)
         this.idInput = result.id
         this.requestedKey = this.entryKey(result.id, surface)
         this.$router.push(this.entryRoute(result.id, surface))
         this.showStatus()
         if (result.feedback?.type === 'saveFeedbackHeadwordExists') {
            this.alert = `WARNING: another entry with this headword exists. ID=${result.feedback.info}`
         } else if (result.feedback) {
            this.alert = result.feedback.type || JSON.stringify(result.feedback)
         }
         dictionaryWorkspace.loadEntryList()
      },
      async remove() {
         if (this.mutating || !window.confirm('Careful now! Are you sure?')) return
         const { id } = this.entry
         const revision = this.revision
         this.mutating = true
         this.showStatus('Deleting...', 'wait')
         const result = await api.post(`${this.dictPath}/entrydelete.json`, { id }).catch(() => null)
         if (revision !== this.revision) return
         this.mutating = false
         if (!result?.success) {
            this.showStatus('Failed to delete.', 'warn')
            return
         }
         this.show(null, 'empty')
         this.showStatus()
         dictionaryWorkspace.loadEntryList()
      },
      refreshLinks() {
         this.$refs.entryLinks?.load()
      },
      async toggleSource() {
         if (this.surface === 'source') {
            const source = this.$refs.source.value
            const changed = source !== this.sourceInputValue
            const content = changed ? source : this.source
            if (!parseXml(content)) {
               this.invalidSource = true
               return
            }
            this.show({ ...this.entry, content }, 'edit', this.baseDirty || changed)
            return
         }
         const revision = this.revision
         const content = await this.harvest()
         if (content == null || revision !== this.revision) return
         this.source = content
         this.show(this.entry, 'source', this.dirty)
         this.$nextTick(() => this.$refs.source?.focus())
      },
      async toggleHistory() {
         const id = this.entry?.id || activeDictionary.entryId || this.idInput
         if (!id || !confirmEntryNavigation()) return
         if (this.surface === 'history') {
            this.openEntry(id, 'view')
            return
         }
         this.revisions = []
         this.selectedRevision = null
         this.show(this.entry, 'history')
         this.showStatus('Getting history...', 'wait')
         const revision = this.revision
         const data = await api.post(`${this.dictPath}/history.json`, { id }).catch(() => null)
         if (revision !== this.revision) return
         this.showStatus(data ? 'Ready.' : 'Failed to get history.', data ? '' : 'warn')
         this.revisions = data?.history || []
         const latest = this.revisions[0]
         if (latest && !['delete', 'purge'].includes(latest.action)) this.selectRevision(latest)
      },
      selectRevision(item, pretty = false) {
         this.selectedRevision = item
         this.previewHistory = pretty
         this.revision++
      },
      async reviveRevision(item) {
         const id = item.entry_id
         this.requestedKey = this.entryKey(id, 'edit')
         const failure = await this.$router.push(this.entryRoute(id, 'edit'))
         if (failure && !isNavigationFailure(failure, NavigationFailureType.duplicated)) return
         this.idInput = id
         this.show({ ...item, id }, 'edit', true)
      },
      async followHeadword(event) {
         const link = event.target.closest('a.xref[data-text]')
         if (!link || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return
         event.preventDefault()
         const revision = this.revision
         const results = await searchEntriesFromRoute({ searchtext: link.dataset.text, modifier: 'substring' })
         if (revision !== this.revision) return
         const match = results?.[0]
         if (match) this.openEntry(match.id, 'view')
      }
   }
}
</script>
