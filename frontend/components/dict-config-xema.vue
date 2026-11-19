<template>
<div class="dict-config-xema">
   <LoadingOverlay v-if="loading || saving"/>
   <DictNav :links="[['config', 'Configure'], ['config-xema', 'Entry structure']]"/>
   <h1>Entry structure</h1>

   <template v-if="ready && draft">
      <DictConfigButtons :dict-id="dictId" :save-data="saveData" :disabled="saving">
         <button type="button" class="btn waves-effect waves-light" @click="override = !override">
            {{ override ? 'Stop using your own schema' : 'Use your own schema' }}
            <i class="material-symbols-outlined right">edit</i>
         </button>
      </DictConfigButtons>

      <div v-if="!override" id="editor" class="editor designer">
         <div class="list">
            <DictConfigElementInTree v-for="root in roots"
               :key="root"
               :id="root"
               :xema="draft"
               :current-element="currentElement"
               :current-attribute="currentAttribute"
               @select="select"
            />
         </div>
         <div class="details">
            <DictConfigXemaElement v-if="currentElement && selectedElement && !currentAttribute"
               :key="currentElement"
               :element-id="currentElement"
               :xema="draft"
               :config="selectedElement"
               @update="updateElement"
               @select="select"
               @remove="removeElement"
            />
            <DictConfigXemaAttribute v-if="currentElement && currentAttribute && selectedAttribute && selectedElement?.attributes"
               :key="`${currentElement}/${currentAttribute}`"
               :attribute-id="currentAttribute"
               :attributes="selectedElement.attributes"
               :config="selectedAttribute"
               @update="updateAttribute"
               @rename="renameAttribute"
            />
         </div>
      </div>

      <div v-else>
         <div class="row">
            <div class="col s10">
               <p>To specify your custom Lexonomy schema use either <i>Xonomy Document Specification</i>, or <i>DTD</i>.</p>
               <h3>Xonomy Document Specification</h3>
               <p>A <a href="http://www.lexiconista.com/xonomy/" target="_blank">Xonomy Document Specification</a> is a JavaScript object which configures the Xonomy XML editor used in Lexonomy.</p>
            </div>
         </div>
         <div class="row">
            <div class="input-field col s10">
               <textarea id="editor_doc" rows="6" class="materialize-textarea" placeholder="" v-model="draft._xonomyDocSpec"></textarea>
               <label class="active" for="editor_doc">Document specification</label>
               <span class="helper-text">Xonomy Document Specification. If you would like to see an example, <button type="button" class="btn-flat" @click="exampleDoc">click here to load a sample specification</button>.</span>
            </div>
         </div>
         <div class="row">
            <div class="input-field col s10">
               <textarea id="editor_xml" rows="6" class="materialize-textarea" placeholder="" v-model="draft._newXml"></textarea>
               <label class="active" for="editor_xml">Template for new entries</label>
               <span class="helper-text">XML template for newly created entries. If you would like to see an example, <button type="button" class="btn-flat" @click="exampleXML">click here to load a sample XML template</button>.</span>
            </div>
         </div>
         <div class="row">
            <div class="col s10">
               <h3>DTD (Document Type Definition)</h3>
               <p><a href="https://en.wikipedia.org/wiki/Document_type_definition" target="_blank">Document Type Definitions</a> are a popular formalism for defining the structure of XML documents.</p>
            </div>
         </div>
         <div class="row">
            <div class="input-field col s10">
               <textarea id="editor_dtd" rows="6" class="materialize-textarea" placeholder="" v-model="draft._dtd"></textarea>
               <label class="active" for="editor_dtd">Your DTD</label>
               <span class="helper-text">If you would like to see an example, <button type="button" class="btn-flat" @click="exampleDTD">click here to load a sample DTD</button>.</span>
            </div>
         </div>
      </div>

   </template>
   <p v-else-if="!loading">Settings could not be loaded. <button class="btn-flat" type="button" @click="load">Retry</button></p>
</div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import '../widgets/xema-designer.css'
import { isValidXmlName } from '../js/xml.ts'
import { type Xema, type XemaAttribute, type XemaElement } from '../js/xema.ts'
import { useDictionarySetting } from '../js/use-dictionary-setting.ts'
import DictConfigButtons from './dict-config-buttons.vue'
import DictConfigElementInTree from './dict-config-element-in-tree.vue'
import DictConfigXemaAttribute from './entry-structure/dict-config-xema-attribute.vue'
import DictConfigXemaElement from './entry-structure/dict-config-xema-element.vue'
import DictNav from './dict-nav.vue'
import LoadingOverlay from './loading-overlay.vue'
import { treeRoots } from './entry-structure/tree-roots.ts'

const props = defineProps<{ dictId: string }>()
const draft = ref<Xema>()
const currentElement = ref<string>()
const currentAttribute = ref<string>()
const override = ref(false)
const { loading, ready, saving, load, save } = useDictionarySetting(() => props.dictId, 'xema', content => {
   draft.value = { ...content, _newXml: content._newXml ?? content.newXml }
   currentElement.value = treeRoots(content)[0]
   currentAttribute.value = undefined
   override.value = Boolean(content._xonomyDocSpec || content._dtd || content._newXml || content.newXml)
})
const roots = computed(() => treeRoots(draft.value))
const selectedElement = computed(() => currentElement.value ? draft.value?.elements[currentElement.value] : undefined)
const selectedAttribute = computed(() => currentAttribute.value ? selectedElement.value?.attributes?.[currentAttribute.value] : undefined)

function select(element: string, attribute?: string) {
   if (!draft.value || !Object.hasOwn(draft.value.elements, element)) return
   currentElement.value = element
   currentAttribute.value = attribute
}

function updateElement(id: string, config: XemaElement) {
   if (draft.value) draft.value.elements = { ...draft.value.elements, [id]: config }
}

function removeElement(id: string) {
   const xema = draft.value
   if (!xema || Object.keys(xema.elements).length <= 1) return
   if (Object.values(xema.elements).some(element => element.children?.some(child => child.name === id))) return
   delete xema.elements[id]
   if (xema.root === id) xema.root = treeRoots(xema)[0]
   if (currentElement.value === id) select(xema.root)
}

function updateAttribute(config: XemaAttribute) {
   const id = currentElement.value
   const name = currentAttribute.value
   if (id && name && selectedElement.value) {
      updateElement(id, { ...selectedElement.value, attributes: { ...selectedElement.value.attributes, [name]: config } })
   }
}

function renameAttribute(name: string) {
   const id = currentElement.value
   const previous = currentAttribute.value
   const element = selectedElement.value
   if (!id || !previous || !element?.attributes || !isValidXmlName(name) || Object.hasOwn(element.attributes, name)) return
   const attributes = { ...element.attributes, [name]: element.attributes[previous] }
   delete attributes[previous]
   updateElement(id, { ...element, attributes })
   currentAttribute.value = name
}

function saveData() {
   const xema = draft.value
   if (!xema) return
   const { _xonomyDocSpec, _newXml, _dtd, newXml: _legacy, ...structure } = xema
   structure.root = Object.hasOwn(xema.elements, xema.root) ? xema.root : roots.value[0] ?? xema.root
   return save(override.value ? { ...structure, _xonomyDocSpec, _newXml, _dtd } : structure)
}

function exampleDoc() {
   if (draft.value) draft.value._xonomyDocSpec = JSON.stringify({ elements: { entry: {}, headword: { hasText: true } } }, undefined, 2)
}
function exampleXML() {
   if (draft.value) draft.value._newXml = '<entry><headword></headword></entry>'
}
function exampleDTD() {
   if (draft.value) draft.value._dtd = '<!ELEMENT entry (headword)>\n<!ELEMENT headword (#PCDATA)>'
}
</script>

<style>
.dict-config-xema #editor {
   position: relative !important;
   min-height: 750px;
   display: flex;
   flex-wrap: nowrap;
}
.dict-config-xema #editor .details {flex-grow: 1; overflow: hidden; max-width: 100%;}

.dict-config-xema .editor .list { flex-basis: 0; }

.dict-config-xema #editor.designer input.textbox.cap {
   width: 15em !important;
}
.dict-config-xema #editor.designer input[type=radio] {
   opacity: 1 !important;
}
.dict-config-xema {
   display: block;
}
</style>
