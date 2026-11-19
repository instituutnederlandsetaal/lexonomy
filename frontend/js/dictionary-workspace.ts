import { computed, reactive, ref, shallowReadonly } from 'vue'
import Materialize from '../libs/materialize/materialize.min.js'
import { api, dictionaryPath } from './api.ts'
import { session } from './auth.ts'
import { xmlElementName } from './xema.ts'
import type { DictionaryPermissions, DictionarySettings } from './dictionary-config-api.ts'

type DictionaryInfo = { title: string; blurb: string; licence: string; public: boolean }
type EntrySummary = { id: number; doctype: string; title: string; titlePlain?: string; flag: string; isSaving?: boolean }
export type EntrySearch = { searchtext: string; searchflag: string; modifier: string }
export type WorkspaceConfig = Pick<DictionarySettings, 'xema' | 'xemplate' | 'subbing' | 'titling' | 'flagging' | 'editing'> & {
   linking: DictionarySettings['links']
   metadata: Record<string, string>
}
type DictionaryResponse = { success: false } | {
   success: true
   configs: WorkspaceConfig
   doctypes: string[]
   userAccess: DictionaryPermissions | false
   publicInfo: Omit<DictionaryInfo, 'licence'> & { licence?: string }
}

async function fetchDictionary(dictId: string) {
   return api.get<DictionaryResponse>(dictionaryPath(dictId, 'config.json'))
}
type EntryListResponse = { success: false } | { success: true; entries: EntrySummary[]; total: number }

type DictionaryLocation = {
   dictId: string | null
   doctype?: string | null
   entryId?: number | null
   mode?: 'view' | 'edit'
   filters?: EntrySearch
   entryLimit?: number
}
type WorkspaceState = DictionaryInfo & {
   dictId: string | null
   config: WorkspaceConfig | null
   doctype: string | null
   doctypes: string[]
   entryId: number | null
   mode: 'view' | 'edit'
   userAccess: DictionaryPermissions | null
   isDictionaryLoading: boolean
   entryList: EntrySummary[] | null
   entryCount: number
   isEntryListLoading: boolean
   currentPage: number
}

const defaultSearch: EntrySearch = { searchtext: '', searchflag: '', modifier: 'start' }

export function sameEntrySearch(a: EntrySearch, b: EntrySearch) {
   return a.searchtext === b.searchtext && a.searchflag === b.searchflag && a.modifier === b.modifier
}

function emptyDictionary(dictId: string | null): WorkspaceState {
   return {
      dictId, config: null, doctype: null, doctypes: [], entryId: null, mode: 'view',
      title: '', blurb: '', licence: '', public: false,
      userAccess: null,
      isDictionaryLoading: false,
      entryList: null, entryCount: 0, isEntryListLoading: false, currentPage: 1
   }
}

const workspace = reactive(emptyDictionary(null))
export const activeDictionary = shallowReadonly(workspace)

let dictionaryRequest: Promise<false | undefined> | undefined
let pendingEntries: { page: number; result: Promise<EntrySummary[] | undefined> } | undefined
let activeSearch = defaultSearch
const entryLimit = ref<number>()
const pendingFlagSaves = new Map<string, Promise<void>>()

function flagSaveKey(dictId: string, id: number) {
   return JSON.stringify([dictId, id])
}
export const entryPageSize = computed(() => {
   const size = Number(entryLimit.value ?? workspace.config?.titling.numberEntries)
   return Number.isSafeInteger(size) && size > 0 ? size : 1000
})

function loadDictionary(dictId: string) {
   const request = fetchDictionary(dictId)
   const result: Promise<false | undefined> = request.then(response => {
      if (result !== dictionaryRequest) return
      if (!response.success) throw new Error('Dictionary not found')

      const { configs, userAccess, publicInfo } = response
      const rootTag = xmlElementName(configs.xema, configs.xema.root)
      const doctypes = [...new Set([rootTag, ...response.doctypes.filter(type => type !== configs.xema.root)])].filter(Boolean)
      const doctype = workspace.doctype && doctypes.includes(workspace.doctype)
         ? workspace.doctype : doctypes[0] ?? null
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

function loadEntryList(page = workspace.currentPage): Promise<EntrySummary[] | undefined> | undefined {
   const { dictId, doctype } = workspace
   if (!dictId || !workspace.config || !doctype) return
   const howmany = entryPageSize.value
   const endpoint = session.value && workspace.userAccess?.canEdit
      ? dictionaryPath(dictId, doctype, 'entrylist.json') : dictionaryPath(dictId, 'search.json')
   const request = api.post<EntryListResponse>(endpoint, {
      ...activeSearch, howmany, offset: (page - 1) * howmany
   })
   const result: Promise<EntrySummary[] | undefined> = request.then(response => {
      if (pendingEntries?.result !== result) return
      if (!response.success) throw new Error('Entry list request rejected')
      const { entries, total } = response
      const lastPage = Math.max(1, Math.ceil(total / howmany))
      if (page > lastPage) return loadEntryList(lastPage)
      for (const entry of entries) {
         if (pendingFlagSaves.has(flagSaveKey(dictId, entry.id))) entry.isSaving = true
      }
      workspace.entryList = entries
      workspace.entryCount = total
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

   pendingEntries = { page, result }
   workspace.isEntryListLoading = true
   return result
}

export const dictionaryWorkspace = {
   async open({ dictId, doctype, entryId = null, mode = 'view', filters = defaultSearch, entryLimit: limit }: DictionaryLocation) {
      const limitChanged = limit !== entryLimit.value
      entryLimit.value = limit
      const opening = dictId !== workspace.dictId
      if (opening) {
         dictionaryRequest = pendingEntries = undefined
         Object.assign(workspace, emptyDictionary(dictId))
      }
      if (!dictId) return

      const nextType = workspace.config && (!doctype || !workspace.doctypes.includes(doctype))
         ? workspace.doctypes[0] ?? null : doctype || null
      const typeChanged = nextType !== workspace.doctype
      workspace.doctype = nextType
      workspace.mode = mode
      workspace.entryId = entryId

      const searchChanged = !sameEntrySearch(filters, activeSearch)
      activeSearch = filters
      if (!workspace.config) return dictionaryRequest ?? loadDictionary(dictId)
      if (typeChanged || searchChanged || limitChanged) {
         workspace.entryList = null
         workspace.entryCount = 0
         workspace.currentPage = 1
         void loadEntryList()
      }
   },

   searchResults() {
      return pendingEntries ? pendingEntries.result : workspace.entryList
   },

   repeatSearch() {
      if (pendingEntries?.page === 1) return pendingEntries.result
      return loadEntryList(1)
   },

   refreshEntries(dictId: string) {
      if (workspace.dictId === dictId) return loadEntryList()
   },

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

   pendingFlagSave(dictId: string, id: number) {
      return pendingFlagSaves.get(flagSaveKey(dictId, id))
   },

   setEntryFlag(id: number, flag: string) {
      const { dictId } = workspace
      const entry = workspace.entryList?.find(item => item.id === id)
      if (!dictId || !entry) return
      const key = flagSaveKey(dictId, id)
      if (pendingFlagSaves.has(key)) return
      entry.isSaving = true
      const currentEntry = () => workspace.dictId === dictId ? workspace.entryList?.find(item => item.id === id) : undefined
      const request = api.post<{ success: boolean }>(dictionaryPath(dictId, 'entryflag.json'), { id, flag })
         .then(({ success }) => {
            if (!success) throw new Error('Flag rejected')
            const current = currentEntry()
            if (current) current.flag = flag
            if (workspace.dictId === dictId && (activeSearch.searchflag || pendingEntries)) {
               void loadEntryList(pendingEntries?.page)
            }
         }).catch(() => {
            if (workspace.dictId === dictId) Materialize.toast({ html: 'Flag was not saved.' })
         }).finally(() => {
            pendingFlagSaves.delete(key)
            delete entry.isSaving
            const current = currentEntry()
            if (current) delete current.isSaving
         })
      pendingFlagSaves.set(key, request)
      return request
   },

   refresh(dictId: string) {
      if (workspace.dictId === dictId) return loadDictionary(dictId)
   }
}
