import { api, dictionaryPath } from './api.ts'
import type { DictionaryLink as EntryLink } from './linked-entry-location.ts'

export type { DictionaryLink as EntryLink } from './linked-entry-location.ts'

export type EntryRendering = { contentHtml?: string; resolvedXml?: string }
export type RelatedEntry = { id: number; title: string; doctype: string; sortkey?: string }
export type EditorEntry = EntryRendering & {
   schemaId?: string
   id: number
   content: string
   doctype?: string
   subentries?: RelatedEntry[]
   parententries?: RelatedEntry[]
}
export type EntryDraft = Omit<EditorEntry, 'id'> & { id?: number }
type LoadedEntry = EditorEntry & RelatedEntry
export type EntryRevision = EntryRendering & {
   schemaId?: string
   entry_id: number
   revision_id: number
   content: string
   action: 'create' | 'update' | 'delete' | 'purge' | 'autonumber'
   when: string
   email: string
   historiography: { uploadStart?: string; viaApi?: boolean; refactoredFrom?: number }
}
type Failure = { success: false }
type SavedEntry = EditorEntry & { success: true; feedback?: { type: string; info?: string | number } | null }

export type LinkTarget = { element: string; link: string; entry: number; preview: string | null }
type LinkDetails = Pick<EntryLink, 'source_el' | 'source_id' | 'target_dict' | 'target_el' | 'target_id'>
export type EntryLinks = { in: EntryLink[]; out: EntryLink[] }

export const entryEditorApi = {
   read(dictId: string, id: number) {
      return api.post<(LoadedEntry & { success: true }) | Failure>(dictionaryPath(dictId, 'entryread.json'), { id })
   },
   save(dictId: string, content: string, id?: number) {
      return api.post<SavedEntry | Failure>(dictionaryPath(dictId, id ? 'entryupdate.json' : 'entrycreate.json'), { id, content })
   },
   remove(dictId: string, id: number) {
      return api.post<{ success: boolean }>(dictionaryPath(dictId, 'entrydelete.json'), { id })
   },
   history(dictId: string, id: number) {
      return api.post<{ history: EntryRevision[] }>(dictionaryPath(dictId, 'history.json'), { id })
   },
   subentries(dictId: string, lemma: string, doctype: string, schemaId?: string) {
      return api.get<{ success: true; total: number; entries: RelatedEntry[] } | Failure>(
         dictionaryPath(dictId, 'subget'), { lemma, doctype, schemaId }
      )
   },
   links(dictId: string, id: number) {
      return api.get<{ links: EntryLinks }>(dictionaryPath(dictId, 'entrylinks.json'), { id })
   },
   linkTargets(dictId: string) {
      return api.get<{ links: LinkTarget[] }>(dictionaryPath(dictId, 'linkablelist.json'))
   },
   addLink(dictId: string, details: LinkDetails) {
      return api.get<{ success: boolean; error?: string }>(dictionaryPath(dictId, 'links', 'add'), details)
   },
   removeLink(dictId: string, id: number) {
      return api.get<{ success: boolean }>(dictionaryPath(dictId, 'links', 'delete', String(id)))
   }
}
