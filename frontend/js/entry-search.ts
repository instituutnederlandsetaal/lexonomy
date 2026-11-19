import { isNavigationFailure, NavigationFailureType } from 'vue-router'
import { activeDictionary, dictionaryWorkspace, type EntrySearch } from './dictionary-workspace.ts'
import { router } from './router.ts'

let latestSearch = 0

export async function searchEntriesFromRoute(changes: Partial<EntrySearch>) {
   const { name, params } = router.currentRoute.value
   if (!name) return
   const { searchtext, searchflag, modifier } = { ...activeDictionary, ...changes }
   const query = searchtext || searchflag || modifier !== 'start' || name === 'dictionary'
      ? { s: searchtext, f: searchflag, m: modifier } : {}
   const location = { name, params, query }
   const { fullPath } = router.resolve(location)
   const search = ++latestSearch
   const failure = await router.push(location)
   if (failure && !isNavigationFailure(failure, NavigationFailureType.duplicated)) return
   const appliedRoute = router.currentRoute.value
   if (search !== latestSearch || fullPath !== appliedRoute.fullPath) return

   const entries = await dictionaryWorkspace.searchEntries({ searchtext, searchflag, modifier })
   if (search === latestSearch && appliedRoute === router.currentRoute.value) return entries
}
