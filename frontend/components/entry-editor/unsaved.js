import { ref } from 'vue'

export const unsavedEntry = ref(false)

export function confirmEntryNavigation() {
   return !unsavedEntry.value || window.confirm('You have unsaved changes. Are you sure you want to lose them?')
}
