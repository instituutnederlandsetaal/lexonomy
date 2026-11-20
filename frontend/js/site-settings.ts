import { shallowRef } from 'vue'
import { api } from './api.ts'

type SiteSettings = {
   setupRequired?: boolean
   consent?: { terms: string | null; confirm: string | null }
   licences: Record<string, { title: string; url: string; icon: string; canDownloadXml: boolean }>
}

export const siteSettings = shallowRef<SiteSettings | null>(null)

export async function loadSiteSettings() {
   siteSettings.value = await api.get<SiteSettings>('siteconfigread.json')
}
