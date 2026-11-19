<template>
<div class="display-styles">
   <div class="controls">
      <div>
         <h4>
            Configuration for {{ attributeName ? `@${attributeName}` : elementName }}
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
                     @change="emit('update', 'shown', !elementData.shown)"
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
                     @change="emit('update', 'layout', elementData.layout === 'block' ? 'inline' : 'block')"
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
            <FormSelect :id="style.type" :options="selectOptions(style.values)"
               :model-value="choice(style.type)" :aria-label="style.title"
               @update:model-value="value => emit('update', style.type, value)"/>
         </div>
         <div class="break"/>
         <div class="select-input">
            <label for="label">Label</label>
            <input id="label" class="textbox" @input="setLabel" :value="elementData.label">
         </div>
      </div>
      <div v-if="elementData.shown" class="section--graphical">
         <div class="break"/>
         <h5>Graphical editor</h5>
         <div :inert="!graphical">
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
                        @change="emit('update', setting.type, elementData[setting.type] !== true)"
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
               <FormSelect :id="style.type" :options="selectOptions(style.values)"
                  :model-value="choice(style.type)" :aria-label="style.title"
                  @update:model-value="value => emit('update', style.type, value)"/>
            </div>
         </div>
         <div v-if="!graphical" class="overlay--disabled">
            <div class="notification">
               <p>Enable <b>Graphical mode</b></p>
            </div>
         </div>
      </div>
   </div>

</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { type Xema } from '../../js/xema.ts'
import { type FormattingFields } from '../../js/xemplate.ts'
import FormSelect from '../FormSelect.vue'

const props = defineProps<{
   elementName: string
   attributeName?: string
   elementData: FormattingFields
   xema: Xema
   graphical: boolean
}>()
const emit = defineEmits<{ update: [field: keyof FormattingFields, value: string | boolean] }>()

type FormatChoices = { type: keyof FormattingFields; title: string; values: { value: string; label: string }[] }

const possibleToggles = [
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
] satisfies { type: keyof FormattingFields; label: string }[]
const graphicalEditorSettings = [
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
] satisfies FormatChoices[]
const possibleStyles = [
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
            value: "hanging",
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
] satisfies FormatChoices[]

const visibleStyles = computed(() => possibleStyles.filter(style => shouldRenderStyle(style.type)))
const visibleGraphicalSettings = computed(() => graphicalEditorSettings.filter(style => shouldRenderStyle(style.type)))

function choice(key: keyof FormattingFields) {
   const value = props.elementData[key]
   return typeof value === 'string' ? value : ''
}

function selectOptions(values: { value: string; label: string }[]) {
   return [{ value: '', label: 'Select option' }, ...values]
}

function setLabel(event: Event) {
   if (event.target instanceof HTMLInputElement) emit('update', 'label', event.target.value)
}

function shouldRenderStyle(style: string) {
   const element = props.xema.elements[props.elementName]
   if (!element) return false
   const filling = props.attributeName ? element.attributes?.[props.attributeName]?.filling : element.filling
   if (style === 'editorInputType') return filling === 'txt'
   if ((style === 'separation' || style === 'gutter') && props.xema.root === props.elementName) return false
   if (['innerPunc', 'weight', 'slant', 'colour', 'textsize'].includes(style) && (filling === 'chd' || filling === 'med')) return false
   if (style === 'captioning') return filling === 'lst'
   return true
}
</script>

<style>
.display-styles .controls {
   margin: 0 8px;
}

.display-styles .controls h5 {
   margin-left: 0;
}

.display-styles .break {
   width: 100%;
   margin: 15px 0;
   border-bottom: 1px solid #eee;
}

.display-styles .toggle-input {
   margin: 16px 0;
}

.display-styles .toggle-input--preview .switch {
   margin-top: 8px;
}

.display-styles .select-input {
   margin: 8px 0;
}

.display-styles .section--graphical {
   position: relative;
}

.display-styles .overlay--disabled {
   position: absolute;
   display: flex;
   inset: 0;
   align-items: center;
   background: rgba(100, 100, 100, 0.4);
   cursor: not-allowed;
}

.display-styles .overlay--disabled .notification {
   width: 100%;
   padding: 0 16px;
   text-align: center;
   background: #f6f6f6;
}
.display-styles .controls .textbox {
   border: 1px solid #f2f2f2;
}
</style>
