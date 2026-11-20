import assert from 'node:assert/strict'
import { test } from 'node:test'

globalThis.document = {
   baseURI: 'https://lexonomy.example/workspace/',
   querySelector: () => ({ content: '/workspace/' })
}
const { compileEditorExtension, createEditorExtensionServices, loadEditorExtension, subentryReferenceXml } =
   await import('../js/editor-extension.ts')
delete globalThis.document

test('editor extension validation compiles without executing configured JavaScript', () => {
   assert.doesNotThrow(() => compileEditorExtension('(() => { throw new Error("executed") })()'))
   assert.throws(() => compileEditorExtension('{ mount( }'), SyntaxError)
   assert.throws(() => loadEditorExtension('{}'), /must provide mount/)
   assert.throws(() => loadEditorExtension('{ mount() {}, initialXml: "entry" }'), /initialXml property/)

   const extension = loadEditorExtension(`// A stored editor extension
      {
         mount({ entry }) { return { harvest() { return entry.content } } }
      } // end of extension`)
   assert.equal(extension.mount({ entry: { content: '<entry/>' } }).harvest(), '<entry/>')
})

test('subentry references carry their namespace and escape each XML attribute', () => {
   assert.equal(subentryReferenceXml({ id: 23, doctype: 'example', title: `a < b & c "'\n` }),
      '<lxnm:subentryParent xmlns:lxnm="http://www.lexonomy.eu/" id="23" doctype="example" title="a &lt; b &amp; c &quot;&apos;&#10;"/>')
})

test('extension entry services scope requests to the active dictionary and schema definition', async t => {
   const schema = { root: 'entry', elements: { 'example-id': { elementName: 'example' } } }
   const relatedEntry = { id: 23, doctype: 'example', title: 'Example' }
   const loadedEntry = { ...relatedEntry, content: '<example/>', parententries: [] }
   const controller = new AbortController()
   const fetch = t.mock.method(globalThis, 'fetch', async (url, { body, signal }) => {
      assert.equal(signal, controller.signal)
      assert.match(url.pathname, /^\/workspace\/my%20dictionary\//)
      signal.throwIfAborted()
      if (url.pathname.endsWith('/subget')) {
         assert.equal(url.searchParams.get('doctype'), 'example')
         if (url.searchParams.get('lemma') === 'blocked') return Response.json({ success: false })
         assert.equal(url.searchParams.get('schemaId'), 'example-id')
         assert.equal(url.searchParams.get('lemma'), 'test')
         return Response.json({ success: true, entries: [relatedEntry] })
      }
      assert.match(url.pathname, /\/entryread\.json$/)
      return Response.json(body.get('id') === '23' ? { ...loadedEntry, success: true } : { success: false })
   })
   const definitions = { 'example-id': { attributes: { type: 'example' } } }
   const { subentries, readEntry, createInitialElement } = createEditorExtensionServices(
      'my dictionary', schema, definitions, controller.signal
   )

   assert.deepEqual(subentries.definitions, definitions)
   assert.equal(createInitialElement('example-id'), '<example></example>')
   assert.throws(() => createInitialElement('missing'), /Unknown schema element/)
   assert.deepEqual(await subentries.search(' ', 'example-id'), [])
   await assert.rejects(subentries.search('test', 'missing'), /Unknown schema element/)
   assert.equal(fetch.mock.callCount(), 0)
   assert.deepEqual(await subentries.search(' test ', 'example-id'), [relatedEntry])
   await assert.rejects(subentries.search('blocked', 'example-id'), /Subentry search rejected/)
   assert.deepEqual((await readEntry(23)).parententries, [])
   assert.equal(await readEntry(99), null)
   controller.abort()
   await assert.rejects(readEntry(23), { name: 'AbortError' })
   await assert.rejects(subentries.search('test', 'example-id'), { name: 'AbortError' })
})
