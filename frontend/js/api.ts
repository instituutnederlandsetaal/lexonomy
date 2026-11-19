type Fields = Record<string, string | number | boolean | null | undefined>

const base = new URL('.', document.baseURI)
export const basePath = base.pathname

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
   const url = new URL(path, base)
   if (url.origin !== base.origin || !url.pathname.startsWith(basePath)) {
      throw new Error('API paths must be relative to Lexonomy.')
   }
   for (const [key, value] of formFields(query ?? {})) url.searchParams.append(key, value)
   return url
}

async function request(path: string, query?: Fields, body?: URLSearchParams | FormData) {
   const url = endpointUrl(path, query)
   const response = await fetch(url, { method: body ? 'POST' : 'GET', body, cache: 'no-store' })
   if (!response.ok) throw new Error(`${url.pathname} returned HTTP ${response.status}`)
   return response
}

export const api = {
   url: endpointUrl,
   async get<T = unknown>(path: string, query?: Fields): Promise<T> {
      return (await request(path, query)).json()
   },
   async post<T = unknown>(path: string, data: Fields | FormData = {}): Promise<T> {
      return (await request(path, undefined, data instanceof FormData ? data : formFields(data))).json()
   },
   async text(path: string, query?: Fields): Promise<string> {
      return (await request(path, query)).text()
   }
}
