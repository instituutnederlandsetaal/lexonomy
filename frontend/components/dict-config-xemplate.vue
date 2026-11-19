<template>
<div class="dict-config-xemplate">
   <LoadingOverlay v-if="loading || saving"/>
   <DictNav :links="[['config', 'Configure'], ['config-xemplate', 'Entry formatting']]"/>
   <h1>Entry formatting</h1>
   <template v-if="ready">
      <DictConfigButtons :dict-id="dictId" :save-data="saveData" :disabled="saving">
         <button
            class="btn waves-effect waves-light"
            @click="toggleOverride" type="button"
         >
            {{ override ? "Stop using your own stylesheet" : "Use your own stylesheet" }}
            <i class="material-symbols-outlined right">edit</i>
         </button>
      </DictConfigButtons>

      <div v-if="!override && xema">
         <div class="formatting-editor">
            <div id="editor" class="designer">
               <div class="list">
                  <DictConfigElementInTree v-for="root in roots"
                     :key="root" :id="root" :xema="xema"
                     :current-element="elementName" :current-attribute="attributeName" @select="select"/>
               </div>
            </div>

            <DisplayStyles v-if="elementName"
               :element-name="elementName" :attribute-name="attributeName" :element-data="selectedFields"
               :xema="xema" :graphical="graphical" @update="updateFormatting"/>

            <div id="preview" class="preview">
               <div class="block">
                  <div class='title'><button type="button" class="reload" :disabled="previewLoading" @click="loadNewPreview">Reload random entry</button> Preview
                  </div>
               </div>
               <div id="preview-box" class="area viewer" v-html="previewHtml"></div>
               <div v-if="previewUnavailable" class="noentries">Could not load the entry preview.</div>
               <div v-else-if="noEntries" class="noentries">The dictionary has no entries yet.</div>
            </div>
         </div>

      </div>
      <div v-if="override">
         <div class="row">
            <div class="input-field col s10">
               <textarea id="editor_xsl"
                         rows="6" class="materialize-textarea" v-model="draft._xsl"></textarea>
               <label class="active" for="editor_xsl">XSL</label>
               <span class="helper-text">Custom XSL stylesheet. If you would like to see an example,
                  <button type="button" class="btn-flat" @click="exampleXsl">click here to load a sample XSL</button>.
               </span>
            </div>
         </div>
         <div class="row">
            <div class="input-field col s10">
               <textarea id="editor_css"
                         rows="6" class="materialize-textarea" v-model="draft._css"></textarea>
               <label class="active" for="editor_css">CSS</label>
               <span class="helper-text">Custom CSS stylesheet. If you would like to see an example,
                  <button type="button" class="btn-flat" @click="exampleCss">click here to load a sample CSS</button>.
               </span>
            </div>
         </div>

      </div>

   </template>
   <p v-else-if="!loading">Settings could not be loaded. <button class="btn-flat" type="button" @click="load">Retry</button></p>
</div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import '../widgets/xema-designer.css'
import { activeDictionary } from '../js/dictionary-workspace.ts'
import { fetchPreviewEntry } from '../js/dictionary-config-api.ts'
import { crossReferenceHref } from '../js/entry-search.ts'
import { sanitizeHtml } from '../js/sanitize-html.ts'
import { useDictionarySetting } from '../js/use-dictionary-setting.ts'
import { xmlElementName } from '../js/xema.ts'
import { previewFormatting, readFormattingFields, type FormattingFields, type Xemplate } from '../js/xemplate.ts'
import { renderXml } from '../widgets/xemplatron.ts'
import DictConfigButtons from './dict-config-buttons.vue'
import DictConfigElementInTree from './dict-config-element-in-tree.vue'
import DictNav from './dict-nav.vue'
import DisplayStyles from './entry-formatting/display-styles.vue'
import LoadingOverlay from './loading-overlay.vue'
import { treeRoots } from './entry-structure/tree-roots.ts'

const props = defineProps<{ dictId: string }>()
const draft = ref<Xemplate>({})
const override = ref(false)
const elementName = ref<string>()
const attributeName = ref<string>()
const previewXml = ref('')
const previewLoading = ref(false)
const previewUnavailable = ref(false)
const noEntries = ref(false)
const { scope, loading, ready, saving, load, save } = useDictionarySetting(() => props.dictId, 'xemplate', content => {
   draft.value = content
   override.value = Boolean(content._xsl || content._css)
   if (!override.value) void loadNewPreview()
})
watch(scope, () => {
   elementName.value = undefined
   attributeName.value = undefined
   previewXml.value = ''
   previewLoading.value = false
   previewUnavailable.value = false
   noEntries.value = false
})
const xema = computed(() => activeDictionary.config?.xema)
const graphical = computed(() => activeDictionary.config?.editing.xonomyMode === 'graphical')
const roots = computed(() => treeRoots(xema.value))
const selectedTag = computed(() => elementName.value && xema.value ? xmlElementName(xema.value, elementName.value) : '')
const selectedFields = computed(() => {
   if (!elementName.value) return {}
   return previewFormatting(draft.value, elementName.value, selectedTag.value, attributeName.value)
})
const previewHtml = computed(() => previewXml.value && xema.value
   ? sanitizeHtml(renderXml(previewXml.value, draft.value, xema.value, crossReferenceHref))
   : '')

function toggleOverride() {
   override.value = !override.value
   if (!override.value && !previewXml.value) void loadNewPreview()
}

function select(id: string, attribute?: string) {
   elementName.value = id
   attributeName.value = attribute
}

function updateFormatting(key: keyof FormattingFields, value: boolean | string) {
   const id = elementName.value
   if (!id) return
   const element = readFormattingFields(draft.value, id, selectedTag.value)
   const attribute = attributeName.value
   const fields = attribute
      ? { ...readFormattingFields(draft.value, id, selectedTag.value, attribute), [key]: value }
      : { ...element, [key]: value }
   draft.value = { ...draft.value, [id]: attribute
      ? { ...element, attributes: { ...element.attributes, [attribute]: fields } } : fields }
}

async function loadNewPreview() {
   if (previewLoading.value) return
   const current = scope.value
   previewLoading.value = true
   previewUnavailable.value = false
   try {
      const entry = await fetchPreviewEntry(current.dictId)
      if (!current.active) return
      noEntries.value = entry.id === 0
      previewXml.value = entry.xml
   } catch {
      if (current.active) previewUnavailable.value = true
   } finally {
      if (current.active) previewLoading.value = false
   }
}

function saveData() {
   const { _xsl, _css, ...fields } = draft.value
   return save(override.value ? { ...fields, _xsl, _css } : fields)
}

function exampleXsl() {
   draft.value._xsl = `<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
   <xsl:template match="entry">
      <div class="myEntry"><xsl:apply-templates/></div>
   </xsl:template>
   <xsl:template match="headword">
      <span class="myHeadword"><xsl:apply-templates/></span>
   </xsl:template>
</xsl:stylesheet>`
}

function exampleCss() {
   draft.value._css = 'div.myEntry {font-family: serif; font-size: 1.25em}\ndiv.myEntry span.myHeadword {font-weight: bold}'
}
</script>

<style>
.dict-config-xemplate .formatting-editor {
   display: flex;
}
.dict-config-xemplate #editor.designer {
   flex-basis: 0;
   width: auto;
   position: static;
   overflow: initial;
   margin-right: 15px !important;
}

.dict-config-xemplate #editor.designer input[type=radio] {
   opacity: 1 !important;
}

.dict-config-xemplate #preview {
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

.dict-config-xemplate #preview .block {
   margin: 10px 15px 0px 15px;
   padding: 5px 0px 5px 0px;
}

.dict-config-xemplate #preview .block:first-child {
   padding-top: 0px;
}

.dict-config-xemplate #preview .block > .title {
   background-color: #dddddd;
   padding: 10px 10px;
   border-radius: 2px;
   margin-bottom: 10px;
   text-shadow: 1px 1px 0px #ffffff;
}

.dict-config-xemplate #preview .block > .title > .reload {
   float: right;
   border: 0;
   background-color: transparent;
   background-image: url(/assets/furniture/arrow_refresh.png);
   background-position: left center;
   background-repeat: no-repeat;
   padding: 5px 0px 5px 25px;
   position: relative;
   top: -5px;
   cursor: pointer;
   color: #004f9b;
}

.dict-config-xemplate #preview .block > .title > .reload:hover {
   color: #1969b6;
}

.dict-config-xemplate #preview .viewer {
   padding: 0px 30px 30px 30px;
}

.dict-config-xemplate #preview .noentries {
   padding: 0px 20px 20px 25px;
   color: #999999;
}
</style>
