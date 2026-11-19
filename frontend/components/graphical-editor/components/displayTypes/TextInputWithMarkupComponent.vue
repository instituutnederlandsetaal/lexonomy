<template>
   <div>
      <section v-if="elementData.shown && !readOnly" class="input-section">
         <div ref="input" class="text-with-markup">
            <span v-for="segment in segments" :key="segment.index" :data-index="segment.index"
                  :class="segment.name ? 'dynamic-element' : 'text-element'"
                  :style="styles(segment.name)" :role="segment.editable ? 'textbox' : undefined"
                  :aria-label="segment.editable ? xmlName : undefined"
                  :contenteditable="segment.editable ? 'plaintext-only' : false"
                  v-sync-text="segment.text" @input="updateValue(segment, $event)"
                  @focusout="rememberSelection"/>
         </div>
         <DropdownMenuRoot v-if="markupChoices.length" :modal="false">
            <DropdownMenuTrigger type="button" class="secondary mark-as" :disabled="editorLocked"
                                 @pointerdown="rememberSelection" @keydown.enter="rememberSelection"
                                 @keydown.space="rememberSelection">Mark as</DropdownMenuTrigger>
            <DropdownMenuPortal>
               <DropdownMenuContent class="graphical-action-menu" :inert="editorLocked" align="start" :side-offset="4" :collision-padding="8">
                  <DropdownMenuItem @select="markSelection('')">text</DropdownMenuItem>
                  <DropdownMenuItem v-for="choice in markupChoices" :key="choice" :style="styles(choice)" @select="markSelection(choice)">
                     {{ xmlElementName(xema, choice) }}
                  </DropdownMenuItem>
               </DropdownMenuContent>
            </DropdownMenuPortal>
         </DropdownMenuRoot>
      </section>
      <section v-else-if="elementData.shown" class="read-only">
         <p v-if="showPreview" class="text--xs">{{ xmlName }}: </p>
         <span :class="showPreview ? 'text--xs' : 'text--md'">
            <span v-for="segment in segments" :key="segment.index" :style="styles(segment.name)">{{ segment.text }}</span>
         </span>
      </section>
   </div>
</template>

<script setup lang="ts">
import { editorLockedKey, editorContextKey } from '../../editor-context.ts'
import { computed, inject, ref, type CSSProperties, type Directive } from 'vue'
import type { Element } from 'xml-js'
import { DropdownMenuContent, DropdownMenuItem, DropdownMenuPortal, DropdownMenuRoot, DropdownMenuTrigger } from 'reka-ui'
import { xemaElementId, xmlElementName } from '../../../../js/xema.ts'
import { readFormattingFields } from '../../../../js/xemplate.ts'
import type { EditorChild, ElementDisplay } from '../../editor-schema.ts'

const props = defineProps<{
   elementData: ElementDisplay
   elementName: string
   content: Element[]
   children?: EditorChild[]
   showPreview?: boolean
}>()
const emit = defineEmits<{ input: [change: { elementName: string; elements: Element[] }] }>()
const editor = inject(editorContextKey)!
const editorLocked = inject(editorLockedKey)!
const xema = computed(() => editor.config.xema)
const input = ref<HTMLElement | null>(null)
const xmlName = computed(() => xmlElementName(xema.value, props.elementName))
const readOnly = computed(() => props.elementData.readOnly || props.showPreview)
const markupChoices = computed(() => (props.children ?? []).filter(child => !child.isAttribute).map(child => child.name))
type Segment = { index: number; node?: Element; name?: string; text: string; editable: boolean }
type Selection = { index: number; start: number; end: number; text: string }
let selection: Selection | undefined

const segments = computed<Segment[]>(() => {
   if (!props.content.length) return [{ index: 0, text: '', editable: true }]
   return props.content.flatMap((node, index) => {
      const simple = (node.elements?.length ?? 0) <= 1 && (node.elements?.every(child => child.type === 'text') ?? true)
      if (node.type === 'text' || node.type === 'element' || node.type === 'cdata') {
         return [{ index, node, text: nodeText(node), editable: node.type === 'text' || (node.type === 'element' && simple),
            name: node.name ? xemaElementId(xema.value, node.name, props.elementName) : undefined }]
      }
      return []
   })
})

const vSyncText: Directive<HTMLElement, string> = {
   mounted(el, { value }) { el.textContent = value },
   updated(el, { value }) { if (el.textContent !== value) el.textContent = value }
}

function nodeText(node: Element): string {
   return String(node.text ?? node.cdata ?? node.elements?.map(nodeText).join('') ?? '')
}

function styles(name?: string): CSSProperties {
   const id = name ?? props.elementName
   const { background, colour, slant, weight } = readFormattingFields(editor.config.xemplate, id, xmlElementName(xema.value, id))
   return { backgroundColor: background, color: colour, borderColor: colour, fontStyle: slant, fontWeight: weight }
}

function updateValue(segment: Segment, event: Event) {
   const text = (event.currentTarget as HTMLElement).textContent ?? ''
   if (text === segment.text) return
   const updated = segment.node?.type === 'element'
      ? { ...segment.node, elements: text ? [{ type: 'text', text }] : [] }
      : { type: 'text', text }
   const elements = [...props.content]
   elements.splice(segment.index, segment.node ? 1 : 0, updated)
   emit('input', { elementName: props.elementName, elements })
}

function rememberSelection() {
   const current = window.getSelection()
   if (!current?.rangeCount || current.isCollapsed) return
   const range = current.getRangeAt(0)
   const startParent = range.startContainer instanceof HTMLElement ? range.startContainer : range.startContainer.parentElement
   const field = startParent?.closest<HTMLElement>('span[data-index]')
   if (!field || !input.value?.contains(field) || !field.contains(range.endContainer)) return
   const index = Number(field.dataset.index)
   const segment = segments.value.find(item => item.index === index)
   if (!segment?.editable || Object.keys(segment.node?.attributes ?? {}).length) return
   const before = range.cloneRange()
   before.selectNodeContents(field)
   before.setEnd(range.startContainer, range.startOffset)
   const start = before.toString().length
   selection = { index, start, end: start + range.toString().length, text: field.textContent ?? '' }
}

function markSelection(mark: string) {
   const saved = selection
   selection = undefined
   if (!saved) return
   const segment = segments.value.find(item => item.index === saved.index)
   if (!segment?.editable || segment.text !== saved.text || !segment.node) return
   const previousName = segment.node.name
   const chosenName = mark ? xmlElementName(xema.value, mark) : undefined
   const parts: [string, string | undefined][] = [
      [saved.text.slice(0, saved.start), previousName],
      [saved.text.slice(saved.start, saved.end), chosenName],
      [saved.text.slice(saved.end), previousName],
   ]
   const replacement = parts.filter(([text]) => text !== '').map(([text, name]): Element =>
      name ? { type: 'element', name, elements: [{ type: 'text', text }] } : { type: 'text', text })
   const elements = [...props.content]
   elements.splice(saved.index, 1, ...replacement)
   emit('input', { elementName: props.elementName, elements })
}
</script>

<style scoped>
.text-with-markup { font-style: normal; text-align: left; }
.text-with-markup span,
.read-only span { white-space: pre-wrap; }
.text-with-markup span[contenteditable="plaintext-only"] {
   display: inline;
   padding: 5px 1px;
   border-radius: 0;
   line-height: 24px;
}
.text-with-markup span[contenteditable="plaintext-only"]:hover,
.text-with-markup span[contenteditable="plaintext-only"]:focus {
   padding: 4px 0;
   border: 1px solid;
}
.text-with-markup span[contenteditable="plaintext-only"]:empty { padding: 4px 16px; }
.input-section { display: flex; align-items: center; }
.mark-as { width: 85px; margin-left: 8px; }
</style>
