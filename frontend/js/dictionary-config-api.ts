import { api, dictionaryPath } from './api.ts'
import type { Xema } from './xema.ts'
import type { Xemplate } from './xemplate.ts'

export type DictionaryPermissions = { canEdit: boolean; canConfig: boolean; canUpload: boolean; canDownload: boolean }
export type Flag = { key: string; name: string; label: string; color: string }
type LabelledCode = { code: string; lang: string }

export type DictionarySettings = {
   autonumbering: Record<string, { element: string; target?: string; type?: 'number' | 'string';
      string_template?: string; number_globally?: boolean; number_next?: number;
      overwrite_existing?: boolean; auto_apply?: boolean }>
   download: { xslt?: string }
   editing: { xonomyMode: 'nerd' | 'laic' | 'graphical'; xonomyTextEditor?: string;
      editorApiVersion?: 1 | null; _css?: string; _js?: string }
   flagging: { flag_element: string; flags: Flag[] }
   ident: { title: string; blurb: string; lang: string; handle: string; langs?: LabelledCode[] }
   links: Record<string, { linkElement: string; identifier: string; preview: string }>
   publico: { public: boolean; licence?: string }
   searchability: { searchableElements?: string[] }
   subbing: Record<string, { attributes?: Record<string, string>; titling?: { headword: string } | null }>
   titling: { numberEntries?: number; headword?: string; headwordSorting?: string; sortDesc?: boolean;
      locale?: string; sort_locale?: string; locales?: LabelledCode[]; headwordAnnotationsType?: 'simple' | 'advanced';
      headwordAnnotations?: string[]; headwordAnnotationsAdvanced?: string }
   users: Record<string, DictionaryPermissions>
   xema: Xema
   xemplate: Xemplate
}
type Setting = keyof DictionarySettings
type SettingsResponse<K extends Setting> = { success: true; id: K; content: DictionarySettings[K] } | { success: false }
const pendingWrites = new Map<string, Promise<void>>()

function settingKey(dictId: string, id: Setting) {
   return JSON.stringify([dictId, id])
}

export async function readDictionarySetting<K extends Setting>(dictId: string, id: K) {
   // A settings page can close and reopen before its save finishes.
   const pending = pendingWrites.get(settingKey(dictId, id))
   if (pending) await pending.catch(() => {})
   const response = await api.post<SettingsResponse<K>>(dictionaryPath(dictId, 'configread.json'), { id })
   if (!response.success) throw new Error('Settings request rejected')
   return response.content
}

export async function writeDictionarySetting<K extends Setting>(dictId: string, id: K, data: DictionarySettings[K]) {
   const key = settingKey(dictId, id)
   const content = JSON.stringify(data)
   const send = async () => {
      const response = await api.post<SettingsResponse<K>>(dictionaryPath(dictId, 'configupdate.json'), { id, content })
      if (!response.success) throw new Error('Settings update rejected')
   }
   const previous = pendingWrites.get(key)
   const request = previous ? previous.then(send, send) : send()
   pendingWrites.set(key, request)
   try {
      await request
   } finally {
      if (pendingWrites.get(key) === request) pendingWrites.delete(key)
   }
}

export function fetchDictionaryStats(dictId: string) {
   return api.get<{ needUpdate?: number }>(dictionaryPath(dictId, 'stats.json'))
}

export async function reindexDictionaryBatch(dictId: string) {
   const result = await api.post<{ todo: number; finished: boolean; progressMessage: string }>(dictionaryPath(dictId, 'resave.json'))
   if (typeof result.finished !== 'boolean' || !Number.isInteger(result.todo) || result.todo < 0) {
      throw new Error('Re-indexing request rejected')
   }
   return result
}

export function moveDictionary(dictId: string, url: string) {
   return api.post<{ success: boolean }>(dictionaryPath(dictId, 'move.json'), { url })
}

export async function fetchPreviewEntry(dictId: string) {
   const result = await api.post<{ id: number; xml: string }>(dictionaryPath(dictId, 'randomone.json'))
   if (!('id' in result)) throw new Error('Entry preview request rejected')
   return result
}

export function applyAutonumbering(dictId: string) {
   return api.post<{ success: boolean; processed?: number }>(dictionaryPath(dictId, 'autonumber.json'))
}

export async function findNextNumber(dictId: string, element: string, target?: string) {
   const result = await api.post<{ next?: number | null }>(dictionaryPath(dictId, 'next_autonumber.json'), { element, target })
   if (!('next' in result)) throw new Error('Next number request rejected')
   return result.next
}
