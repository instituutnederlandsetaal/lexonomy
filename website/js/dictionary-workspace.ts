import { computed, reactive, shallowReadonly } from 'vue'
import Materialize from '../libs/materialize/materialize.min.js'
import { api } from './api.ts'
import { session } from './auth.ts'

type Permissions = { canEdit: boolean; canConfig: boolean; canUpload: boolean; canDownload: boolean }
type DictionaryInfo = { title: string; blurb: string; licence: string; public: boolean }
type EntrySummary = { id: number; doctype: string; title: string; titlePlain?: string; flag: string; isSaving?: boolean }
type Flag = { key: string; name: string; label: string; color: string }
type LabelledCode = { code: string; lang: string }

type XemaElement = {
   elementName?: string
   filling?: string
   children?: { name: string; min: number | string; max: number | string | null }[]
   attributes?: Record<string, unknown>
   values?: { value: string; caption: string }[]
}

type DictionarySettings = {
   autonumbering: Record<string, { element: string; target?: string; type?: 'number' | 'string';
      string_template?: string; number_globally?: boolean; number_next?: number;
      overwrite_existing?: boolean; auto_apply?: boolean }>
   download: { xslt?: string }
   editing: { xonomyMode: 'nerd' | 'laic' | 'graphical'; xonomyTextEditor?: string; _css?: string; _js?: string }
   flagging: { flag_element: string; flags: Flag[] }
   ident: { title: string; blurb: string; lang: string; handle: string; langs?: LabelledCode[] }
   links: Record<string, { linkElement: string; identifier: string; preview: string }>
   publico: { public: boolean; licence?: string }
   searchability: { searchableElements?: string[] }
   subbing: Record<string, { attributes?: Record<string, string>; titling?: { headword: string } | null }>
   titling: { numberEntries?: number; headword?: string; headwordSorting?: string; sortDesc?: boolean;
      locale?: string; sort_locale?: string; locales?: LabelledCode[]; headwordAnnotationsType?: 'simple' | 'advanced';
      headwordAnnotations?: string[]; headwordAnnotationsAdvanced?: string }
   users: Record<string, Permissions>
   xema: { root: string; elements: Record<string, XemaElement>; _dtd?: string; _newXml?: string; _xonomyDocSpec?: string }
   xemplate: Record<string, unknown> & { _css?: string; _xsl?: string }
}
type Setting = keyof DictionarySettings
type SettingsResponse<K extends Setting> = { success: true; id: K; content: DictionarySettings[K] } | { success: false }

type WorkspaceConfig = Pick<DictionarySettings, 'xema' | 'xemplate' | 'subbing' | 'titling' | 'flagging' | 'editing'> & {
   linking: DictionarySettings['links']
   metadata: Record<string, string>
}
type DictionaryResponse = { success: false } | {
   success: true
   configs: WorkspaceConfig
   doctypes: string[]
   userAccess: Permissions | false
   publicInfo: Omit<DictionaryInfo, 'licence'> & { licence?: string }
}
type EntryListResponse = { success: false } | { success: true; entries: EntrySummary[]; total: number }

export type EntrySearch = { searchtext: string; searchflag: string; modifier: string }
type DictionaryLocation = {
   dictId: string | null
   doctype?: string | null
   entryId?: number | null
   mode?: 'view' | 'edit'
   filters?: Partial<EntrySearch>
   entryLimit?: number
}
type WorkspaceState = DictionaryInfo & EntrySearch & {
   dictId: string | null
   config: WorkspaceConfig | null
   doctype: string | null
   doctypes: string[]
   entryId: number | null
   mode: 'view' | 'edit'
   userAccess: Permissions | null
   isDictionaryLoading: boolean
   entryList: EntrySummary[] | null
   entryCount: number
   isEntryListLoading: boolean
   currentPage: number
}

const defaultSearch: EntrySearch = { searchtext: '', searchflag: '', modifier: 'start' }

function emptyDictionary(dictId: string | null): WorkspaceState {
   return {
      dictId, config: null, doctype: null, doctypes: [], entryId: null, mode: 'view',
      title: '', blurb: '', licence: '', public: false,
      userAccess: null,
      isDictionaryLoading: false,
      entryList: null, entryCount: 0, isEntryListLoading: false, currentPage: 1,
      ...defaultSearch
   }
}

const workspace = reactive(emptyDictionary(null))
export const activeDictionary = shallowReadonly(workspace)

let dictionaryRequest: Promise<false | undefined> | undefined
let pendingEntries: { key: string; result: Promise<EntrySummary[] | undefined> } | undefined
let entryLimit: number | undefined
export const entryPageSize = computed(() => workspace.config?.titling.numberEntries || 1000)

function loadDictionary(dictId: string) {
   const request = api.get<DictionaryResponse>(`${encodeURIComponent(dictId)}/config.json`)
   const result: Promise<false | undefined> = request.then(response => {
      if (result !== dictionaryRequest) return
      if (!response.success) throw new Error('Dictionary not found')

      const { configs, doctypes, userAccess, publicInfo } = response
      const doctype = workspace.doctype && doctypes.includes(workspace.doctype)
         ? workspace.doctype : configs.xema.root || doctypes[0] || null
      const { title, blurb, licence = '', public: isPublic } = publicInfo
      Object.assign(workspace, { config: configs, doctypes, doctype, userAccess: userAccess || null, title, blurb, licence, public: isPublic })
      void loadEntryList()
      return undefined
   }).catch(() => {
      if (result === dictionaryRequest) {
         Materialize.toast({ html: 'Could not load dictionary.' })
         return false as const
      }
      return undefined
   }).finally(() => {
      if (result === dictionaryRequest) {
         dictionaryRequest = undefined
         workspace.isDictionaryLoading = false
      }
   })
   dictionaryRequest = result
   workspace.isDictionaryLoading = true
   return result
}

function loadEntryList(page = workspace.currentPage, reusePending = false) {
   const { dictId, doctype, searchtext, modifier, searchflag } = workspace
   if (!dictId || !workspace.config || !doctype) return
   const howmany = entryLimit ?? entryPageSize.value
   const endpoint = session.value && workspace.userAccess?.canEdit
      ? `${encodeURIComponent(doctype)}/entrylist.json` : 'search.json'
   const key = JSON.stringify([dictId, endpoint, searchtext, modifier, searchflag, howmany, page])
   if (reusePending && pendingEntries?.key === key) return pendingEntries.result

   const request = api.post<EntryListResponse>(`${encodeURIComponent(dictId)}/${endpoint}`, {
      searchtext, modifier, searchflag, howmany, offset: (page - 1) * howmany
   })
   const result: Promise<EntrySummary[] | undefined> = request.then(response => {
      if (pendingEntries?.result !== result) return
      const entries = response.success ? response.entries : []
      workspace.entryList = entries
      workspace.entryCount = response.success ? response.total : 0
      workspace.currentPage = page
      return entries
   }).catch(() => {
      if (pendingEntries?.result === result) Materialize.toast({ html: 'Entry list could not be loaded.' })
      return undefined
   }).finally(() => {
      if (pendingEntries?.result === result) {
         pendingEntries = undefined
         workspace.isEntryListLoading = false
      }
   })

   pendingEntries = { key, result }
   workspace.isEntryListLoading = true
   return result
}

export const dictionaryWorkspace = {
   async open({ dictId, doctype, entryId = null, mode = 'view', filters, entryLimit: limit }: DictionaryLocation) {
      const limitChanged = limit !== entryLimit
      entryLimit = limit
      const opening = dictId !== workspace.dictId
      if (opening) {
         dictionaryRequest = pendingEntries = undefined
         Object.assign(workspace, emptyDictionary(dictId))
      }
      if (!dictId) return

      const nextType = workspace.config && (!doctype || !workspace.doctypes.includes(doctype))
         ? workspace.config.xema.root || workspace.doctypes[0] || null : doctype || null
      const typeChanged = nextType !== workspace.doctype
      if (typeChanged) {
         workspace.doctype = nextType
         workspace.entryList = null
         workspace.entryCount = 0
      }
      workspace.mode = mode
      workspace.entryId = entryId

      const searchable = { ...defaultSearch, ...filters }
      const searchChanged = searchable.searchtext !== workspace.searchtext || searchable.modifier !== workspace.modifier ||
         searchable.searchflag !== workspace.searchflag
      if (searchChanged) Object.assign(workspace, searchable)
      if (!workspace.config) return dictionaryRequest ?? loadDictionary(dictId)
      if (typeChanged || searchChanged || limitChanged) void loadEntryList(1)
   },

   searchEntries(filters: EntrySearch) {
      Object.assign(workspace, filters)
      return loadEntryList(1, true)
   },

   loadEntryList,

   nextPage() {
      if (workspace.currentPage < Math.ceil(workspace.entryCount / entryPageSize.value)) {
         void loadEntryList(workspace.currentPage + 1)
      }
   },

   previousPage() {
      if (workspace.currentPage > 1) {
         void loadEntryList(workspace.currentPage - 1)
      }
   },

   async setEntryFlag(id: number, flag: string) {
      const { dictId } = workspace
      const entry = workspace.entryList?.find(item => item.id === id)
      if (!dictId || !entry || entry.isSaving) return
      entry.isSaving = true
      try {
         const { success } = await api.post<{ success: boolean }>(`${encodeURIComponent(dictId)}/entryflag.json`, { id, flag })
         if (!success) throw new Error('Flag rejected')
         entry.flag = flag
      } catch {
         Materialize.toast({ html: 'Flag was not saved.' })
      } finally {
         delete entry.isSaving
      }
   },

   async loadDictionaryConfig<K extends Setting>(id: K) {
      const { dictId } = workspace
      if (!dictId) return
      try {
         const response = await api.post<SettingsResponse<K>>(`${encodeURIComponent(dictId)}/configread.json`, { id })
         if (response.success) return response
         throw new Error('Settings request rejected')
      } catch {
         Materialize.toast({ html: `Could not load ${id} settings.` })
      }
   },

   async updateDictionaryConfig<K extends Setting>(id: K, data: DictionarySettings[K]) {
      const { dictId } = workspace
      if (!dictId) return
      try {
         const response = await api.post<SettingsResponse<K>>(`${encodeURIComponent(dictId)}/configupdate.json`, {
            id, content: JSON.stringify(data)
         })
         if (!response.success) throw new Error('Settings update rejected')
         Materialize.toast({ html: 'Saved' })
         if (workspace.dictId === dictId) await loadDictionary(dictId)
         return response
      } catch {
         Materialize.toast({ html: `Could not save ${id} settings.` })
      }
   }
}
