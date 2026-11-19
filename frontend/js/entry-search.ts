import { isNavigationFailure, NavigationFailureType } from 'vue-router'
import { dictionaryWorkspace, sameEntrySearch, type EntrySearch } from './dictionary-workspace.ts'
import { readEntrySearch, router } from './router.ts'

export function crossReferenceHref(text: string) {
   const { name, params } = router.currentRoute.value
   return router.resolve({ name, params, query: { s: text, m: 'substring' } }).href
}

export async function searchEntriesFromRoute(changes: Partial<EntrySearch>) {
   const { name, params, query: currentQuery } = router.currentRoute.value
   if (!name) return
   const current = readEntrySearch(currentQuery)
   const { searchtext = current.searchtext, searchflag = current.searchflag, modifier = current.modifier } = changes
   const repeating = sameEntrySearch({ searchtext, searchflag, modifier }, current)
   const query = searchtext || searchflag || modifier !== 'start' || name === 'dictionary'
      ? { s: searchtext, f: searchflag, m: modifier } : {}
   const location = { name, params, query }
   const { fullPath } = router.resolve(location)
   const failure = await router.push(location)
   if (failure && !isNavigationFailure(failure, NavigationFailureType.duplicated)) return
   const appliedRoute = router.currentRoute.value
   if (fullPath !== appliedRoute.fullPath) return

   const entries = await (repeating ? dictionaryWorkspace.repeatSearch() : dictionaryWorkspace.searchResults())
   if (appliedRoute === router.currentRoute.value) return entries
}
