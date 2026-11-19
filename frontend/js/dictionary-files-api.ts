import { api, dictionaryPath } from './api.ts'

type Upload = { filename: string; uploadStart: string }
type UploadResponse = { success: false } | { success: true; file: string; uploadStart: string }
type ImportStatus = { progressMessage: string; finished: boolean; errors: boolean }

export function dictionaryDownloadUrl(dictId: string, clean: boolean) {
   return api.url(dictionaryPath(dictId, 'download.xml'), { clean: clean || undefined }).href
}

export async function startDictionaryUpload(dictId: string, file: File, purge: boolean): Promise<Upload> {
   const form = new FormData()
   form.append('myfile', file)
   if (purge) form.append('purge', 'on')
   const result = await api.post<UploadResponse>(dictionaryPath(dictId, 'upload.html'), form)
   if (!result.success || !result.file) throw new Error('Upload rejected')
   return { filename: result.file, uploadStart: result.uploadStart }
}

export async function fetchImportStatus(dictId: string, upload: Upload) {
   const response = await api.get<ImportStatus | { success: false }>(dictionaryPath(dictId, 'import.json'), upload)
   if (!('progressMessage' in response)) throw new Error('Could not read import status')
   return response
}

export async function fetchImportErrors(dictId: string, upload: Upload) {
   const { errorData } = await api.get<{ errorData: string }>(dictionaryPath(dictId, 'import.json'), {
      ...upload, showErrors: true, truncate: 10000
   })
   return errorData.replaceAll('&lt;', '<')
}
