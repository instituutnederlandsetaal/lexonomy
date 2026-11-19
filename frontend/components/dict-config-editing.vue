<template>
<dict-config-editing>
   <LoadingOverlay v-if="state.isLoading || state.isSaving"/>
   <DictNav :links="[['config', 'Configure'], ['config-editing', 'Entry editor']]"/>
   <h1>Entry editor</h1>

   <template v-if="!state.isLoading">
      <DictConfigButtons :save-data="saveData">
         <button class="btn waves-effect waves-light" @click="toggleOverride" >
            {{ state.override ? 'Disable entry editor customizations' : 'Customize entry editor' }}
            <i class="material-symbols-outlined right">{{ state.override ? 'close' : 'edit' }}</i>
         </button>
      </DictConfigButtons>
      <div v-if="!state.override">
         <div class="input-field">
            <p>
               <label>
                  <input name="xonomyMode"
                        id="xonomyMode_nerd"
                        type="radio"
                        class="with-gap"
                        value="nerd"
                        v-model="state.data.xonomyMode" />
                  <span>Nerd mode</span>
               </label>
               <label style="margin-left: 30px;">
                  <input name="xonomyMode"
                        id="xonomyMode_laic"
                        type="radio"
                        class="with-gap"
                        value="laic"
                        v-model="state.data.xonomyMode"/>
                  <span>Laic mode</span>
               </label>
               <label style="margin-left: 30px;">
                  <input name="xonomyMode"
                        id="xonomyMode_graphical"
                        type="radio"
                        class="with-gap"
                        value="graphical"
                        v-model="state.data.xonomyMode"/>
                  <span>Graphical mode</span>
               </label>
            </p>
            <span class="helper-text">Choose what the entry editor will look like.</span>
         </div>
         <div id="info_nerd" v-show="state.data.xonomyMode === 'nerd'">
            <p>When editing an entry in <b>nerd mode</b> the user sees the XML source code, angle brackets and all.</p>
               <div class='instro'>
                  <img src='/docs/mode-nerd.png' alt='Illustration'/>
               </div>
               <br/>
               Individual users can override this setting by clicking an icon in the bottom-left corner of their screen.
         </div>
         <div id="info_laic" v-show="state.data.xonomyMode === 'laic'">
            <p>When editing an entry in <b>laic mode</b> the XML source code is hidden and the entry looks more like a bulleted list.</p>
               <div class='instro'>
                  <img src='/docs/mode-laic.png' alt='Illustration'/>
               </div>
               <br/>
               Individual users can override this setting by clicking an icon in the bottom-left corner of their screen.
         </div>
         <div id="info_graphical" v-show="state.data.xonomyMode === 'graphical'" style="padding-left: 50px;">
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
                        v-model="state.data.xonomyTextEditor"/>
                  <span>Single line</span>
               </label>
               <label style="margin-left: 30px;">
                  <input name="xonomyTextEditor"
                        id="xonomyTextEditor_longstring"
                        type="radio"
                        class="with-gap"
                        value="askLongString"
                        v-model="state.data.xonomyTextEditor"/>
                  <span>Multi line</span>
               </label>
            </p>
            <span class="helper-text">Choose the default text editor for node values.</span>
         </div>
         <div id="info_string" v-show="state.data.xonomyTextEditor === 'askString'"
               style="margin-left: 30px;">
            <p>When editing text in <b>single line mode</b> the user sees a smaller editor.</p>
               <div class='instro'>
                  <img src='/docs/text-editor-askstring.png' alt='Illustration'/>
               </div>
         </div>
         <div id="info_longstring" v-show="state.data.xonomyTextEditor === 'askLongString'"
               style="margin-left: 30px;">
            <p>When editing text in <b>multi line mode</b> the user sees a full-fledged text editor.</p>
               <div class='instro'>
                  <img src='/docs/text-editor-asklongstring.png' alt='Illustration'/>
               </div>
         </div>
      </div>
      <div v-if="state.override">
         <div class="row">
            <div class="input-field">
               <div id="codeStatus">
                  <b :class="codeError ? 'red-text' : 'green-text'">{{ codeError ? 'invalid' : 'valid' }}</b>
                  <span v-if="codeError" class="grey-text right">{{ codeError }}</span>
               </div>
               <textarea id="editor_js"
                     class="materialize-textarea"
                     v-model="state.data._js"></textarea>
               <label>JavaScript</label>
               <span class="helper-text">
                  You can customize the editor by defining two functions in JavaScript: one that will render the HTML editor from the XML entry and one that will harvest the (edited) HTML back into XML. If you would like to see an example,
                  <a @click="exampleJS">click here to load a sample JavaScript code</a>.
               </span>
            </div>
         </div>
         <div class="row">
            <div class="input-field">
               <textarea id="editor_css"
                     class="materialize-textarea" v-model="state.data._css"></textarea>
               <label for="editor_css">CSS</label>
               <span class="helper-text">
                  You can customize the editor look and feel by writing your own CSS styles. If you would like to see an example,
                  <a @click="exampleCSS">click here to load a sample CSS style</a>.
               </span>
            </div>
         </div>
      </div>
      <DictConfigButtons :save-data="saveData">
         <button class="btn waves-effect waves-light" @click="toggleOverride" >
            {{ state.override ? 'Disable entry editor customizations' : 'Customize entry editor' }}
            <i class="material-symbols-outlined right">{{ state.override ? 'close' : 'edit' }}</i>
         </button>
      </DictConfigButtons>
   </template>

</dict-config-editing>
</template>

<script>
import Materialize from '../libs/materialize/materialize.min.js'
import { dictionaryWorkspace } from '../js/dictionary-workspace.ts'
import DictConfigButtons from './dict-config-buttons.vue'
import DictNav from './dict-nav.vue'
import LoadingOverlay from './loading-overlay.vue'
export default {
   components: { DictConfigButtons, DictNav, LoadingOverlay },
   data() {
      return {
         state: {
            isLoading: true,
            isSaving: false,
            override: false,
            data: {
               xonomyMode: "nerd",
               xonomyTextEditor: "askString",
               _js: "",
               _css: ""
            }
         }
      }
   },

   async mounted() {
      const response = await dictionaryWorkspace.loadDictionaryConfig('editing')
      if (response) {
         const { content } = response
         this.state.data = {...this.state.data, ...content}
         this.state.override = Boolean(content._js)
      }
      this.state.isLoading = false
      if (this.state.override) this.$nextTick(this.resizeFields)
   },

   computed: {
      codeError() {
         try {
            new Function('return ' + (this.state.data._js || ''))
            return ''
         } catch (error) {
            return error.toString().split('\n')[0]
         }
      }
   },

   methods: {
      resizeFields() {
         Materialize.updateTextFields()
         this.$el.querySelectorAll('#editor_css, #editor_js').forEach(field => Materialize.textareaAutoResize(field))
      },

      toggleOverride() {
         this.state.override = !this.state.override
         if (this.state.override) this.$nextTick(this.resizeFields)
      },

      exampleJS() {
         this.state.data._js = `{
        editor: function(div, entry, uneditable){
          //div = the div into which you should render the editor
          //entry.id = the entry ID (a number, eg. 123), or zero if new entry
          //entry.content = the entry's XML source code, eg. "<entry></headword>hello</headword></entry>"
          //uneditable = true if we want the entry to be uneditable (read-only)
          $(div).html("<div class='myEditor'>HEADWORD: <input class='headword' "+(uneditable?"disabled":"")+"/></div>");
          $(div).find("input.headword").val($($.parseXML(entry.content)).find("headword").html());
        },
        harvester: function(div){
          //div = the div from which you should harvest the contents of the editor
          var headword=$(div).find("input.headword").val();
          return "<entry><headword>"+headword+"</headword></entry>";
        },
        adjustDocSpec: function (docSpec) {
          // NOTE: you normally want to use this method if you don't have a custom editor,
          // but just want to change certain aspects of how Xonomy presents the document.
          $.each(docSpec.elements, function (elementName, elementSpec) {
            // Expand <sense> elements by default.
            if (elementName === 'sense') {
              elementSpec.collapsed = function (jsElement) { return false; }
            }
            // Make <example> read-only
            if (elementName === 'example') {
              elementSpec.isReadOnly = true;
            }
            // Hide <partOfSpeech>.
            if (elementName === 'partOfSpeech') {
              elementSpec.isInvisible = true;
            }
          });
        }
      }`
         this.$nextTick(this.resizeFields)
      },

      exampleCSS() {
         this.state.data._css = 'div.myEditor {padding: 20px; font-size: 1.25em}\ndiv.myEditor input {font-weight: bold}'
         this.$nextTick(this.resizeFields)
      },

      getConfigData() {
         const {xonomyMode, xonomyTextEditor, _js, _css} = this.state.data
         return {
            xonomyMode,
            xonomyTextEditor,
            _js: this.state.override ? _js : '',
            _css: this.state.override ? _css : ''
         }
      },

      async saveData() {
         this.state.isSaving = true
         await dictionaryWorkspace.updateDictionaryConfig("editing", this.getConfigData())
         this.state.isSaving = false
      }
   }
}
</script>

<style>
dict-config-editing textarea{
   min-height: 30vh;
}
dict-config-editing #editor_js{
   padding-top: 25px;
}
dict-config-editing #codeStatus{
   top: 1px;
   position: absolute;
   right: 1px;
   left: 1px;
   background-color: whitesmoke;
   padding: 3px 8px;
}
dict-config-editing #info_nerd, dict-config-editing #info_laic{
   padding-left: 50px;
}
</style>
