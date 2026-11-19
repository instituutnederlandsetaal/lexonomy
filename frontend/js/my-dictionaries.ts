import { reactive, shallowReadonly } from 'vue'
import Materialize from '../libs/materialize/materialize.min.js'
import { api, dictionaryPath } from './api.ts'
import { session } from './auth.ts'

export type MyDictionary = {
   id: string; title: string; hasLinks: boolean; lang: string; favorite?: boolean
   currentUserCanEdit?: boolean; currentUserCanDelete?: boolean; size?: number; broken?: boolean
}
type DictionaryList = { dicts: MyDictionary[] }
type DictionaryMutation = DictionaryList & { success: boolean }

const library = reactive({ items: [] as MyDictionary[], loading: false, failed: false })
export const myDictionaries = shallowReadonly(library)
let listRequest: Promise<DictionaryList> | undefined

function replaceList(items: MyDictionary[]) {
   listRequest = undefined
   library.items = items
   library.loading = false
   library.failed = false
}

export function clearMyDictionaries() {
   replaceList([])
}

export async function loadMyDictionaries() {
   const email = session.value?.email
   if (!email) return
   const request = api.get<DictionaryList>('userdicts.json')
   listRequest = request
   library.loading = true
   library.failed = false
   try {
      const { dicts } = await request
      if (request === listRequest && email === session.value?.email) library.items = dicts
   } catch {
      if (request === listRequest && email === session.value?.email) library.failed = true
   } finally {
      if (request === listRequest) library.loading = false
   }
}

export async function cloneDictionary(dictId: string) {
   const email = session.value?.email
   try {
      const { success, dicts, dictID } = await api.post<DictionaryMutation & { dictID?: string }>(dictionaryPath(dictId, 'clone.json'))
      if (!success || !dictID) throw new Error('Clone rejected')
      if (email !== session.value?.email) return
      replaceList(dicts)
      Materialize.toast({ html: 'Dictionary was cloned.' })
      return dictID
   } catch {
      Materialize.toast({ html: 'Dictionary clone creation failed.' })
   }
}

export async function deleteDictionary(dictId: string) {
   const email = session.value?.email
   try {
      const { success, dicts } = await api.post<DictionaryMutation>(dictionaryPath(dictId, 'destroy.json'))
      if (!success) throw new Error('Deletion rejected')
      if (email !== session.value?.email) return
      replaceList(dicts)
      Materialize.toast({ html: 'Dictionary was deleted.' })
   } catch {
      Materialize.toast({ html: 'Dictionary could not be deleted.' })
   }
}
