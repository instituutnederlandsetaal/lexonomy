<template>
   <div id="editor" @input="markCustomDirty" @change="markCustomDirty"></div>
</template>

<script>
import jquery from '../../libs/jquery/jquery.min.js'
import cookies from '../../libs/js.cookie.js'
import '../../node_modules/@elexis-eu/xonomy/dist/xonomy.css'
import { Xonomy as XonomyClass } from '@elexis-eu/xonomy'
import * as XonomyExports from '@elexis-eu/xonomy'
import { basePath } from '../../js/api.ts'
import { activeDictionary } from '../../js/dictionary-workspace.ts'
import { myDictionaries } from '../../js/my-dictionaries.ts'
import { parseDTD, struct2Xonomy } from '../../libs/xonomy-tools/dtdconvert/dtd2xonomy.js'
import { Xematron } from '../../widgets/xematron.js'
import { Xemplatron } from '../../widgets/xemplatron.js'
import { Sub } from './sub.js'
import { Xrefs } from './xrefs.js'
import './sub.css'
import './xrefs.css'

export default {
   props: { entry: Object, config: Object, readonly: Boolean, initialXml: String },
   emits: ['use-graphical', 'dirty-change', 'links-changed', 'status'],
   mounted() {
      const { xema, xemplate, subbing, titling, flagging, linking, editing } = this.config
      const context = {
         $: jquery, jQuery: jquery, Cookies: cookies, XonomyExports, Xematron, Xemplatron, API_URL: basePath,
         Sub, Xrefs, xema, xemplate, subbing, titling, flagging, linking, editing,
         dictId: activeDictionary.dictId, userDicts: myDictionaries.items
      }
      const saved = Object.fromEntries([...Object.keys(context), 'Xonomy'].map(key => [key, window[key]]))
      Object.assign(window, context)
      const xonomy = window.Xonomy = new XonomyClass()
      this.cleanup = () => {
         xonomy.$div?.off('.lexonomyEditor')
         jquery(document.body).off('click', xonomy.boundClickOff).off('dragend', xonomy.boundDragend)
         Object.assign(window, saved)
      }
      xonomy.buttonClass = 'btn'
      xonomy.lang = 'en'
      xonomy.baseUrl = basePath

      let custom
      if (editing._js) {
         try {
            custom = new Function('return ' + editing._js)()
         } catch {
            this.$emit('status', 'Invalid custom editor code.', 'warn')
         }
      }
      if (custom?.editor && custom.harvester) {
         this.custom = custom
         custom.editor(this.$el, { ...this.entry, content: this.initialXml }, this.readonly)
      } else if (!this.readonly && editing.xonomyMode === 'graphical') {
         this.$emit('use-graphical')
      } else {
         const dictId = activeDictionary.dictId
         const cookie = 'xonomyMode_' + dictId
         const mode = editing.xonomyMode === 'graphical' ? 'nerd' : cookies.get(cookie) || editing.xonomyMode
         xonomy.setMode(mode)
         let docSpec = xema._xonomyDocSpec
         if (typeof docSpec === 'string') {
            try {
               docSpec = new Function('return (' + docSpec + ')')()
            } catch {
               docSpec = null
               this.$emit('status', 'Invalid Xonomy document specification.', 'warn')
            }
         }
         docSpec = docSpec ? { ...docSpec, elements: { ...docSpec.elements } }
            : xema._dtd ? struct2Xonomy(parseDTD(xema._dtd)) : Xematron.xema2docspec(xema, editing.xonomyTextEditor)
         docSpec.allowModeSwitching = true
         docSpec.onModeSwitch = mode => {
            cookies.set(cookie, mode)
            const doctypes = document.querySelector('.doctypes')
            doctypes?.classList.remove('laic', 'nerd')
            doctypes?.classList.add(mode)
         }
         docSpec.onchange = () => this.$emit('dirty-change', true)
         if (!this.readonly) {
            docSpec.allowLayby = true
            docSpec.laybyMessage = 'This is your temporary lay-by for entry fragments. You can drag and drop XML elements here.'
            Xrefs.extendDocspec(docSpec, xema, this.$emit)
         }
         Sub.extendDocspec(docSpec, xema, { ...this.entry, id: this.entry.id || this.entry.entry_id })
         custom?.adjustDocSpec?.(docSpec)
         if (this.readonly) {
            for (const [name, spec] of Object.entries(docSpec.elements)) {
               docSpec.elements[name] = { ...spec, isReadOnly: true }
            }
            const unknown = docSpec.unknownElement
            if (unknown) docSpec.unknownElement = typeof unknown === 'function'
               ? name => ({ ...unknown(name), isReadOnly: true }) : { ...unknown, isReadOnly: true }
         }
         xonomy.render(this.initialXml, this.$el, docSpec)
         xonomy.keyNav = true
         xonomy.keyboardEventCatcher = xonomy.$div.attr('tabindex', 0).on('keydown.lexonomyEditor', event => xonomy.key(event))
         xonomy.scrollableContainer = jquery(this.$el.closest('#container'))
      }
      this.xonomy = xonomy
   },
   beforeUnmount() {
      this.cleanup?.()
   },
   methods: {
      markCustomDirty() {
         if (this.custom && !this.readonly) this.$emit('dirty-change', true)
      },
      harvest() {
         return this.custom ? this.custom.harvester(this.$el) : this.xonomy?.harvest()
      }
   }
}
</script>
