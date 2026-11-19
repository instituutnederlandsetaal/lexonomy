import assert from 'node:assert/strict'
import { test } from 'node:test'
import { canReceiveNode, elementDisplay, findDraftHeadword, findMoveParents, moveNode, serializeDraft } from '../components/graphical-editor/editor-schema.ts'

test('graphical formatting falls back to stored XML tag names', () => {
   const xema = { root: 'record-id', elements: { 'record-id': {
      elementName: 'record', attributes: { label: { optionality: 'obligatory' } }
   } } }
   const template = {
      'record-id': { displayType: 'inline' },
      record: { displayType: 'popup', attributes: { label: { shown: false } } }
   }
   assert.equal(elementDisplay(template, xema, 'record-id').displayType, 'inline')
   assert.equal(elementDisplay(template, xema, 'record-id').editorLabel, 'record')
   assert.equal(elementDisplay({ record: template.record }, xema, 'record-id').displayType, 'popup')
   assert.equal(elementDisplay(template, xema, 'label', 'record-id', true).shown, false)
   assert.equal(elementDisplay(template, xema, 'label', 'record-id', true).editorLabel, 'label*')
})

test('moves stay within the active draft and respect both maximum formats', () => {
   const node = { type: 'element', name: 'sense' }
   const origin = { type: 'element', name: 'section', elements: [node] }
   const destination = { type: 'element', name: 'section' }
   const popup = { type: 'element', name: 'popup', elements: [origin, destination] }
   const rule = { name: 'sense', min: 0, max: '0' }
   const xema = { root: 'popup', elements: { section: { children: [rule] } } }
   assert.equal(canReceiveNode(xema, 'section', origin, 'sense', node), false)
   assert.equal(canReceiveNode(xema, 'section', destination, 'sense', node), true)
   rule.max = 0
   assert.equal(canReceiveNode(xema, 'section', destination, 'sense', node), false)
   assert.equal(moveNode(popup, { node, destination: { ...destination } }), null)
   assert.equal(serializeDraft(moveNode(popup, { node, destination })), '<popup><section/><section><sense/></section></popup>')
   assert.equal(serializeDraft(popup), '<popup><section><sense/></section><section/></popup>')
})

test('move destinations follow the entry and popup draft boundaries', () => {
   const node = (name, ...elements) => ({ type: 'element', name, elements })
   const source = node('sense')
   const popupSource = node('sense')
   const inlineDestination = node('section')
   const popupDestination = node('section')
   const popup = node('dialog', node('section', popupSource), popupDestination)
   const document = { elements: [node('record', node('section', source), inlineDestination, popup)] }
   const child = name => ({ name, min: 0, max: null })
   const config = {
      xema: { root: 'record-id', elements: {
         'record-id': { elementName: 'record', filling: 'chd', children: [child('inline-section'), child('dialog')] },
         'inline-section': { elementName: 'section', filling: 'chd', children: [child('sense')] },
         'popup-section': { elementName: 'section', filling: 'chd', children: [child('sense')] },
         dialog: { filling: 'chd', children: [child('popup-section'), child('sense')] }
      } },
      xemplate: { 'inline-section': { shown: false, readOnly: true }, dialog: { displayType: 'popup' } },
      subbing: {}
   }
   const scope = { elementName: 'dialog', parentElementName: 'record-id' }
   const names = candidates => candidates.map(({ elementName }) => elementName)
   assert.deepEqual(names(findMoveParents(config, document, source, 'sense')), ['inline-section', 'dialog'])
   assert.deepEqual(names(findMoveParents(config, popup, popupSource, 'sense', scope)), ['dialog', 'popup-section'])
   assert.deepEqual(findMoveParents(config, popup, source, 'sense', scope), [])
})

test('headword lookup resolves the active draft field by schema ID', () => {
   const xema = { root: 'record-id', elements: {
      'record-id': { elementName: 'record' }, word_id: { elementName: 'headword' }
   } }
   const word = { type: 'element', name: 'headword', elements: [{ type: 'text', text: 'Draft word' }] }
   const entry = { elements: [{ type: 'element', name: 'record', elements: [word] }] }
   assert.equal(findDraftHeadword(xema, entry, 'word_id'), 'Draft word')
   assert.equal(findDraftHeadword(xema, { type: 'element', name: 'dialog' }, 'word_id', { elementName: 'dialog' }), undefined)
})
