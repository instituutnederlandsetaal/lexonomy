import Materialize from '../../libs/materialize/materialize.min.js'
import { api, basePath } from '../../js/api.ts'

export const Xrefs = {
   extendDocspec(docspec, xema, emit) {
      for (const name of Object.keys(xema.elements)) {
         if (!linking[name] || !docspec.elements[name]) continue
         const caption = docspec.elements[name].caption
         docspec.elements[name] = {
            ...docspec.elements[name],
            caption(element) {
               const original = typeof caption === 'function' ? caption(element) : caption
               return `${original || ''}<button class="btn btn-secondary lexonomyXrefsCaption" onclick='Xonomy.notclick=true; Xrefs.linkBox("${element.htmlID}")'>▼</button>`
            },
         }
      }
      this.emit = emit
   },

   linkBox(htmlID) {
      const editor = Xonomy
      const emit = this.emit
      const box = $(`
         <div class="xrefsbox">
            Link this element to<br/>dictionary:
            <select name="xrefdict" class="browser-default" style="display:inline-block;width:auto"></select><br/>
            target:
            <div class="input-field"><input id="xreftarget" name="xreftarget" class="autocomplete"/></div>
            <button class="btn">Link</button>
         </div>`)
      const dictionaries = box.find('select')
      const target = box.find('input')[0]
      const button = box.find('button').prop('disabled', true)
      const path = encodeURIComponent(dictId)
      const cookiePath = basePath + path
      let selected
      let request = 0
      for (const dict of userDicts) {
         if (dict.id !== dictId && dict.hasLinks) dictionaries.append(new Option(dict.title, dict.id))
      }
      const preferred = Cookies.get('linkPref')
      if (Array.from(dictionaries[0].options).some(option => option.value === preferred)) {
         dictionaries.val(preferred)
      }
      const refresh = async () => {
         const revision = ++request
         const id = dictionaries.val()
         Materialize.Autocomplete.getInstance(target)?.destroy()
         button.prop('disabled', true)
         target.value = ''
         selected = null
         if (!id) return
         const result = await api.get(`${encodeURIComponent(id)}/linkablelist.json`).catch(() => null)
         if (!box[0].isConnected || revision !== request || !result) return
         const links = new Map(result.links.map(item => [
            `${item.element}: ${item.link}${item.preview ? ' (' + item.preview + ')' : ''}`, item,
         ]))
         Materialize.Autocomplete.init(target, {
            data: Object.fromEntries([...links.keys()].map(label => [label, null])),
            limit: 10,
            onAutocomplete: text => {
               selected = links.get(text)
               button.prop('disabled', !selected)
            },
         })
      }
      dictionaries.on('change', refresh)
      button.on('click', async () => {
         if (!selected) return
         const element = document.getElementById(htmlID)
         const targetDict = dictionaries.val()
         const source = $(element).children('.tag.opening').children('.attributes').children('[data-name="lxnm:linkable"]')
         Cookies.set('linkPref', targetDict, { path: cookiePath })
         editor.destroyBubble()
         const result = await api.get(`${path}/links/add`, {
            source_el: element.dataset.name, source_id: source.data('value'),
            target_dict: targetDict, target_el: selected.element, target_id: selected.link,
         }).catch(() => null)
         if (!element.isConnected) return
         if (result?.success) {
            emit('status', 'Link created successfully.')
            emit('links-changed')
         } else {
            emit('status', result?.error ? 'Error while creating link: ' + result.error : 'Failed to create link.', 'warn')
         }
      })
      editor.makeBubble(box)
      editor.showBubble($('#' + htmlID + ' > .inlinecaption'))
      refresh()
   },
}
