<template>
   <div id="editor" ref="element" @input="markCustomDirty" @change="markCustomDirty"></div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import jquery from 'jquery'
import cookies from '../../libs/js.cookie.js'
import '../../node_modules/@elexis-eu/xonomy/dist/xonomy.css'
import { Xonomy as XonomyClass, type XonomyDocSpec, type XonomyDocSpecExternal } from '@elexis-eu/xonomy'
import * as XonomyExports from '@elexis-eu/xonomy'
import { basePath } from '../../js/api.ts'
import type { WorkspaceConfig } from '../../js/dictionary-workspace.ts'
import type { EntryDraft, EntryRevision } from '../../js/entry-editor-api.ts'
import { crossReferenceHref } from '../../js/entry-search.ts'
import type { MyDictionary } from '../../js/my-dictionaries.ts'
import { parseDTD, struct2Xonomy } from '../../libs/xonomy-tools/dtdconvert/dtd2xonomy.js'
import type { Xema } from '../../js/xema.ts'
import { createDocSpec, createInitialElement, createInitialXml } from '../../widgets/xematron.ts'
import { Xemplatron } from '../../widgets/xemplatron.ts'
import { createSubentryTools } from './sub.ts'
import { createCrossReferenceTools } from './xrefs.ts'
import './sub.css'
import './xrefs.css'

type CustomEditor = {
   editor?: (element: HTMLElement, entry: EntryDraft | EntryRevision, readonly: boolean) => void
   harvester?: (element: HTMLElement) => string | Promise<string>
   adjustDocSpec?: (docSpec: XonomyDocSpecExternal) => void
}

const props = defineProps<{
   entry: EntryDraft | EntryRevision; dictId: string; config: WorkspaceConfig
   userDicts: readonly MyDictionary[]; readonly?: boolean; initialXml: string
}>()
const emit = defineEmits<{
   'use-graphical': []
   'dirty-change': [dirty: boolean]
   'links-changed': []
   'open-entry': [id: number, doctype?: string]
   status: [text: string, style?: string]
}>()
const element = ref<HTMLElement | null>(null)
let xonomy: XonomyClass | undefined
let customHarvester: CustomEditor['harvester']
let restoreGlobals: (() => void) | undefined
let captionEvents: AbortController | undefined

onMounted(() => {
   const root = element.value
   if (!root) return
   const { xema, xemplate, subbing, titling, flagging, linking, editing } = props.config
   const context = {
      $: jquery, jQuery: jquery, Cookies: cookies, XonomyExports, API_URL: basePath,
      Xemplatron: {
         ...Xemplatron,
         xml2html: (...[xml, template, schema]: Parameters<typeof Xemplatron.xml2html>) =>
            Xemplatron.xml2html(xml, template, schema, crossReferenceHref)
      },
      Xematron: {
         xema2docspec: (schema: Xema, asker?: string) => createDocSpec(editor, schema, asker),
         xema2xml: createInitialXml,
         initialElement: createInitialElement,
      },
      xema, xemplate, subbing, titling, flagging, linking, editing,
      dictId: props.dictId, userDicts: props.userDicts
   }
   // Stored custom editors and Xonomy's legacy event handlers access this context by name.
   const previous = new Map([...Object.keys(context), 'Xonomy', 'Sub', 'Xrefs']
      .map(key => [key, Object.getOwnPropertyDescriptor(window, key)]))
   restoreGlobals = () => {
      for (const [key, descriptor] of previous) {
         if (descriptor) Object.defineProperty(window, key, descriptor)
         else Reflect.deleteProperty(window, key)
      }
   }
   Object.assign(window, context)
   const editor = xonomy = new XonomyClass()
   const setFocus = editor.setFocus.bind(editor)
   // Xonomy schedules focus after edits, including when the editor has since unmounted.
   editor.setFocus = (id, target) => {
      if (root.isConnected) setFocus(id, target)
   }
   const subentries = createSubentryTools(editor, props.dictId, props.config, (id, doctype) => emit('open-entry', id, doctype))
   const xrefs = createCrossReferenceTools(editor, props.dictId, props.userDicts, linking, emit)
   Object.assign(window, { Xonomy: editor, Sub: subentries, Xrefs: xrefs })
   editor.buttonClass = 'btn'
   editor.lang = 'en'
   Object.assign(editor, { baseUrl: basePath })

   const custom = readCustomEditor(editing._js)
   if (typeof custom?.editor === 'function' && typeof custom.harvester === 'function') {
      try {
         custom.editor(root, { ...props.entry, content: props.initialXml }, Boolean(props.readonly))
         customHarvester = custom.harvester.bind(custom)
         return
      } catch {
         root.replaceChildren()
         emit('status', 'Failed to open the custom editor.', 'warn')
      }
   } else if (!props.readonly && editing.xonomyMode === 'graphical') {
      emit('use-graphical')
      return
   }

   const cookie = 'xonomyMode_' + props.dictId
   const preference = cookies.get(cookie)
   editor.setMode(preference === 'laic' || (!preference && editing.xonomyMode === 'laic') ? 'laic' : 'nerd')
   const docSpec = readDocSpec(xema._xonomyDocSpec)
      ?? (xema._dtd ? struct2Xonomy(parseDTD(xema._dtd)) as XonomyDocSpecExternal : createDocSpec(editor, xema, editing.xonomyTextEditor))
   const elements = docSpec.elements ??= {}
   docSpec.allowModeSwitching = true
   docSpec.onModeSwitch = mode => {
      cookies.set(cookie, mode)
      const doctypes = root.closest('.dict-edit')?.querySelector('.doctypes')
      doctypes?.classList.remove('laic', 'nerd')
      doctypes?.classList.add(mode)
   }
   docSpec.onchange = () => emit('dirty-change', true)
   if (!props.readonly) {
      docSpec.allowLayby = true
      docSpec.laybyMessage = 'This is your temporary lay-by for entry fragments. You can drag and drop XML elements here.'
      xrefs.extendDocspec(docSpec, xema)
   }
   const entry = 'entry_id' in props.entry ? { id: props.entry.entry_id } : props.entry
   subentries.extendDocspec(docSpec, xema, entry)
   try {
      custom?.adjustDocSpec?.(docSpec)
   } catch {
      emit('status', 'Failed to adjust the Xonomy document specification.', 'warn')
   }
   if (props.readonly) {
      for (const [name, spec] of Object.entries(elements)) {
         elements[name] = { ...spec, isReadOnly: true }
      }
      const unknown = docSpec.unknownElement
      docSpec.unknownElement = typeof unknown === 'function'
         ? name => ({ ...unknown(name), isReadOnly: true }) : { ...unknown, isReadOnly: true }
   }
   // Xonomy normalizes external specifications in render, despite the package signature.
   editor.render(props.initialXml, root, docSpec as XonomyDocSpec)
   captionEvents = new AbortController()
   function openCaption(event: Event) {
      if (!(event.target instanceof Element)) return
      const control = event.target.closest('.lexonomySubentryCaption, .lexonomyXrefsCaption')
      const target = control?.closest('.element')
      if (!control || !target?.id) return
      event.preventDefault()
      event.stopPropagation()
      if (control.classList.contains('lexonomySubentryCaption')) void subentries.menuSubentry(target.id)
      else xrefs.linkBox(target.id)
   }
   const listenerOptions = { signal: captionEvents.signal }
   root.addEventListener('click', openCaption, listenerOptions)
   root.addEventListener('keydown', event => {
      if (event.target instanceof Element && event.target.matches('.lexonomySubentryCaption, .lexonomyXrefsCaption') &&
          (event.key === 'Enter' || event.key === ' ')) event.stopPropagation()
   }, { ...listenerOptions, capture: true })
   editor.keyNav = true
   editor.keyboardEventCatcher = editor.$div.attr('tabindex', 0).on('keydown.lexonomyEditor', event => editor.key(event))
   const container = root.closest<HTMLElement>('#container')
   editor.scrollableContainer = container ? jquery(container) : null
})

onBeforeUnmount(() => {
   captionEvents?.abort()
   if (xonomy) {
      xonomy.destroyBubble()
      xonomy.$div?.off('.lexonomyEditor')
      jquery(document.body).off('click', xonomy.boundClickOff).off('dragend', xonomy.boundDragend)
   }
   restoreGlobals?.()
})
defineExpose({
   harvest() {
      if (customHarvester && element.value) return customHarvester(element.value)
      return xonomy?.harvest()
   }
})

function markCustomDirty() {
   if (customHarvester && !props.readonly) emit('dirty-change', true)
}

function readCustomEditor(source?: string): CustomEditor | undefined {
   if (!source) return
   try {
      return new Function('return ' + source)()
   } catch {
      emit('status', 'Invalid custom editor code.', 'warn')
   }
}

function readDocSpec(source?: string): XonomyDocSpecExternal | undefined {
   if (!source) return
   try {
      const spec = new Function('return (' + source + ')')() as XonomyDocSpecExternal
      return { ...spec, elements: { ...spec.elements } }
   } catch {
      emit('status', 'Invalid Xonomy document specification.', 'warn')
   }
}
</script>
