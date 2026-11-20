<template>
<div class="dict-config-editing">
   <LoadingOverlay v-if="loading || saving"/>
   <DictNav :links="[['config', 'Configure'], ['config-editing', 'Entry editor']]"/>
   <h1>Entry editor</h1>

   <template v-if="ready">
      <DictConfigButtons :dict-id="dictId" :save-data="saveData" :disabled="saving || !ready || Boolean(codeError)">
         <button class="btn waves-effect waves-light" @click="override = !override" >
            {{ override ? 'Disable entry editor customizations' : 'Customize entry editor' }}
            <i class="material-symbols-outlined right">{{ override ? 'close' : 'edit' }}</i>
         </button>
      </DictConfigButtons>
      <div v-if="!override">
         <div class="input-field">
            <p>
               <label>
                  <input name="xonomyMode"
                        id="xonomyMode_nerd"
                        type="radio"
                        class="with-gap"
                        value="nerd"
                        v-model="draft.xonomyMode" />
                  <span>Nerd mode</span>
               </label>
               <label style="margin-left: 30px;">
                  <input name="xonomyMode"
                        id="xonomyMode_laic"
                        type="radio"
                        class="with-gap"
                        value="laic"
                        v-model="draft.xonomyMode"/>
                  <span>Laic mode</span>
               </label>
               <label style="margin-left: 30px;">
                  <input name="xonomyMode"
                        id="xonomyMode_graphical"
                        type="radio"
                        class="with-gap"
                        value="graphical"
                        v-model="draft.xonomyMode"/>
                  <span>Graphical mode</span>
               </label>
            </p>
            <span class="helper-text">Choose what the entry editor will look like.</span>
         </div>
         <div id="info_nerd" v-show="draft.xonomyMode === 'nerd'">
            <p>When editing an entry in <b>nerd mode</b> the user sees the XML source code, angle brackets and all.</p>
               <div class='instro'>
                  <img src='/docs/mode-nerd.png' alt='Illustration'/>
               </div>
               <br/>
               Individual users can override this setting by clicking an icon in the bottom-left corner of their screen.
         </div>
         <div id="info_laic" v-show="draft.xonomyMode === 'laic'">
            <p>When editing an entry in <b>laic mode</b> the XML source code is hidden and the entry looks more like a bulleted list.</p>
               <div class='instro'>
                  <img src='/docs/mode-laic.png' alt='Illustration'/>
               </div>
               <br/>
               Individual users can override this setting by clicking an icon in the bottom-left corner of their screen.
         </div>
         <div id="info_graphical" v-show="draft.xonomyMode === 'graphical'" style="padding-left: 50px;">
            <p>When editing an entry in <b>graphical mode</b> the XML source code is hidden and the entry uses settings configuration to display a more graphically friendly interface.</p>
            <div class='instro'>Image of graphical editor</div>
         </div>
         <br>
         <div class="input-field">
            <p>
               <label>
                  <input name="xonomyTextEditor"
                        id="xonomyTextEditor_string"
                        type="radio"
                        class="with-gap"
                        value="askString"
                        v-model="draft.xonomyTextEditor"/>
                  <span>Single line</span>
               </label>
               <label style="margin-left: 30px;">
                  <input name="xonomyTextEditor"
                        id="xonomyTextEditor_longstring"
                        type="radio"
                        class="with-gap"
                        value="askLongString"
                        v-model="draft.xonomyTextEditor"/>
                  <span>Multi line</span>
               </label>
            </p>
            <span class="helper-text">Choose the default text editor for node values.</span>
         </div>
         <div id="info_string" v-show="draft.xonomyTextEditor === 'askString'"
               style="margin-left: 30px;">
            <p>When editing text in <b>single line mode</b> the user sees a smaller editor.</p>
               <div class='instro'>
                  <img src='/docs/text-editor-askstring.png' alt='Illustration'/>
               </div>
         </div>
         <div id="info_longstring" v-show="draft.xonomyTextEditor === 'askLongString'"
               style="margin-left: 30px;">
            <p>When editing text in <b>multi line mode</b> the user sees a full-fledged text editor.</p>
               <div class='instro'>
                  <img src='/docs/text-editor-asklongstring.png' alt='Illustration'/>
               </div>
         </div>
      </div>
      <div v-if="override">
         <div class="row">
            <label for="editor_api_version">JavaScript format</label>
            <select id="editor_api_version" class="browser-default" v-model="draft.editorApiVersion">
               <option :value="null">Legacy editor script</option>
               <option :value="1">Editor extension (v1)</option>
            </select>
            <div class="input-field">
               <div id="codeStatus">
                  <b :class="codeError ? 'red-text' : 'green-text'">{{ codeError ? 'invalid syntax' : 'valid syntax' }}</b>
                  <span v-if="codeError" class="grey-text right">{{ codeError }}</span>
               </div>
               <textarea id="editor_js"
                     rows="7" class="materialize-textarea"
                     v-model="draft._js"></textarea>
               <label for="editor_js">JavaScript</label>
               <span class="helper-text">
                  Editor extensions receive the entry and schema when mounted and return a function to read the edited XML.
                  <button type="button" class="btn-flat" @click="exampleJS">Load sample JavaScript</button>
                  <a :href="extensionDocs" target="_blank" rel="noopener">Editor extension guide</a>
               </span>
            </div>
         </div>
         <div class="row">
            <div class="input-field">
               <textarea id="editor_css"
                     rows="7" class="materialize-textarea" v-model="draft._css"></textarea>
               <label for="editor_css">CSS</label>
               <span class="helper-text">
                  You can customize the editor look and feel by writing your own CSS styles. If you would like to see an example,
                  <button type="button" class="btn-flat" @click="exampleCSS">Load sample CSS</button>
               </span>
            </div>
         </div>
      </div>
      <DictConfigButtons :dict-id="dictId" :save-data="saveData" :disabled="saving || !ready || Boolean(codeError)">
         <button class="btn waves-effect waves-light" @click="override = !override" >
            {{ override ? 'Disable entry editor customizations' : 'Customize entry editor' }}
            <i class="material-symbols-outlined right">{{ override ? 'close' : 'edit' }}</i>
         </button>
      </DictConfigButtons>
   </template>

   <p v-if="!loading && !ready">Settings could not be loaded. <button class="btn-flat" type="button" @click="load">Retry</button></p>
</div>
</template>

<script setup lang="ts">
import { pageUrl } from '../js/page-url.ts'
import { compileEditorExtension } from '../js/editor-extension.ts'
import { useDictionarySetting } from '../js/use-dictionary-setting.ts'
import DictConfigButtons from './dict-config-buttons.vue'
import DictNav from './dict-nav.vue'
import LoadingOverlay from './loading-overlay.vue'
import { computed, ref } from 'vue'
import type { DictionarySettings } from '../js/dictionary-config-api.ts'

const props = defineProps<{ dictId: string }>()
const defaults: DictionarySettings['editing'] = {
   xonomyMode: 'nerd', xonomyTextEditor: 'askString', editorApiVersion: null, _js: '', _css: ''
}
const extensionDocs = new URL('docs/editor-extensions.md', pageUrl).href
const draft = ref({ ...defaults })
const override = ref(false)
const { loading, ready, saving, load, save } = useDictionarySetting(() => props.dictId, 'editing', content => {
   draft.value = { ...defaults, ...content }
   override.value = Boolean(content._js || content._css)
})

const codeError = computed(() => {
   if (!override.value || !draft.value._js) return ''
   try {
      if (draft.value.editorApiVersion === 1) compileEditorExtension(draft.value._js)
      else new Function('return ' + draft.value._js)
      return ''
   } catch (error) {
      return String(error).split('\n')[0]
   }
})

function saveData() {
   if (codeError.value) return
   return save(override.value ? draft.value : { ...draft.value, editorApiVersion: null, _js: '', _css: '' })
}

function exampleJS() {
   draft.value.editorApiVersion = 1
   draft.value._js = `{
   mount({ element, entry, readOnly, signal, markDirty }) {
      const input = document.createElement('textarea')
      input.className = 'myEditor'
      input.setAttribute('aria-label', 'Entry XML')
      input.value = entry.content
      input.readOnly = readOnly
      input.addEventListener('input', markDirty, { signal })
      element.append(input)
      return { harvest: () => input.value }
   }
}`
}

function exampleCSS() {
   draft.value._css = '#editor textarea.myEditor {min-height: 12rem; font-family: monospace}'
}
</script>

<style>
.dict-config-editing textarea{
   min-height: 30vh;
}
.dict-config-editing #editor_js{
   padding-top: 25px;
}
.dict-config-editing #codeStatus{
   top: 1px;
   position: absolute;
   right: 1px;
   left: 1px;
   background-color: whitesmoke;
   padding: 3px 8px;
}
.dict-config-editing #info_nerd, .dict-config-editing #info_laic{
   padding-left: 50px;
}
</style>
