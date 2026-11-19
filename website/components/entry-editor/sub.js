import subentryIcon from '../../furniture/favicon.png'
import { api } from '../../js/api.ts'
import { activeDictionary } from '../../js/dictionary-workspace.ts'
import { router } from '../../js/router.ts'

export const Sub = {
   extendDocspec(docspec, xema, entry) {
      const editor = Xonomy
      const children = this.children = Object.fromEntries((entry.subentries || []).map(item => [item.id, item]))
      this.entryID = entry.id
      if (entry.id && !entry.subentries) {
         api.post(`${encodeURIComponent(dictId)}/entryread.json`, { id: entry.id }).then(result => {
            if (!editor.$div[0]?.isConnected) return
            for (const child of result.subentries || []) children[child.id] = child
            editor.refresh()
         }).catch(() => {})
      }

      for (const [id, element] of Object.entries(xema.elements)) {
         const subentries = (element.children || []).filter(child => subbing[child.name])
         if (!subentries.length) continue
         const existing = docspec.elements[id] || {}
         docspec.elements[id] = {
            ...existing,
            menu: [...(existing.menu || []), ...subentries.map(child => {
               const elName = xema.elements[child.name]?.elementName || child.name
               return {
                  icon: subentryIcon, caption: 'Find subentries <' + elName + '>',
                  action: Sub.subentrySearchMenu, actionParameter: { elName },
               }
            })],
         }
      }

      docspec.elements['lxnm:subentryParent'] = {
         caption(item) {
            const { title = 'Loading...' } = children[item.getAttribute('id')?.value] || {}
            return `${title} <span class="lexonomySubentryCaption" onclick='Xonomy.notclick=true; Sub.menuSubentry("${item.htmlID}")'>Also used in... ▼</span>`
         },
         backgroundColour() { return '#e6e6e6' },
         displayName(item) { return children[item.getAttribute('id')?.value]?.doctype || 'Loading...' },
         menu: [{ action: editor.deleteElement, caption: 'Remove this subentry' }],
         attributes: { id: { isReadOnly: true } },
      }
   },

   async menuSubentry(htmlID) {
      const editor = Xonomy
      const anchor = $('#' + htmlID + ' > .inlinecaption')
      const item = editor.harvestElement(document.getElementById(htmlID))
      const id = item.getAttributeValue('id', 0)
      if (!this.children[id]?.parententries) {
         const waiting = editor.makeBubble('<div>Loading parents...</div>')
         editor.showBubble(anchor)
         const result = await api.post(`${encodeURIComponent(dictId)}/entryread.json`, { id }).catch(() => null)
         if (!waiting[0].isConnected) return
         if (!result?.success) {
            waiting.text('Failed to load parents.')
            return
         }
         this.children[id] = result
      }
      const parents = this.children[id].parententries.filter(parent => parent.id != this.entryID)
      const message = parents.length === 1 ? 'shared with one other entry.' :
         parents.length ? `shared with ${parents.length} other entries.` : 'not shared with any other entry.'
      const html = $('<div class="subinfobox"><div class="topline"><span class="opener">This subentry</span></div></div>')
      html.find('.topline').append(document.createTextNode(' is ' + message))
      html.find('.opener').on('click', () => this.openEntry(id))
      if (parents.length) {
         const lines = $('<div class="entrylines"></div>').appendTo(html)
         for (const parent of parents) {
            $('<div class="entryline"></div>').html(parent.title).on('click', () => this.openEntry(parent.id)).appendTo(lines)
         }
      }
      editor.makeBubble(html)
      editor.showBubble(anchor)
   },

   openEntry(id) {
      const { dictId, doctype, mode } = activeDictionary
      router.push({ name: 'edit', params: { dictId, doctype, entryId: id, mode }, query: router.currentRoute.value.query })
   },

   subentrySearchMenu(htmlID, { elName }) {
      const xml = $($.parseXML(Xonomy.harvest()))
      const headword = xml.find(titling.headword).text()
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
      const field = box.find('input[name=val]').val(headword)
      const choices = box.find('.choices').hide()
      const waiter = box.find('.waiter').hide()
      const bottom = box.find('.bottombar').hide()
      let searchId = 0
      const search = async () => {
         const request = ++searchId
         choices.empty().hide()
         bottom.hide()
         const lemma = field.val().trim()
         waiter.toggle(Boolean(lemma))
         if (!lemma) return
         const result = await api.get(`${encodeURIComponent(dictId)}/subget/`, { lemma, doctype: elName }).catch(() => null)
         if (request !== searchId || !box[0].isConnected) return
         if (!result?.success || !result.entries?.length) {
            $('<div class="error"></div>').text(result?.success ? 'No matches found.' : 'Failed to load subentries.').appendTo(choices)
         } else {
            for (const entry of result.entries) {
               const label = $('<label><input type="checkbox"/><span class="inside"></span></label>').data('entry', entry)
               label.find('input').on('change', event => label.toggleClass('selected', event.target.checked))
               label.find('.inside').html(entry.title)
               label.appendTo(choices)
            }
            bottom.show()
         }
         waiter.hide()
         choices.show()
      }
      box.find('form').on('submit', event => {
         event.preventDefault()
         search()
      })
      box.find('.creator').on('click', () => {
         Xonomy.newElementChild(htmlID, Xematron.initialElement(xema, elName))
         Xonomy.clickoff()
      })
      box.find('.insert').on('click', () => {
         choices.find('.selected').each((_, label) => {
            const { id, title, doctype } = $(label).data('entry')
            Sub.children[id] = { id, title, doctype }
            const escape = value => Xonomy.xmlEscape(value)
            Xonomy.newElementChild(htmlID, `<lxnm:subentryParent xmlns:lxnm="http://www.lexonomy.eu/" id="${escape(id)}" doctype="${escape(doctype)}" title="${escape(title)}"/>`)
         })
      })
      const anchor = { openingTagName: ' > .tag.opening > .name', closingTagName: ' > .tag.closing > .name' }
      Xonomy.makeBubble(box)
      Xonomy.showBubble($('#' + htmlID + (anchor[Xonomy.lastClickWhat] || '')))
      if (headword) {
         search()
         field.select()
      }
   },
}
