import type { RouteLocationRaw } from 'vue-router'

type Side = 'source' | 'target'
type LinkEndpoints = Record<`${Side}_${'dict' | 'entry' | 'id'}`, string>
   & Partial<Record<`${Side}_doctype`, string>>

export function linkedEntryLocation(link: LinkEndpoints, side: Side): RouteLocationRaw {
   const dictId = link[`${side}_dict`]
   const entryId = link[`${side}_entry`]
   if (!/^\d+$/.test(entryId)) return { name: 'dictionary', params: { dictId } }

   return {
      name: 'edit',
      params: { dictId, doctype: link[`${side}_doctype`] || 'entry', entryId, mode: 'view' },
      query: { link: link[`${side}_id`] }
   }
}
