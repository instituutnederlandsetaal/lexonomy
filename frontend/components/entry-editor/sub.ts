import subentryIcon from '../../assets/furniture/favicon.png'
import $ from 'jquery'
import type { Xonomy, XonomyDocSpecExternal, XonomyMenuActionExternal, XonomyWhat } from '@elexis-eu/xonomy'
import { subentryReferenceXml } from '../../js/editor-extension.ts'
import { entryEditorApi, type RelatedEntry } from '../../js/entry-editor-api.ts'
import { sanitizeHtml } from '../../js/sanitize-html.ts'
import type { WorkspaceConfig } from '../../js/dictionary-workspace.ts'
import { xmlElementName, type Xema } from '../../js/xema.ts'
import { createInitialElement } from '../../widgets/xematron.ts'

type Subentry = RelatedEntry & { parententries?: RelatedEntry[] }

export function createSubentryTools(editor: Xonomy, dictId: string, config: Pick<WorkspaceConfig, 'xema' | 'subbing' | 'titling'>,
   openEntry: (id: number, doctype?: string) => void) {
   const { subbing, titling } = config
   const children = new Map<number, Subentry>()
   let entryId: number | undefined

   function extendDocspec(docspec: XonomyDocSpecExternal, xema: Xema, entry: { id?: number; subentries?: RelatedEntry[] }) {
      const elements = docspec.elements ??= {}
      children.clear()
      for (const child of entry.subentries ?? []) children.set(child.id, child)
      entryId = entry.id
      if (entry.id && !entry.subentries) {
         entryEditorApi.read(dictId, entry.id).then(result => {
            if (!result.success || !editor.$div[0]?.isConnected) return
            for (const child of result.subentries ?? []) children.set(child.id, child)
            editor.refresh()
         }).catch(() => {})
      }

      for (const [id, element] of Object.entries(xema.elements)) {
         const subentries = (element.children || []).filter(child => subbing[child.name])
         if (!subentries.length) continue
         const name = xmlElementName(xema, id)
         const key = Object.hasOwn(elements, id) ? id : name
         const existing = elements[key] || {}
         elements[key] = {
            ...existing,
            menu: [...(existing.menu ?? []), ...subentries.map((child): XonomyMenuActionExternal & { icon: string } => {
               const elName = xmlElementName(xema, child.name)
               return {
                  icon: subentryIcon, caption: 'Find subentries <' + elName + '>',
                  action: htmlId => subentrySearchMenu(htmlId, { elName, schemaId: child.name }),
               }
            })],
         }
      }

      elements['lxnm:subentryParent'] = {
         caption(item) {
            const title = children.get(Number(item.getAttributeValue('id')))?.title ?? 'Loading...'
            return `${sanitizeHtml(title)} <button type="button" class="lexonomySubentryCaption">Also used in... ▼</button>`
         },
         backgroundColour() { return '#e6e6e6' },
         displayName(item) { return children.get(Number(item.getAttributeValue('id')))?.doctype || 'Loading...' },
         menu: [{ action: editor.deleteElement, caption: 'Remove this subentry' }],
         attributes: { id: { isReadOnly: true } },
      }
   }

   async function menuSubentry(htmlId: string) {
      const element = document.getElementById(htmlId)
      if (!element) return
      const anchor = $(element).children('.inlinecaption')
      const item = editor.harvestElement(element)
      const id = Number(item.getAttributeValue('id'))
      if (!id) return
      let child = children.get(id)
      if (!child?.parententries) {
         const waiting = editor.makeBubble('<div>Loading parents...</div>')
         editor.showBubble(anchor)
         const result = await entryEditorApi.read(dictId, id).catch(() => null)
         if (!waiting[0]?.isConnected) return
         if (!result?.success) {
            waiting.text('Failed to load parents.')
            return
         }
         child = result
         children.set(id, child)
      }
      const parents = (child.parententries ?? []).filter(parent => parent.id !== entryId)
      const message = parents.length === 1 ? 'shared with one other entry.' :
         parents.length ? `shared with ${parents.length} other entries.` : 'not shared with any other entry.'
      const html = $('<div class="subinfobox"><div class="topline"><span class="opener">This subentry</span></div></div>')
      html.find('.topline').append(document.createTextNode(' is ' + message))
      html.find('.opener').on('click', () => openEntry(id, child.doctype))
      if (parents.length) {
         const lines = $('<div class="entrylines"></div>').appendTo(html)
         for (const parent of parents) {
            $('<div class="entryline"></div>').html(sanitizeHtml(parent.title)).on('click', () => openEntry(parent.id, parent.doctype)).appendTo(lines)
         }
      }
      editor.makeBubble(html)
      editor.showBubble(anchor)
   }

   function subentrySearchMenu(htmlID: string, { elName, schemaId }: { elName: string; schemaId: string }) {
      const { xema } = config
      const xml = $.parseXML(editor.harvest())
      const headwordName = titling.headword && xmlElementName(xema, titling.headword)
      const headword = headwordName ? xml.getElementsByTagName(headwordName)[0]?.textContent ?? '' : ''
      const box = $(`
         <div class="subbox">
            <form class="topbar">
               <input name="val" class="textbox focusme"/>
               <input type="submit" class="button sub" value="&nbsp;"/>
               <button type="button" class="creator">New</button>
            </form>
            <div class="waiter"></div>
            <div class="choices"></div>
            <div class="bottombar"><button class="insert">Insert</button></div>
         </div>`)
      const field = box.find<HTMLInputElement>('input[name=val]')
      field.val(headword)
      const choices = box.find('.choices').hide()
      const waiter = box.find('.waiter').hide()
      const bottom = box.find('.bottombar').hide()
      const matches = new Map<HTMLInputElement, RelatedEntry>()
      let searchId = 0
      const search = async () => {
         const request = ++searchId
         choices.empty().hide()
         bottom.hide()
         matches.clear()
         const lemma = field[0].value.trim()
         waiter.toggle(Boolean(lemma))
         if (!lemma) return
         const result = await entryEditorApi.subentries(dictId, lemma, elName, schemaId).catch(() => null)
         if (request !== searchId || !box[0]?.isConnected) return
         if (!result?.success || !result.entries?.length) {
            $('<div class="error"></div>').text(result?.success ? 'No matches found.' : 'Failed to load subentries.').appendTo(choices)
         } else {
            for (const entry of result.entries) {
               const label = $('<label><input type="checkbox"/><span class="inside"></span></label>')
               const input = label.find<HTMLInputElement>('input')[0]
               matches.set(input, entry)
               input.addEventListener('change', () => label.toggleClass('selected', input.checked))
               label.find('.inside').html(sanitizeHtml(entry.title))
               label.appendTo(choices)
            }
            bottom.show()
         }
         waiter.hide()
         choices.show()
      }
      box.find('form').on('submit', event => {
         event.preventDefault()
         void search()
      })
      box.find('.creator').on('click', () => {
         editor.newElementChild(htmlID, createInitialElement(xema, schemaId))
         editor.clickoff()
      })
      box.find('.insert').on('click', () => {
         for (const [input, entry] of matches) {
            if (!input.checked) continue
            children.set(entry.id, entry)
            editor.newElementChild(htmlID, subentryReferenceXml(entry))
         }
      })
      const anchor: Partial<Record<XonomyWhat, string>> = {
         openingTagName: ' > .tag.opening > .name', closingTagName: ' > .tag.closing > .name'
      }
      editor.makeBubble(box)
      editor.showBubble($('#' + htmlID + (anchor[editor.lastClickWhat] || '')))
      if (headword) {
         void search()
         field[0].select()
      }
   }

   return { extendDocspec, menuSubentry, openEntry, subentrySearchMenu }
}
