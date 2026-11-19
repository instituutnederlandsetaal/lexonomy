import { computed, inject, ref, shallowRef, type Component } from 'vue'
import type { Attributes, Element } from 'xml-js'
import { editorContextKey, useEditorDraft } from './editor-context.ts'
import { emptyElement, updateValueChildren, valueInputKind, type EditorChild, type ElementDisplay, type ParentCandidate } from './editor-schema.ts'
import type { XemaFilling } from '../../js/xema.ts'
import DropdownComponent from './components/displayTypes/DropdownComponent.vue'
import MediaComponent from './components/displayTypes/MediaComponent.vue'
import ReadOnlyComponent from './components/displayTypes/ReadOnlyComponent.vue'
import TextInputComponent from './components/displayTypes/TextInputComponent.vue'
import TextInputWithMarkupComponent from './components/displayTypes/TextInputWithMarkupComponent.vue'

export type EditorFieldProps = {
   children?: EditorChild[]
   elementData: ElementDisplay
   elementName: string
   parentElementName?: string
   numberOfElements: number
   content: Element
   editorChildNumber: number
   isAttribute?: boolean
   showElementsPreview?: boolean
}

export type FieldUpdate = { elementName: string; editorChildNumber: number; content: Element; isAttribute?: false }
   | { isAttribute: true; content: Attributes }
export type NewElement = { name: string; content?: Element }
export type ElementPosition = { name: string; position: number }

export type EmitField = {
   (event: 'input', update: FieldUpdate): void
   (event: 'create-element', element: NewElement | NewElement[]): void
   (event: 'move-element', element: ElementPosition & { direction: number }): void
   (event: 'delete-element', element: ElementPosition): void
}

export function useFieldActions(props: EditorFieldProps, emit: EmitField) {
   const draft = useEditorDraft()
   const newPossibleParents = shallowRef<ParentCandidate[]>([])
   const showSelectNewParent = ref(false)
   const position = () => ({ name: props.elementName, position: props.editorChildNumber })
   const actions = {
      'move-element-down': () => emit('move-element', { ...position(), direction: 1 }),
      'move-element-up': () => emit('move-element', { ...position(), direction: -1 }),
      'add-element': () => emit('create-element', { name: props.elementName }),
      'remove-element': () => emit('delete-element', position()),
      'clone-element': () => emit('create-element', { name: props.elementName, content: props.content }),
      'select-new-parent': () => {
         newPossibleParents.value = draft.moveParents(props.content, props.elementName)
         showSelectNewParent.value = true
      }
   }

   function handleSelectedNewParent(candidate: ParentCandidate) {
      draft.move(props.content, props.elementName, candidate.node)
   }
   return { actions, newPossibleParents, showSelectNewParent, handleSelectedNewParent }
}

const valueComponents: Record<XemaFilling, Component> = {
   chd: ReadOnlyComponent, emp: ReadOnlyComponent, txt: TextInputComponent,
   lst: DropdownComponent, med: MediaComponent, inl: TextInputWithMarkupComponent
}

export type ValueUpdate = { attributes?: Attributes; elements?: Element[] }

export function useFieldValue(props: EditorFieldProps, emit: EmitField, content = () => props.content) {
   const editor = inject(editorContextKey)!
   const xema = computed(() => editor.config.xema)
   const valueKind = computed(() => valueInputKind(xema.value, content(), props.elementName, props.parentElementName, props.isAttribute))
   const valueComponent = computed(() => valueComponents[valueKind.value])
   const showChildren = computed(() => valueKind.value !== 'inl')
   const componentData = computed(() => {
      const node = content()
      if (!showChildren.value) return node.elements ?? []
      if (props.isAttribute) return node
      return node.elements?.find(element => element.type === 'text') ?? { text: '', type: 'text' }
   })

   function updateValue(node: Element, data: ValueUpdate): Element {
      return props.isAttribute ? { ...node, text: data.attributes?.[props.elementName] }
         : updateValueChildren(node, data.elements ?? [], !showChildren.value)
   }

   function commitContent(node: Element) {
      if (props.isAttribute) {
         const value = typeof node.text === 'boolean' ? String(node.text) : node.text
         emit('input', { isAttribute: true, content: { [props.elementName]: value } })
         return
      }
      emit('input', { elementName: props.elementName, editorChildNumber: props.editorChildNumber,
         content: { ...emptyElement(xema.value, props.elementName), ...node } })
   }

   return { componentData, valueComponent, showChildren, updateValue, commitContent }
}
