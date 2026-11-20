import assert from 'node:assert/strict'
import { test } from 'node:test'

test('the configured API root is independent of the page URL', async t => {
   globalThis.document = {
      baseURI: 'https://lexonomy.example/workspace/#/my-dictionary',
      querySelector: () => ({ content: 'https://lexonomy.example/service/' })
   }
   globalThis.location = { origin: 'https://lexonomy.example', pathname: '/workspace/' }
   t.after(() => {
      delete globalThis.document
      delete globalThis.location
   })
   const { pageUrl } = await import('../js/page-url.ts')
   const { api } = await import('../js/api.ts')
   assert.equal(new URL('#/my-dictionary', pageUrl).href, 'https://lexonomy.example/workspace/#/my-dictionary')
   assert.equal(api.url('login.json').href, 'https://lexonomy.example/service/login.json')
   assert.throws(() => api.url('../login.json'), /relative to Lexonomy/)
})
