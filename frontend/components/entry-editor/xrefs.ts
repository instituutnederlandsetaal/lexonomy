import $ from 'jquery'
import type { Xonomy, XonomyDocSpecExternal } from '@elexis-eu/xonomy'
import cookies from '../../libs/js.cookie.js'
import type { WorkspaceConfig } from '../../js/dictionary-workspace.ts'
import type { MyDictionary } from '../../js/my-dictionaries.ts'
import { dictionaryPath } from '../../js/api.ts'
import { pageUrl } from '../../js/page-url.ts'
import { entryEditorApi, type LinkTarget } from '../../js/entry-editor-api.ts'
import { xmlElementName, type Xema } from '../../js/xema.ts'

type LinkNotifications = {
   (event: 'status', text: string, style?: string): void
   (event: 'links-changed'): void
}

export function createCrossReferenceTools(editor: Xonomy, dictId: string, userDicts: readonly MyDictionary[],
   linking: WorkspaceConfig['linking'], emit: LinkNotifications) {
   let notify = emit

   function extendDocspec(docspec: XonomyDocSpecExternal, xema: Xema, send = emit) {
      const elements = docspec.elements ??= {}
      for (const id of Object.keys(xema.elements)) {
         const name = xmlElementName(xema, id)
         const key = Object.hasOwn(elements, id) ? id : name
         const spec = elements[key]
         if ((!linking[id] && !linking[name]) || !spec) continue
         const caption = spec.caption
         elements[key] = {
            ...spec,
            caption(element) {
               const original = typeof caption === 'function' ? caption(element) : caption
               return `${original || ''}<button type="button" class="btn btn-secondary lexonomyXrefsCaption" aria-label="Link this element">▼</button>`
            },
         }
      }
      notify = send
   }

   function linkBox(htmlId: string) {
      const element = document.getElementById(htmlId)
      if (!element) return
      const box = $(`
         <div class="xrefsbox">
            Link this element to<br/>dictionary:
            <select name="xrefdict" class="browser-default" style="display:inline-block;width:auto"></select><br/>
            target:
            <div class="input-field"><input id="xreftarget" name="xreftarget" list="xref-options" aria-label="Link target"/></div>
            <datalist id="xref-options"></datalist>
            <button class="btn">Link</button>
         </div>`)
      const dictionaries = box.find<HTMLSelectElement>('select')[0]
      const target = box.find<HTMLInputElement>('input')[0]
      const button = box.find('button').prop('disabled', true)
      const cookiePath = pageUrl.pathname + dictionaryPath(dictId)
      const options = box.find<HTMLDataListElement>('datalist')[0]
      const links = new Map<string, LinkTarget>()
      let selected: LinkTarget | undefined
      let request = 0
      for (const dict of userDicts) {
         if (dict.id !== dictId && dict.hasLinks) dictionaries.append(new Option(dict.title, dict.id))
      }
      const preferred = cookies.get('linkPref')
      if (Array.from(dictionaries.options).some(option => option.value === preferred)) {
         dictionaries.value = preferred
      }
      const refresh = async () => {
         const revision = ++request
         const id = dictionaries.value
         links.clear()
         options.replaceChildren()
         button.prop('disabled', true)
         target.value = ''
         selected = undefined
         if (!id) return
         const result = await entryEditorApi.linkTargets(id).catch(() => null)
         if (!box[0]?.isConnected || revision !== request || !result) return
         for (const item of result.links) {
            const label = `${item.element}: ${item.link}${item.preview ? ' (' + item.preview + ')' : ''}`
            if (links.has(label)) continue
            links.set(label, item)
            options.append(new Option(label, label))
         }
      }
      target.addEventListener('input', () => {
         selected = links.get(target.value)
         button.prop('disabled', !selected)
      })
      dictionaries.addEventListener('change', refresh)
      button.on('click', async () => {
         if (!selected) return
         const targetDict = dictionaries.value
         const source = editor.harvestElement(element)
         const sourceId = source.getAttributeValue('lxnm:linkable')
         if (!sourceId || !targetDict) return
         cookies.set('linkPref', targetDict, { path: cookiePath })
         editor.destroyBubble()
         const result = await entryEditorApi.addLink(dictId, {
            source_el: source.elementName, source_id: sourceId,
            target_dict: targetDict, target_el: selected.element, target_id: selected.link,
         }).catch(() => null)
         if (!element.isConnected) return
         if (result?.success) {
            notify('status', 'Link created successfully.')
            notify('links-changed')
         } else {
            notify('status', result?.error ? 'Error while creating link: ' + result.error : 'Failed to create link.', 'warn')
         }
      })
      editor.makeBubble(box)
      editor.showBubble($(element).children('.inlinecaption'))
      void refresh()
   }

   return { extendDocspec, linkBox }
}
