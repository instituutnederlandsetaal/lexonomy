import { api, dictionaryPath } from './api.ts'

type Example = { id: number; titlePlain: string }
export type Examples = { entries: Example[]; more: boolean }

export type PublicDictionary = {
   id: string
   title: string
   size: number
   lang: string | null
   licence: string
   isAdmin?: boolean
}

export async function fetchExamples(dictId: string) {
   return api.post<Examples>(dictionaryPath(dictId, 'random.json'))
}

export async function fetchPublicDictionaries() {
   const { entries } = await api.get<{ entries: PublicDictionary[] }>('publicdicts.json')
   return entries
}

export function fetchDictionaryUrlSuggestion() {
   return api.get<{ suggested: string; baseUrl: string }>('makesuggest.json')
}

export type DictionaryTemplate = 'blank' | 'smd' | 'sbd'

export function createDictionary(fields: { url: string; template: DictionaryTemplate; title: string }) {
   return api.post<{ success: boolean; url: string }>('make.json', fields)
}
