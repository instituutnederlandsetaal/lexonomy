import { api, dictionaryPath } from './api.ts'
import type { DictionaryLink } from './linked-entry-location.ts'

type DictionaryLinks = { from: DictionaryLink[]; to: DictionaryLink[] }
type DictionarySummary = { title: string; blurb: string; isExternal: boolean }
export type LinkedDictionary = DictionarySummary & DictionaryLinks & { dictId: string }

export async function fetchDictionaryLinks(dictId: string) {
   const response = await api.get<{
      links: DictionaryLinks
      dictionaries?: Record<string, DictionarySummary>
   } | { success: false }>(dictionaryPath(dictId, 'links.json'))
   if (!('links' in response)) throw new Error('Could not load dictionary links')

   const grouped = new Map<string, LinkedDictionary>()
   for (const direction of ['to', 'from'] as const) {
      for (const link of response.links[direction]) {
         const id = direction === 'from' ? link.source_dict : link.target_dict
         let group = grouped.get(id)
         if (!group) {
            const summary = response.dictionaries?.[id] ??
               { title: id, blurb: '', isExternal: id === 'BABELNET' || id === 'CILI' }
            group = { dictId: id, ...summary, from: [], to: [] }
            grouped.set(id, group)
         }
         group[direction].push(link)
      }
   }
   if (response.dictionaries) return [...grouped.values()]

   // Older remote backends return link rows without dictionary summaries.
   return Promise.all(Array.from(grouped.values(), async group => {
      if (group.isExternal) return group
      const config = await api.get<{ publicInfo?: Pick<DictionarySummary, 'title' | 'blurb'> }>(
         dictionaryPath(group.dictId, 'config.json')
      ).catch(() => undefined)
      const summary = config?.publicInfo
      return summary ? { ...group, title: summary.title, blurb: summary.blurb } : group
   }))
}
