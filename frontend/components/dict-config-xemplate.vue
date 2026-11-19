<template>
<dict-config-xemplate>
   <LoadingOverlay v-if="state.isLoading || state.isSaving"/>
   <DictNav :links="[['config', 'Configure'], ['config-xemplate', 'Entry formatting']]"/>
   <h1>Entry formatting</h1>
   <DictConfigButtons :save-data="saveData">
      <button
         class="btn waves-effect waves-light"
         @click="toggleOverride"
      >
         {{ state.override ? "Stop using your own stylesheet" : "Use your own stylesheet" }}
         <i class="material-symbols-outlined right">edit</i>
      </button>
   </DictConfigButtons>

   <div v-if="!state.override">
      <div style="display: flex">
         <!-- TODO fixup styles so we don't need this sillyness. -->
         <div
            id="editor"
            class="designer"
            style="
            flex-basis: 0;
            width: auto;
            position: static;
            overflow: initial!important;
            margin-right: 15px!important"
         >
            <div class="list">
               <DictConfigElementInTree v-for="root in roots"
                                            :key="root.id"
                                            :depth="0"
                                            :data="root"
                                            :xema="activeDictionary.config.xema"
                                            :current-element="elementName"
                                            :current-attribute="attributeName"
                                            :selectElementOrAttribute="selectElementOrAttribute"
               />
            </div>
         </div>

         <DisplayStyles v-if="elementName"
                         name="displayStylesComponent"
                         :elementName="elementName"
                         :attributeName="attributeName"
                         :elementConfigData="state.data[elementName]"
                         :config="activeDictionary.config"
                         :save-data="handleElementData"
         />

         <div id="preview" class="preview">
            <div class="block">
               <div class='title'><span class='reload' @click="loadNewPreview">reload random entry</span> Preview
               </div>
            </div>
            <div id="preview-box" class="area viewer" v-html="previewHtml"></div>
            <div v-if="noEntries" class="noentries">The dictionary has no entries yet.</div>
         </div>
      </div>

   </div>
   <div v-if="state.override">
      <div class="row">
         <div class="input-field col s10">
            <textarea id="editor_xsl"
                      class="materialize-textarea" v-model="state.data._xsl"></textarea>
            <label for="editor_xsl">XSL</label>
            <span class="helper-text">Custom XSL stylesheet. If you would like to see an example,
               <a @click="exampleXsl">click here to load a sample XSL</a>.
            </span>
         </div>
      </div>
      <div class="row">
         <div class="input-field col s10">
            <textarea id="editor_css"
                      class="materialize-textarea" v-model="state.data._css"></textarea>
            <label for="editor_css">CSS</label>
            <span class="helper-text">Custom CSS stylesheet. If you would like to see an example,
               <a @click="exampleCss">click here to load a sample CSS</a>.
            </span>
         </div>
      </div>

   </div>

</dict-config-xemplate>
</template>

<script>
import Materialize from '../libs/materialize/materialize.min.js'
import '../widgets/xema-designer.css'
import { activeDictionary, dictionaryWorkspace } from '../js/dictionary-workspace.ts'
import DictConfigButtons from './dict-config-buttons.vue'
import DictConfigElementInTree from './dict-config-element-in-tree.vue'
import DictNav from './dict-nav.vue'
import DisplayStyles from './entry-formatting/display-styles.vue'
import LoadingOverlay from './loading-overlay.vue'
import { api } from '../js/api.ts'
import { Xemplatron } from '../widgets/xemplatron.js'
import { treeRoots } from './entry-structure/tree-roots.js'

export default {
   setup: () => ({ activeDictionary }),
   components: { DictConfigButtons, DictConfigElementInTree, DictNav, DisplayStyles, LoadingOverlay },
   data() {
      return {
         state: {
            isLoading: true,
            isSaving: false,
            override: false,
            data: {}
         },
         elementName: null,
         attributeName: null,
         previewXml: '',
         noEntries: false
      }
   },

   async mounted() {
      const response = await dictionaryWorkspace.loadDictionaryConfig('xemplate')
      if (response) {
         const { content } = response
         this.state.data = content
         this.state.override = Boolean(content._xsl || content._css)
         if (this.state.override) {
            this.$nextTick(this.resizeFields)
         } else {
            this.loadNewPreview()
         }
      }
      this.state.isLoading = false
   },

   computed: {
      roots() {
         return treeRoots(this.activeDictionary.config?.xema)
      },
      previewHtml() {
         return this.previewXml && this.activeDictionary.config
            ? Xemplatron.xml2html(this.previewXml, this.state.data, this.activeDictionary.config.xema)
            : ''
      }
   },

   methods: {
      toggleOverride() {
         this.state.override = !this.state.override
         if (this.state.override) {
            this.$nextTick(this.resizeFields)
         } else {
            delete this.state.data._xsl
            delete this.state.data._css
            this.$nextTick(this.loadNewPreview)
         }
      },

      resizeFields() {
         Materialize.updateTextFields()
         this.$el.querySelectorAll('textarea').forEach(field => Materialize.textareaAutoResize(field))
      },

      exampleXsl() {
         this.state.data._xsl = `<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
   <xsl:template match="entry">
      <div class="myEntry"><xsl:apply-templates/></div>
   </xsl:template>
   <xsl:template match="headword">
      <span class="myHeadword"><xsl:apply-templates/></span>
   </xsl:template>
</xsl:stylesheet>`
         this.$nextTick(this.resizeFields)
      },

      exampleCss() {
         this.state.data._css = 'div.myEntry {font-family: serif; font-size: 1.25em}\ndiv.myEntry span.myHeadword {font-weight: bold}'
         this.$nextTick(this.resizeFields)
      },

      selectElementOrAttribute(elementId, attributeId) {
         this.elementName = elementId
         this.attributeName = attributeId || null

      },

      handleElementData(elementName, attributeName, attribute, value) {
         const element = (this.state.data[elementName] ??= {})
         const fields = attributeName ? ((element.attributes ??= {})[attributeName] ??= {}) : element
         fields[attribute] = value
      },

      async loadNewPreview() {
         try {
            const data = await api.post(`${encodeURIComponent(this.activeDictionary.dictId)}/randomone.json`)
            this.noEntries = !data.id
            this.previewXml = data.id ? data.xml : ''
         } catch {
            Materialize.toast({ html: 'Could not load the entry preview.' })
         }
      },

      async saveData() {
         this.state.isSaving = true
         await dictionaryWorkspace.updateDictionaryConfig("xemplate", this.state.data)
         this.state.isSaving = false
      }
   }
}
</script>

<style>
dict-config-xemplate #editor.designer input[type=radio] {
   opacity: 1 !important;
}

dict-config-xemplate #preview {
   position: absolute;
   top: 0px;
   left: 60%;
   bottom: 0px;
   right: 0px;
   overflow-x: hidden;
   overflow-y: auto;
   padding: 5px 0px;
   border-left: 1px solid #1e6bcf;
   background-color: #f6f6f6;
}

dict-config-xemplate #preview .block {
   margin: 10px 15px 0px 15px;
   padding: 5px 0px 5px 0px;
}

dict-config-xemplate #preview .block:first-child {
   padding-top: 0px;
}

dict-config-xemplate #preview .block > .title {
   background-color: #dddddd;
   padding: 10px 10px;
   border-radius: 2px;
   margin-bottom: 10px;
   text-shadow: 1px 1px 0px #ffffff;
}

dict-config-xemplate #preview .block > .title > .reload {
   float: right;
   background-image: url(/assets/furniture/arrow_refresh.png);
   background-position: left center;
   background-repeat: no-repeat;
   padding: 5px 0px 5px 25px;
   position: relative;
   top: -5px;
   cursor: pointer;
   color: #004f9b;
}

dict-config-xemplate #preview .block > .title > .reload:hover {
   color: #1969b6;
}

dict-config-xemplate #preview .viewer {
   padding: 0px 30px 30px 30px;
}

dict-config-xemplate #preview .noentries {
   padding: 0px 20px 20px 25px;
   color: #999999;
}
</style>
