<template>
   <div>
      <ul v-for="group in renderedChildren" :key="group.key">
         <component v-for="field in group.fields" :is="field.component"
                    :key="field.key"
                    v-bind="field.props"
                    :class="{ 'is-attribute': field.props.isAttribute }"
                    style="display: list-item"
                    @input="updateField"
                    @create-element="createElements"
                    @move-element="moveElement"
                    @delete-element="deleteElement"/>
      </ul>
   </div>
</template>

<script setup lang="ts">
import { editorContextKey, schemaAncestorsKey } from '../editor-context.ts'
import { computed, inject, provide, type Component } from 'vue'
import type { Element } from 'xml-js'
import { childrenFor, elementDisplay, elementId, emptyElement, type EditorChild } from '../editor-schema.ts'
import type { ElementPosition, FieldUpdate, NewElement } from '../use-editor-field.ts'
import InlineComponent from './displayTypes/InlineComponent.vue'
import PopupComponent from './displayTypes/PopupComponent.vue'
import SubentryComponent from './displayTypes/SubentryComponent.vue'

const props = withDefaults(defineProps<{
   children?: EditorChild[]
   elementName?: string
   content: Element
   showElementsPreview?: boolean
   maxDisplayedChildren?: number
   hideEmptyElements?: boolean
}>(), { maxDisplayedChildren: -1 })
const emit = defineEmits<{ input: [value: { content: Element }] }>()
const editor = inject(editorContextKey)!
const config = computed(() => editor.config)
const xema = computed(() => config.value.xema)
const ancestors = inject(schemaAncestorsKey)
const lineage = computed(() => [...(ancestors?.value ?? []), ...(props.elementName ? [props.elementName] : [])])
provide(schemaAncestorsKey, lineage)

const renderedChildren = computed(() => {
   let remaining = props.maxDisplayedChildren
   const children = props.children ?? (props.elementName ? childrenFor(xema.value, props.elementName, props.content) : [])
   return children.flatMap(child => {
      if (remaining === 0) return []
      const elementName = child.name
      const elementData = elementDisplay(config.value.xemplate, xema.value, elementName, props.elementName, child.isAttribute)
      const attributes = props.content.attributes
      const matches = child.isAttribute
         ? [{ type: 'attribute', name: elementName, text: attributes?.[elementName] }]
         : (props.content.elements ?? []).filter(node => elementId(xema.value, node, props.elementName) === elementName)
      const component: Component = props.showElementsPreview || child.isAttribute
         ? InlineComponent
         : config.value.subbing[elementName] && xema.value.root !== elementName
            ? SubentryComponent
            : elementData.displayType === 'popup' ? PopupComponent : InlineComponent
      let content = matches.length ? matches : [emptyElement(xema.value, elementName)]
      if (remaining > 0) {
         content = content.slice(0, remaining)
         if (elementData.shown) remaining -= content.length
      }
      const key = `${child.isAttribute ? '@' : ''}${elementName}`
      return [{
         key,
         fields: content.map((node: Element, index) => ({
            key: index,
            component,
            props: {
               elementName,
               children: child.isAttribute || (!matches.length && lineage.value.includes(elementName))
                  ? [] : childrenFor(xema.value, elementName, node),
               content: node,
               elementData,
               editorChildNumber: index,
               parentElementName: props.elementName,
               numberOfElements: matches.length,
               isAttribute: child.isAttribute ?? false,
               showElementsPreview: props.showElementsPreview,
               hideEmptyElements: props.hideEmptyElements,
               maxDisplayedChildren: props.maxDisplayedChildren
            }
         }))
      }]
   })
})

function findSiblingIndexes(name: string) {
   return (props.content.elements ?? []).flatMap((element, index) =>
      elementId(xema.value, element, props.elementName) === name ? [index] : [])
}

function updateField(update: FieldUpdate) {
   if (update.isAttribute) {
      emit('input', { content: { ...props.content, attributes: { ...props.content.attributes, ...update.content } } })
      return
   }
   const positions = findSiblingIndexes(update.elementName)
   const elements = [...(props.content.elements ?? [])]
   const target = positions[update.editorChildNumber]
   if (target === undefined) {
      elements.splice((positions.at(-1) ?? elements.length - 1) + 1, 0, update.content)
   } else {
      elements[target] = update.content
   }
   emit('input', { content: { ...props.content, elements } })
}

function createElements(input: NewElement | NewElement[]) {
   const elements = [...(props.content.elements ?? [])]
   for (const { name, content } of Array.isArray(input) ? input : [input]) {
      const indexes = elements.flatMap((element, index) =>
         elementId(xema.value, element, props.elementName) === name ? [index] : [])
      const addition = content ? JSON.parse(JSON.stringify(content)) as Element : emptyElement(xema.value, name)
      elements.splice((indexes.at(-1) ?? elements.length - 1) + 1, 0, addition)
   }
   emit('input', { content: { ...props.content, elements } })
}

function moveElement({ name, position, direction }: ElementPosition & { direction: number }) {
   const positions = findSiblingIndexes(name)
   const from = positions[position], to = positions[position + direction]
   if (from === undefined || to === undefined || !props.content.elements) return
   const elements = [...props.content.elements]
   ;[elements[from], elements[to]] = [elements[to], elements[from]]
   emit('input', { content: { ...props.content, elements } })
}

function deleteElement({ name, position }: ElementPosition) {
   const index = findSiblingIndexes(name)[position]
   if (index === undefined || !props.content.elements) return
   emit('input', { content: { ...props.content, elements: props.content.elements.filter((_, row) => row !== index) } })
}
</script>

<style lang="scss" scoped>
.is-attribute {
  padding: 0 !important;
  padding-left: 4px !important;
  margin: 0;
}
</style>
