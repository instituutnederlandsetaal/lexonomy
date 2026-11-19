import { ref, shallowRef, watch } from 'vue'
import Materialize from '../libs/materialize/materialize.min.js'
import { readDictionarySetting, writeDictionarySetting, type DictionarySettings } from './dictionary-config-api.ts'
import { dictionaryWorkspace } from './dictionary-workspace.ts'

export function useDictionaryScope(dictId: () => string) {
   const scope = shallowRef({ dictId: dictId(), active: true })
   watch(dictId, (id, _, onCleanup) => {
      const current = { dictId: id, active: true }
      scope.value = current
      onCleanup(() => { current.active = false })
   }, { immediate: true, flush: 'sync' })
   return scope
}

export function useDictionarySetting<K extends keyof DictionarySettings>(
   dictId: () => string,
   setting: K,
   onLoad: (content: DictionarySettings[K]) => void
) {
   const scope = useDictionaryScope(dictId)
   const loading = ref(true)
   const ready = ref(false)
   const saving = ref(false)
   let latestLoad = 0

   async function load() {
      const current = scope.value
      const request = ++latestLoad
      const isCurrent = () => current.active && request === latestLoad
      loading.value = true
      ready.value = false
      try {
         const content = await readDictionarySetting(current.dictId, setting)
         if (isCurrent()) {
            onLoad(content)
            ready.value = true
         }
      } catch {
         if (isCurrent()) Materialize.toast({ html: `Could not load ${setting} settings.` })
      } finally {
         if (isCurrent()) loading.value = false
      }
   }

   async function save(content: DictionarySettings[K]) {
      const current = scope.value
      const id = current.dictId
      if (!current.active || !ready.value || saving.value) return false
      saving.value = true
      try {
         await writeDictionarySetting(id, setting, content)
         if (current.active) Materialize.toast({ html: 'Saved' })
         await dictionaryWorkspace.refresh(id)
         return true
      } catch {
         if (current.active) Materialize.toast({ html: `Could not save ${setting} settings.` })
         return false
      } finally {
         if (current.active) saving.value = false
      }
   }

   watch(scope, () => {
      saving.value = false
      void load()
   }, { immediate: true, flush: 'sync' })
   return { scope, loading, ready, saving, load, save }
}
