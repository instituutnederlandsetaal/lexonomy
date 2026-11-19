<template>
<div class="dict-config-xema-element">
   <div class="block">
      <div class="title">Element</div>
      <form @submit.prevent="rename">
         <input v-model="elementName" class="textbox tech elName" aria-label="Element name">
         <button v-if="canDelete" type="button" class="iconOnly iconCross" aria-label="Delete element" @click="emit('remove', elementId)">&nbsp;</button>
         <template v-if="elementName !== savedName">
            <button type="submit" class="butRename iconAccept" :disabled="!isValidXmlName(elementName) || conflictsWithSibling">Rename</button>
            <button type="button" class="butRenameCancel iconCancel" @click="elementName = savedName">Cancel renaming</button>
            <div v-if="!isValidXmlName(elementName)" class="warn">{{ elementName }} is not a valid XML name.</div>
            <div v-else-if="conflictsWithSibling" class="warn">A sibling element already has this name.</div>
         </template>
      </form>
   </div>

   <div class="block">
      <div class="title tight">Attributes</div>
      <table style="table-layout: auto;">
         <tbody>
            <tr v-for="[name, attribute] in sortedAttributes" :key="name">
               <td>
                  <button type="button" class="attribute-link" @click="emit('select', elementId, name)">
                     <span class="tech"><span class="ats">@</span><span class="att">{{ name }}</span></span>
                  </button>
               </td>
               <td>
                  <div style="display: flex; flex-wrap: wrap; align-items: center;">
                     <label v-for="option in optionalityChoices" :key="option" class="radio">
                        <input type="radio" :name="`optionality-${name}`" :value="option"
                           :checked="(attribute.optionality || 'optional') === option"
                           @change="updateAttribute(name, { ...attribute, optionality: option })">{{ option }}
                     </label>
                     <button type="button" class="iconOnly iconCross" :aria-label="`Delete attribute ${name}`" @click="removeAttribute(name)">&nbsp;</button>
                  </div>
               </td>
            </tr>
         </tbody>
      </table>
      <button v-if="!addingAttribute" type="button" class="butAtNewOpener iconAdd" @click="openAttribute">Add...</button>
      <form v-else @submit.prevent="addAttribute">
         <input ref="attributeInput" v-model="newAttributeName" class="textbox tech atName txtAtNew" aria-label="New attribute name">
         <button type="submit" class="butAtNew iconAccept" :disabled="!canAddAttribute">Add</button>
         <button type="button" class="butAtNewCancel iconCancel" @click="addingAttribute = false">Cancel</button>
         <div v-if="newAttributeName && !isValidXmlName(newAttributeName)" class="warn">Not a valid XML name.</div>
         <div v-else-if="Object.hasOwn(attributes, newAttributeName)" class="warn">This attribute already exists.</div>
      </form>
   </div>

   <div class="block">
      <div class="title">Content</div>
      <div v-for="option in fillingChoices" :key="option.value">
         <label class="radio">
            <input type="radio" name="filling" :value="option.value" :checked="filling === option.value"
               @change="apply({ filling: option.value })">{{ option.label }}
         </label>
      </div>
   </div>

   <XemaValues v-if="filling === 'lst'" :values="config.values" @update="values => apply({ values })"/>

   <div v-if="filling === 'inl' || filling === 'chd'" class="block">
      <div class="title tight">Child elements</div>
      <table v-if="children.length" style="table-layout: auto;">
         <tbody>
            <tr v-for="(child, index) in children" :key="`${child.name}-${index}`">
               <td>
                  <button type="button" class="attribute-link" @click="emit('select', child.name)">
                     <span class="tech">
                        <span class="brak">&lt;</span><span class="elm">{{ tagName(child.name) }}</span><span class="brak">&gt;</span>
                     </span>
                  </button>
               </td>
               <td style="white-space: nowrap;">
                  <label>min <input class="textbox min" placeholder="0" type="number" min="0" :value="child.min"
                     @change="setLimit(index, 'min', $event)"></label>
                  <label>max <input class="textbox max" placeholder="∞" type="number" min="0" :value="displayMaximum(child.max)"
                     @change="setLimit(index, 'max', $event)"></label>
               </td>
               <td style="white-space: nowrap;">
                  <button class="iconOnly iconArrowUp" type="button" aria-label="Move child up" :disabled="index === 0" @click="moveChild(index, -1)">&nbsp;</button>
                  <button class="iconOnly iconArrowDown" type="button" aria-label="Move child down" :disabled="index === children.length - 1" @click="moveChild(index, 1)">&nbsp;</button>
                  <button class="iconOnly iconCross" type="button" aria-label="Remove child" @click="deleteChild(index)">&nbsp;</button>
               </td>
               <td>
                  <button v-if="hasOtherParent(child.name)" type="button" style="padding: 5px; margin-left: 15px;"
                     @click="makeUnique(index)">Make unique</button>
                  <div v-if="alternativeOptions(child.name).length" style="display: inline-block; margin-left: 15px;">
                     <FormSelect v-model="replacement[child.name]" :options="alternativeOptions(child.name)"
                        placeholder="Choose another definition" aria-label="Alternative element definition"/>
                     <button type="button" :disabled="!replacement[child.name]" style="padding: 5px;"
                        @click="replaceChild(index)">Use instead</button>
                  </div>
               </td>
            </tr>
         </tbody>
      </table>

      <button v-if="!addingElement" type="button" class="butElNewOpener iconAdd" @click="openElement">Add...</button>
      <form v-else @submit.prevent="addChild">
         <input ref="elementInput" v-model="newChildName" class="textbox tech elName txtElNew" aria-label="New child element name">
         <button type="submit" class="butElNew iconAccept" :disabled="!canAddChild">Add</button>
         <button type="button" class="butElNewCancel iconCancel" @click="addingElement = false">Cancel</button>
         <div v-if="newChildName && !isValidXmlName(newChildName)" class="warn">Not a valid XML name.</div>
         <div v-else-if="childNameInUse" class="warn">This parent already has a child with that name.</div>
      </form>
   </div>
</div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { isValidXmlName } from '../../js/xml.ts'
import { maximumChildCount, xmlElementName, type Xema, type XemaAttribute, type XemaChild, type XemaElement, type XemaFilling } from '../../js/xema.ts'
import FormSelect from '../FormSelect.vue'
import XemaValues from './xema-values.vue'

const props = defineProps<{ config: XemaElement; elementId: string; xema: Xema }>()
const emit = defineEmits<{
   update: [id: string, config: XemaElement]
   remove: [id: string]
   select: [element: string, attribute?: string]
}>()

const fillingChoices: { value: XemaFilling; label: string }[] = [
   { value: 'chd', label: 'Child elements' },
   { value: 'txt', label: 'Text' },
   { value: 'inl', label: 'Text with markup' },
   { value: 'lst', label: 'Value from list' },
   { value: 'emp', label: 'Empty' },
   { value: 'med', label: 'Media' }
]
const optionalityChoices = ['optional', 'obligatory'] as const
const tagName = (id: string) => xmlElementName(props.xema, id)
const savedName = computed(() => tagName(props.elementId))
const elementName = ref(savedName.value)
const elements = computed(() => Object.entries(props.xema.elements))
const attributes = computed(() => props.config.attributes ?? {})
const sortedAttributes = computed(() => Object.entries(attributes.value).sort(([left], [right]) => left.localeCompare(right)))
const children = computed(() => props.config.children ?? [])
const filling = computed(() => props.config.filling ?? 'chd')
const canDelete = computed(() => elements.value.length > 1 &&
   !elements.value.some(([, element]) => element.children?.some(child => child.name === props.elementId)))
const conflictsWithSibling = computed(() => elements.value.some(([, parent]) =>
   parent.children?.some(child => child.name === props.elementId) &&
   parent.children.some(child => child.name !== props.elementId && tagName(child.name) === elementName.value)))

const addingAttribute = ref(false)
const newAttributeName = ref('')
const attributeInput = ref<HTMLInputElement>()
const canAddAttribute = computed(() => isValidXmlName(newAttributeName.value) && !Object.hasOwn(attributes.value, newAttributeName.value))

const addingElement = ref(false)
const newChildName = ref('')
const elementInput = ref<HTMLInputElement>()
const childNameInUse = computed(() => children.value.some(child => tagName(child.name) === tagName(newChildName.value)))
const canAddChild = computed(() => isValidXmlName(newChildName.value) && !childNameInUse.value)
const replacement = ref<Record<string, string>>(Object.create(null))

function apply(fields: Partial<XemaElement>) {
   emit('update', props.elementId, { ...props.config, ...fields })
}

function rename() {
   if (isValidXmlName(elementName.value) && !conflictsWithSibling.value && elementName.value !== savedName.value) {
      apply({ elementName: elementName.value })
   }
}

async function openAttribute() {
   addingAttribute.value = true
   newAttributeName.value = ''
   await nextTick()
   attributeInput.value?.focus()
}

function updateAttribute(name: string, value: XemaAttribute) {
   apply({ attributes: { ...attributes.value, [name]: value } })
}

function addAttribute() {
   if (!canAddAttribute.value) return
   updateAttribute(newAttributeName.value, { optionality: 'optional', filling: 'txt', values: [] })
   newAttributeName.value = ''
}

function removeAttribute(name: string) {
   const remaining = { ...attributes.value }
   delete remaining[name]
   apply({ attributes: remaining })
}

async function openElement() {
   addingElement.value = true
   newChildName.value = ''
   await nextTick()
   elementInput.value?.focus()
}

function addChild() {
   if (!canAddChild.value) return
   const name = newChildName.value
   if (!Object.hasOwn(props.xema.elements, name)) {
      emit('update', name, { elementName: name, filling: 'emp', attributes: {}, children: [] })
   }
   apply({ children: [...children.value, { name, min: 0, max: null }] })
   newChildName.value = ''
}

function hasOtherParent(id: string) {
   return elements.value.some(([key, value]) => key !== props.elementId && value.children?.some(child => child.name === id))
}

function displayMaximum(value: XemaChild['max']) {
   const max = maximumChildCount(value)
   return Number.isFinite(max) ? max : ''
}

function setLimit(index: number, name: 'min' | 'max', event: Event) {
   if (!(event.target instanceof HTMLInputElement)) return
   const child = children.value[index]
   const number = event.target.valueAsNumber
   const value = event.target.value === '' ? (name === 'min' ? 0 : null) : number
   const min = name === 'min' ? Number(value) : Number(child.min || 0)
   const max = name === 'max' ? value : child.max
   if ((value !== null && (!Number.isSafeInteger(value) || value < 0)) ||
       min > maximumChildCount(max)) {
      event.target.value = String(name === 'max' ? displayMaximum(child.max) : child.min)
      return
   }
   const updated: XemaChild = name === 'min' ? { ...child, min } : { ...child, max: value }
   apply({ children: children.value.map((item, row) => index === row ? updated : item) })
}

function moveChild(index: number, direction: 1 | -1) {
   const list = [...children.value]
   const next = index + direction
   if (next < 0 || next >= list.length) return
   const [child] = list.splice(index, 1)
   list.splice(next, 0, child)
   apply({ children: list })
}

function deleteChild(index: number) {
   const id = children.value[index].name
   apply({ children: children.value.filter((_, row) => row !== index) })
   if (id !== props.elementId && !hasOtherParent(id)) emit('remove', id)
}

function alternativeOptions(id: string) {
   return elements.value.filter(([other]) => other !== id && tagName(other) === tagName(id))
      .map(([value]) => {
         const parent = elements.value.find(([, element]) => element.children?.some(child => child.name === value))
         return { value, label: parent ? `${tagName(parent[0])}/${tagName(value)} (${value})` : value }
      })
}

function setChild(index: number, name: string) {
   apply({ children: children.value.map((item, row) => index === row ? { ...item, name } : item) })
}

function makeUnique(index: number) {
   const id = children.value[index].name
   const source = props.xema.elements[id]
   if (!source) return
   let number = 0
   while (Object.hasOwn(props.xema.elements, id + number)) number++
   const uniqueId = id + number
   const copy = JSON.parse(JSON.stringify(source)) as XemaElement
   emit('update', uniqueId, { ...copy, elementName: tagName(id) })
   setChild(index, uniqueId)
}

function replaceChild(index: number) {
   const id = children.value[index].name
   const selected = replacement.value[id]
   if (!selected || !alternativeOptions(id).some(option => option.value === selected)) return
   setChild(index, selected)
   delete replacement.value[id]
   if (id !== props.elementId && !hasOtherParent(id)) emit('remove', id)
}
</script>

<style>
.dict-config-xema-element .attribute-link {
   border: 0;
   background: transparent;
   padding: 0;
   cursor: pointer;
}
.dict-config-xema-element .textbox.min, .dict-config-xema-element .textbox.max {
   min-width: 3em;
}
</style>
