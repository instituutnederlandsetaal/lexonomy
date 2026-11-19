<template>
<display-styles>
   <div class="display-styles">
      <div>
         <h4>
            Configuration for {{ elementName }}
         </h4>
         <h5>Preview</h5>
         <div class="toggle-input toggle-input--preview">
            <label>Visibility</label>
            <div class="switch">
               <label>
                  Off
                  <input
                     id="shown"
                     type="checkbox"
                     @change="toggleVisibility"
                     :checked="elementData.shown === true"
                  >
                  <span class="lever"></span>
                  On
               </label>
            </div>
         </div>
      </div>
      <div class="break"/>
      <div v-if="elementData.shown">
         <div class="toggle-input toggle-input--preview">
            <label>Layout</label>
            <div class="switch">
               <label>
                  Inline
                  <input
                     id="layout"
                     type="checkbox"
                     @change="toggleLayout"
                     :checked="elementData.layout === 'block'"
                  >
                  <span class="lever"></span>
                  Line break before and after
               </label>
            </div>
         </div>
         <div class="break"/>
         <div v-for="style in visibleStyles"
            :key="style.type"
            class="select-input"
         >
            <label :for="style.type">{{ style.title }}</label>
            <select
               :id="style.type"
               :name="style.type"
               :value="elementData[style.type]"
               required
               @change="sendData"
               style="display: block"
            >
               <option
                  :selected="elementData[style.type] == null"
                  value=""
               >
                  Select option
               </option>
               <option
                  v-for="option in style.values"
                  :key="option.value"
                  :value="option.value"
                  :selected="option.value === elementData[style.type]"
               >
                  {{ option.label }}
               </option>
            </select>
         </div>
         <div class="break"/>
         <div class="select-input">
            <label for="label">Label</label>
            <input id="label" class="textbox" @change="sendData" :value="elementData.label">
         </div>
      </div>
      <div v-if="elementData.shown" class="section--graphical">
         <div class="break"/>
         <h5>Graphical editor</h5>
         <div
            v-for="setting in possibleToggles"
            :key="setting.type"
            class="toggle-input"
         >
            <label>{{ setting.label }}</label>
            <div class="switch">
               <label>
                  Off
                  <input
                     :id="setting.type"
                     type="checkbox"
                     @change="sendData"
                     :checked="elementData[setting.type] === true"
                  >
                  <span class="lever"></span>
                  On
               </label>
            </div>
         </div>
         <div class="break"/>
         <div v-for="style in visibleGraphicalSettings"
            :key="style.type"
            class="select-input"
         >
            <label :for="style.type">{{ style.title }}</label>
            <select
               :id="style.type"
               :name="style.type"
               :value="elementData[style.type]"
               required
               @change="sendData"
               style="display: block"
            >
               <option
                  :selected="elementData[style.type] == null"
                  value=""
               >
                  Select option
               </option>
               <option
                  v-for="option in style.values"
                  :key="option.value"
                  :value="option.value"
                  :selected="option.value === elementData[style.type]"
               >
                  {{ option.label }}
               </option>
            </select>
         </div>
         <div v-if="config.editing?.xonomyMode !== 'graphical'" class="overlay--disabled">
            <div class="notification">
               <p>Enable <b>Graphical mode</b></p>
            </div>
         </div>
      </div>
   </div>

</display-styles>
</template>

<script>
export default {
   props: {
      elementName: String,
      attributeName: String,
      elementConfigData: Object,
      config: Object,
      saveData: Function
   },

   data() {
      return {
         possibleToggles: [
            {
               type: "enablePositionChange",
               label: "Enable reordering of elements of same type"
            },
            {
               type: "enableParentChange",
               label: "Enable moving element between different parent elements"
            },
            {
               type: "enableCopying",
               label: "Enable making copies of element"
            },
            {
               type: "readOnly",
               label: "Disable editing of element"
            },
            {
               type: "hideElementName",
               label: "Hide element name in editor"
            }
         ],
         graphicalEditorSettings: [
            {
               type: "displayType",
               title: "Display type of element",
               values: [
                  {
                     value: "popup",
                     label: "Popup on click"
                  },
                  {
                     value: "inline",
                     label: "Display in parent element"
                  }
               ]
            },
            {
               type: "editorInputType",
               title: "Input type in editor",
               values: [
                  {
                     value: "text",
                     label: "Text input"
                  },
                  {
                     value: "textarea",
                     label: "Textarea input"
                  },
                  {
                     value: "number",
                     label: "Number input"
                  }
               ]
            }
         ],
         possibleStyles: [
            {
               type: "captioning",
               title: "Caption display",
               values: [
                  {
                     value: "replace",
                     label: "Show caption instead of value"
                  },
                  {
                     value: "mouseover",
                     label: "Show caption on mouse-over"
                  }
               ]
            },
            {
               type: "interactivity",
               title: "Interactivity",
               values: [
                  {
                     value: "xref",
                     label: "Clickable cross-reference"
                  },
                  {
                     value: "xlink",
                     label: "External URL link"
                  }
               ]
            },
            {
               type: "innerPunc",
               title: "Inner punctuation",
               values: [
                  {
                     value: "roundBrackets",
                     label: "Round brackets"
                  },
                  {
                     value: "squareBrackets",
                     label: "Square brackets"
                  },
                  {
                     value: "curlyBrackets",
                     label: "Curly brackets"
                  },
                  {
                     value: "comma",
                     label: "Comma"
                  },
                  {
                     value: "semicolon",
                     label: "Semicolon"
                  },
                  {
                     value: "colon",
                     label: "Colon"
                  }
               ]
            },
            {
               type: "textsize",
               title: "Text size",
               values: [
                  {
                     value: "smaller",
                     label: "Smaller"
                  },
                  {
                     value: "bigger",
                     label: "Bigger"
                  }
               ]
            },
            {
               type: "weight",
               title: "Text weight",
               values: [
                  {
                     value: "bold",
                     label: "Bold"
                  }
               ]
            },
            {
               type: "slant",
               title: "Text slant",
               values: [
                  {
                     value: "italic",
                     label: "Italic"
                  }
               ]
            },
            {
               type: "colour",
               title: "Text color",
               values: [
                  {
                     value: "red",
                     label: "Red"
                  },
                  {
                     value: "blue",
                     label: "Blue"
                  },
                  {
                     value: "green",
                     label: "Green"
                  },
                  {
                     value: "grey",
                     label: "Grey"
                  }
               ]
            },
            {
               type: "outerPunc",
               title: "Outer punctuation",
               values: [
                  {
                     value: "roundBrackets",
                     label: "Round brackets"
                  },
                  {
                     value: "squareBrackets",
                     label: "Square brackets"
                  },
                  {
                     value: "curlyBrackets",
                     label: "Curly brackets"
                  },
                  {
                     value: "comma",
                     label: "Comma"
                  },
                  {
                     value: "semicolon",
                     label: "Semicolon"
                  },
                  {
                     value: "colon",
                     label: "Colon"
                  }
               ]
            },
            {
               type: "background",
               title: "Background color",
               values: [
                  {
                     value: "yellow",
                     label: "Yellow"
                  },
                  {
                     value: "blue",
                     label: "Blue"
                  },
                  {
                     value: "grey",
                     label: "Grey"
                  }
               ]
            },
            {
               type: "border",
               title: "Box border",
               values: [
                  {
                     value: "dotted",
                     label: "Dotted"
                  },
                  {
                     value: "solid",
                     label: "Solid"
                  },
                  {
                     value: "thick",
                     label: "Thick"
                  }
               ]
            },
            {
               type: "gutter",
               title: "Indentation and bulleting",
               values: [
                  {
                     value: "disk",
                     label: "Round bullet"
                  },
                  {
                     value: "square",
                     label: "Square bullet"
                  },
                  {
                     value: "diamond",
                     label: "Diamond bullet"
                  },
                  {
                     value: "arrow",
                     label: "Arrow bullet"
                  },
                  {
                     value: "indent",
                     label: "Indent"
                  },
                  {
                     value: "handing",
                     label: "Hanging indent"
                  },
                  {
                     value: "sensenum0",
                     label: "Sense number I, II, III..."
                  },
                  {
                     value: "sensenum1",
                     label: "Sense number 1, 2, 3..."
                  },
                  {
                     value: "sensenum2",
                     label: "Sense number a, b, c..."
                  },
                  {
                     value: "sensenum3",
                     label: "Sense number i, ii, iii..."
                  }
               ]
            },
            {
               type: "separation",
               title: "Separation from other content",
               values: [
                  {
                     value: "space",
                     label: "Whitespace"
                  }
               ]
            }
         ]
      }
   },

   computed: {
      elementData() {
         const fields = this.attributeName ? this.elementConfigData?.attributes?.[this.attributeName] : this.elementConfigData
         return { layout: 'inline', ...fields }
      },
      visibleStyles() {
         return this.possibleStyles.filter(style => this.shouldRenderStyle(style.type))
      },
      visibleGraphicalSettings() {
         return this.graphicalEditorSettings.filter(style => this.shouldRenderStyle(style.type))
      }
   },

   methods: {
      toggleVisibility() {
         this.saveData(this.elementName, this.attributeName, 'shown', !this.elementData.shown)
      },

      toggleLayout() {
         const layout = this.elementData.layout === 'block' ? 'inline' : 'block'
         this.saveData(this.elementName, this.attributeName, 'layout', layout)
      },

      sendData(event) {
         const field = event.target
         this.saveData(this.elementName, this.attributeName, field.id, field.type === 'checkbox' ? field.checked : field.value)
      },

      shouldRenderStyle(style) {
         if (!this.config.xema || !this.elementName) {
            return false
         }
         const structureConfig = this.config.xema
         if (style === "editorInputType" && this.config.editing?.xonomyMode === "graphical") {
            if (this.attributeName) {
               return structureConfig.elements[this.elementName]?.attributes?.[this.attributeName]?.filling === "txt"
            } else {
               return structureConfig.elements[this.elementName]?.filling === "txt"
            }
         }

         if ((style === "separation" || style === "gutter")
            && structureConfig.root === this.elementName) {
            return false
         }
         if (
            (style === "innerPunc"
               || style === "weight"
               || style === "slant"
               || style === "colour"
               || style === "textsize"
            ) && (
               !structureConfig.elements[this.elementName]
               || structureConfig.elements[this.elementName].filling === "chd"
               || structureConfig.elements[this.elementName].filling === "med"
            )
         ) {
            return false
         }
         if (
            (style === "captioning")
            && (!structureConfig.elements[this.elementName]
               || structureConfig.elements[this.elementName].filling !== "lst")
         ) {
            return false
         }
         return true
      }
   }
}
</script>

<style>
display-styles .display-styles {
   margin: 0 8px;
}

display-styles .display-styles h5 {
   margin-left: 0;
}

display-styles .break {
   width: 100%;
   margin: 15px 0;
   border-bottom: 1px solid #eee;
}

display-styles .toggle-input {
   margin: 16px 0;
}

display-styles .toggle-input--preview .switch {
   margin-top: 8px;
}

display-styles .select-input {
   margin: 8px 0;
}

display-styles .display-styles > select option {
   color: black;
}

display-styles select option {
   color: black;
}

display-styles select option:first-child,
display-styles select:invalid {
   color: #aaa;
}

display-styles .section--graphical {
   position: relative;
}

display-styles .overlay--disabled {
   position: absolute;
   display: flex;
   inset: 0;
   align-items: center;
   background: rgba(100, 100, 100, 0.4);
   cursor: not-allowed;
}

display-styles .overlay--disabled .notification {
   width: 100%;
   padding: 0 16px;
   text-align: center;
   background: #f6f6f6;
}
display-styles .display-styles .textbox {
   border: 1px solid #f2f2f2;
}
</style>
