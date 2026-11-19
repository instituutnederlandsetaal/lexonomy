import assert from 'node:assert/strict'
import { test } from 'node:test'
import { previewFormatting } from '../js/xemplate.ts'

test('preview uses a visible block for elements and hides unconfigured attributes', () => {
   const element = previewFormatting({}, 'headword', 'headword')
   assert.equal(element.shown, true)
   assert.equal(element.layout, 'block')
   const attribute = previewFormatting({}, 'headword', 'headword', 'language')
   assert.equal(attribute.shown, false)
   assert.equal(attribute.layout, 'inline')
})

test('alias settings override legacy tag keys while preserving legacy attribute fallbacks', () => {
   const template = {
      'first-sense': { shown: true, layout: 'block', attributes: { kind: { shown: false } } },
      sense: {
         shown: 'false',
         layout: 'inline',
         gutter: 'handing',
         attributes: { kind: { shown: 'true' }, number: { shown: 'true', label: 'Number' } }
      }
   }
   assert.equal(previewFormatting(template, 'first-sense', 'sense').shown, true)
   assert.equal(previewFormatting(template, 'another-sense', 'sense').shown, false)
   assert.equal(previewFormatting(template, 'another-sense', 'sense').layout, 'inline')
   assert.equal(previewFormatting(template, 'another-sense', 'sense').gutter, 'hanging')
   assert.equal(previewFormatting(template, 'first-sense', 'sense', 'kind').shown, false)
   assert.equal(previewFormatting(template, 'first-sense', 'sense', 'number').label, 'Number')
})
