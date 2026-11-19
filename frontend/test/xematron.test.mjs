import assert from 'node:assert/strict'
import { test } from 'node:test'
import { createDocSpec, createInitialElement, createInitialXml } from '../widgets/xematron.ts'
import { maximumChildCount } from '../js/xema.ts'

test('starter XML uses tag names and required children without altering stored settings', () => {
   const schema = {
      root: 'primary',
      elements: {
         primary: {
            elementName: 'entry',
            filling: 'chd',
            children: [{ name: 'form.primary', min: '2', max: null }],
            attributes: { id: { filling: 'txt', optionality: 'obligatory' } }
         },
         'form.primary': { elementName: 'form', filling: 'txt' }
      }
   }
   const before = structuredClone(schema)
   assert.equal(createInitialXml(schema), "<entry id=''><form></form><form></form></entry>")
   assert.deepEqual(schema, before)
})

test('a required recursive child produces a finite starter', () => {
   const schema = {
      root: 'subentry',
      elements: {
         subentry: { filling: 'chd', children: [{ name: 'subentry', min: 1, max: null }] }
      }
   }
   assert.equal(createInitialElement(schema, schema.root), '<subentry><subentry></subentry></subentry>')
})

test('modern and legacy starter overrides work without a custom editor specification', () => {
   const schema = { root: 'entry', elements: {} }
   assert.equal(createInitialXml({ ...schema, _newXml: '<entry>current</entry>' }), '<entry>current</entry>')
   assert.equal(createInitialXml({ ...schema, newXml: '<entry>legacy</entry>' }), '<entry>legacy</entry>')
})

test('Xonomy validates aliased subentry references as their parent definition’s children', () => {
   const schema = {
      root: 'entry',
      elements: {
         entry: { filling: 'chd', children: [{ name: 'first-sense', min: 1, max: 1 }] },
         'first-sense': { elementName: 'sense', filling: 'txt' },
         'other-sense': { elementName: 'sense', filling: 'txt' }
      }
   }
   const xonomy = new Proxy({ warnings: [] }, { get: (target, name) => target[name] ?? (() => {}) })
   const { validate } = createDocSpec(xonomy, schema)
   const reference = {
      type: 'element',
      id: 'lxnm:subentryParent',
      elementName: 'lxnm:subentryParent',
      getAttributeValue: name => name === 'doctype' ? 'sense' : undefined
   }
   const root = {
      id: 'entry', elementName: 'entry', htmlID: 'entry', attributes: [],
      children: [reference], parent: () => undefined,
      getChildElements(id) { return this.children.filter(child => child.id === id) }
   }
   validate(root)
   assert.deepEqual(xonomy.warnings, [])
   root.children.push(reference)
   validate(root)
   assert.ok(xonomy.warnings.some(warning => warning.htmlID === 'entry' && warning.text.includes('between 1 and 1 <sense>')))
})

test('legacy string-zero maxima remain unlimited while numeric zero is explicit', () => {
   assert.equal(maximumChildCount('0'), Infinity)
   assert.equal(maximumChildCount(''), Infinity)
   assert.equal(maximumChildCount(null), Infinity)
   assert.equal(maximumChildCount(0), 0)
   assert.equal(maximumChildCount('2'), 2)
})
