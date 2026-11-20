type Fields = Record<string, string | number | boolean | null | undefined>

const apiRoot = document.querySelector<HTMLMetaElement>('meta[name="lexonomy-api-root"]')?.content
if (!apiRoot) throw new Error('Missing Lexonomy API root.')
const apiBase = new URL(apiRoot, document.baseURI)

export function dictionaryPath(dictId: string, ...segments: string[]) {
   const parts = [dictId, ...segments]
   if (parts.some(part => !part || part === '.' || part === '..')) throw new Error('Invalid API path segment.')
   return parts.map(encodeURIComponent).join('/')
}

function formFields(values: Fields) {
   const fields = new URLSearchParams()
   for (const [name, value] of Object.entries(values)) {
      if (value != null) fields.set(name, String(value))
   }
   return fields
}

function endpointUrl(path: string, query?: Fields) {
   const url = new URL(path, apiBase)
   if (url.origin !== apiBase.origin || !url.pathname.startsWith(apiBase.pathname)) {
      throw new Error('API paths must be relative to Lexonomy.')
   }
   for (const [key, value] of formFields(query ?? {})) url.searchParams.append(key, value)
   return url
}

async function request(path: string, query?: Fields, body?: URLSearchParams | FormData, signal?: AbortSignal) {
   const url = endpointUrl(path, query)
   const response = await fetch(url, { method: body ? 'POST' : 'GET', body, cache: 'no-store', signal })
   if (!response.ok) throw new Error(`${url.pathname} returned HTTP ${response.status}`)
   return response
}

export const api = {
   url: endpointUrl,
   async get<T = unknown>(path: string, query?: Fields, signal?: AbortSignal): Promise<T> {
      return (await request(path, query, undefined, signal)).json()
   },
   async post<T = unknown>(path: string, data: Fields | FormData = {}, signal?: AbortSignal): Promise<T> {
      return (await request(path, undefined, data instanceof FormData ? data : formFields(data), signal)).json()
   },
   async text(path: string, query?: Fields): Promise<string> {
      return (await request(path, query)).text()
   }
}
