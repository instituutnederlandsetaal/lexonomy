<template>
<dict-config-xema>
   <LoadingOverlay v-if="state.isLoading || state.isSaving"/>
   <DictNav :links="[['config', 'Configure'], ['config-xema', 'Entry structure']]"/>

   <h1>Entry structure</h1>
   <div v-if="state.isLoading">Loading...</div>

   <template v-if="state.xema">
      <DictConfigButtons :save-data="saveData">
         <button class="btn waves-effect waves-light" @click="toggleOverride" > {{ state.override ? 'Stop using your own schema' : 'Use your own schema' }} <i class="material-symbols-outlined right">edit</i></button>
      </DictConfigButtons>

      <div v-if="!state.override" id="editor" class="editor designer">
         <div class="list">
            <DictConfigElementInTree v-for="root in roots"
               :key="root.id"
               :depth="0"
               :data="root"
               :xema="state.xema"
               :current-element="state.currentElement"
               :current-attribute="state.currentAttribute"
               :selectElementOrAttribute="selectElementOrAttribute"
            />
         </div>
         <div class="details">
            <DictConfigXemaElement v-if="state.currentElement && !state.currentAttribute"
               :key="state.currentElement"
               :elementId="state.currentElement"
               :xema="state.xema"
               :config="state.xema.elements[state.currentElement]"
               :apply-config="onXemaElementUpdated"
               :createElement="onXemaElementUpdated"
               :selectElementOrAttribute="selectElementOrAttribute"
               :remove-element="onXemaElementDeleted"
            />

            <DictConfigXemaAttribute v-if="state.currentElement && state.currentAttribute"
               :key="`${state.currentElement}/${state.currentAttribute}`"
               :elementId="state.currentElement"
               :attributeId="state.currentAttribute"
               :xema="state.xema"
               :config="state.xema.elements[state.currentElement].attributes[state.currentAttribute]"

               :apply-config="onXemaAttributeUpdated"
               :renameAttribute="onXemaAttributeRenamed"
            />
         </div>
      </div>

      <div v-if="state.override">
         <div class="row">
            <div class="col s10">
               <p>To specify your custom Lexonomy schema use either <i>Xonomy Document Specification</i>, or <i>DTD</i>.</p>
               <h3>Xonomy Document Specification</h3>
               <p>A <a href="http://www.lexiconista.com/xonomy/" target="_blank">Xonomy Document Specification</a> is a JavaScript object which configures the Xonomy XML editor used in Lexonomy.</p>
            </div>
         </div>
         <div class="row">
            <div class="input-field col s10">
               <textarea id="editor_doc" class="materialize-textarea" placeholder="" v-model="state.xema._xonomyDocSpec"></textarea>
               <label for="editor_doc">Document specification</label>
               <span class="helper-text">Xonomy Document Specification. If you would like to see an example, <a @click="exampleDoc">click here to load a sample specification</a>.</span>
            </div>
         </div>
         <div class="row">
            <div class="input-field col s10">
               <textarea id="editor_xml" class="materialize-textarea" placeholder="" v-model="state.xema._newXml"></textarea>
               <label for="editor_xml">Template for new entries</label>
               <span class="helper-text">XML template for newly created entries. If you would like to see an example, <a @click="exampleXML">click here to load a sample XML template</a>.</span>
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
               <textarea id="editor_dtd" class="materialize-textarea" placeholder="" v-model="state.xema._dtd"></textarea>
               <label for="editor_dtd">Your DTD</label>
               <span class="helper-text">If you would like to see an example, <a @click="exampleDTD">click here to load a sample DTD</a>.</span>
            </div>
         </div>
      </div>

   </template>
</dict-config-xema>
</template>

<script>
import Materialize from '../libs/materialize/materialize.min.js'
import '../widgets/xema-designer.css'
import { dictionaryWorkspace } from '../js/dictionary-workspace.ts'
import DictConfigButtons from './dict-config-buttons.vue'
import DictConfigElementInTree from './dict-config-element-in-tree.vue'
import DictConfigXemaAttribute from './entry-structure/dict-config-xema-attribute.vue'
import DictConfigXemaElement from './entry-structure/dict-config-xema-element.vue'
import DictNav from './dict-nav.vue'
import LoadingOverlay from './loading-overlay.vue'
import { treeRoots } from './entry-structure/tree-roots.js'

export default {
   components: { DictConfigButtons, DictConfigElementInTree, DictConfigXemaAttribute, DictConfigXemaElement, DictNav, LoadingOverlay },
   data() {
      return {
         state: {
            isLoading: true,
            isSaving: false,
            override: false,
            currentElement: null, // initialize in beforeMount
            currentAttribute: null,
            xema: undefined, // initialized in beforeMount
         }
      }
   },

   async mounted() {
      const response = await dictionaryWorkspace.loadDictionaryConfig('xema')
      if (response) {
         const { content } = response
         this.state.xema = content
         this.state.override = Boolean(content._xonomyDocSpec || content._dtd)
         this.state.currentElement = content.root
         if (this.state.override) this.$nextTick(this.resizeFields)
      }
      this.state.isLoading = false
   },

   computed: {
      roots() {
         return treeRoots(this.state.xema)
      }
   },

   methods: {
      resizeFields() {
         Materialize.updateTextFields()
         this.$el.querySelectorAll('#editor_doc, #editor_xml, #editor_dtd').forEach(field => Materialize.textareaAutoResize(field))
      },

      toggleOverride() {
         this.state.override = !this.state.override
         if (this.state.override) {
            this.$nextTick(this.resizeFields)
         } else {
            delete this.state.xema._xonomyDocSpec
            delete this.state.xema._dtd
            delete this.state.xema._newXml
         }
      },

      getConfigData() {
         const xema = this.state.xema
         const data = {elements: xema.elements, root: this.roots[0]?.id || 'entry'}
         if (this.state.override) {
            for (const key of ['_xonomyDocSpec', '_newXml', '_dtd']) {
               if (xema[key]) data[key] = xema[key]
            }
         }
         return data
      },

      async saveData() {
         this.state.isSaving = true
         await dictionaryWorkspace.updateDictionaryConfig("xema", this.getConfigData())
         this.state.isSaving = false
      },

      selectElementOrAttribute(currentElement, currentAttribute) {
         this.state.currentElement = currentElement;
         this.state.currentAttribute = currentAttribute;

      },

      onXemaElementUpdated(id, newConfig) {
         this.state.xema.elements[id] = newConfig;

      },

      onXemaElementDeleted(id) {
         // check it's not used anywhere, and only delete if it isn't
         if (!Object.values(this.state.xema.elements).some(el => el.children?.some(c => c.name === id))) {
            delete this.state.xema.elements[id];
            if (this.state.currentElement === id)  {
               this.state.currentElement = undefined
               this.state.currentAttribute = undefined
            }
         }
      },

      onXemaAttributeUpdated(newConfig) {
         const el = this.state.xema.elements[this.state.currentElement];
         el.attributes[this.state.currentAttribute] = newConfig;

      },

      onXemaAttributeRenamed(newName) {
         const el = this.state.xema.elements[this.state.currentElement];
         el.attributes[newName] = el.attributes[this.state.currentAttribute];
         delete el.attributes[this.state.currentAttribute];
         this.state.currentAttribute = newName;

      },

      exampleDoc() {
         this.state.xema._xonomyDocSpec = JSON.stringify({ elements: { "entry": {}, "headword": {hasText: true} }}, undefined, 2);
         this.$nextTick(this.resizeFields)
      },

      exampleXML() {
         this.state.xema._newXml = `<entry><headword></headword></entry>`;
         this.$nextTick(this.resizeFields)
      },

      exampleDTD() {
         this.state.xema._dtd = `<!ELEMENT entry (headword)>\n<!ELEMENT headword (#PCDATA)>`;
         this.$nextTick(this.resizeFields)
      }
   }
}
</script>

<style>
dict-config-xema #editor {
   position: relative !important;
   min-height: 750px;
   display: flex;
   flex-wrap: nowrap;
}
dict-config-xema #editor .details {flex-grow: 1; overflow: hidden; max-width: 100%;}

dict-config-xema .editor .list { flex-basis: 0; }

dict-config-xema #editor.designer input.textbox.cap {
   width: 15em !important;
}
dict-config-xema #editor.designer input[type=radio] {
   opacity: 1 !important;
}
dict-config-xema {
   display: block;
}
</style>
