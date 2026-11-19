<template>
  <div class="popup-component" :class="{'element-hidden': !elementData.shown}">
    <div>
      <section v-if="elementData.shown" class="preview drop-shadow--100">
        <ActionButtons
          v-if="!isAttribute"
          class="actions-button"
          :elementName="elementName"
          :elementEditorConfig="elementData"
          :editorChildNumber="editorChildNumber"
          :parentElementName="parentElementName"
          :numberOfElements="numberOfElements"
          :link-source-id="calculatedContent.attributes?.['lxnm:linkable']"
          v-on="actions"
          @add-link="showSelectLinkedElement = true"
        />
        <section class="preview-body">
          <button type="button" class="preview-open" :aria-label="`Edit ${xmlName}`" @click="openPopup"></button>
          <component :is="valueComponent"
                     class="preview-element text--md"
                     :elementName="elementName"
                     :elementData="elementData"
                     :content="componentData"
                     v-bind="showChildren ? {} : { children }"
                     :isAttribute="isAttribute"
                     :parentElementName="parentElementName"
                     :showPreview="true"
              />

          <ComponentGeneratorComponent
            v-if="showChildren"
            class="preview-components"
            :children="children"
            :elementName="elementName"
            :content="content"
            :showElementsPreview="true"
            :hideEmptyElements="true"
            :maxDisplayedChildren="5"
          />
        </section>
      </section>
      <PopupDisplay v-model="showPopup"
                    :fullHeight="false"
                    prevent-outside-dismiss
                    :title="`Edit ${xmlName}`"
                    @cancel="handleCancel"
                    @save="handleSave"
      >
        <component
          v-if="elementData.shown"
          :is="valueComponent"
          :elementName="elementName"
          :elementData="elementData"
          :content="componentData"
          v-bind="showChildren ? {} : { children }"
          :isAttribute="isAttribute"
          :parentElementName="parentElementName"
          @input="updatePopupValue"
        />
        <ComponentGeneratorComponent
          v-if="showChildren"
          :children="children"
          :elementName="elementName"
          :content="calculatedContent"
          @input="change => updatePopup(change.content)"
        />
      </PopupDisplay>
    </div>
    <SelectElementFromArray
      v-if="showSelectNewParent"
      v-model="showSelectNewParent"
      :name="elementData.editorLabel"
      :possible-parent-elements="newPossibleParents"
      @selected-element="handleSelectedNewParent"
    />
    <LinkingElementSelector
      v-if="showSelectLinkedElement"
      v-model="showSelectLinkedElement"
      :sourceId="calculatedContent.attributes && calculatedContent.attributes['lxnm:linkable']"
      :element-name="elementName"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, inject, onBeforeUnmount, ref, shallowRef } from 'vue'
import type { Element } from 'xml-js'
import { editorContextKey, provideEditorDraft, setPopupDirtyKey } from '../../editor-context.ts'
import { serializeDraft } from '../../editor-schema.ts'
import { useFieldActions, useFieldValue, type EditorFieldProps, type EmitField, type ValueUpdate } from '../../use-editor-field.ts'
import { xmlElementName } from '../../../../js/xema.ts'
import ActionButtons from '../ActionButtons.vue'
import ComponentGeneratorComponent from '../ComponentGeneratorComponent.vue'
import LinkingElementSelector from '../LinkingElementSelector.vue'
import PopupDisplay from '../PopupDisplay.vue'
import SelectElementFromArray from '../SelectElementFromArray.vue'

const props = defineProps<EditorFieldProps>()
const emit = defineEmits<EmitField>()
const { actions, newPossibleParents, showSelectNewParent, handleSelectedNewParent } = useFieldActions(props, emit)
const showSelectLinkedElement = ref(false)
const editor = inject(editorContextKey)!
const setPopupDirty = inject(setPopupDirtyKey)!
const popupId = Symbol('Element draft')
const showPopup = ref(false)
const unsavedData = shallowRef<Element | null>(null)
const calculatedContent = computed(() => unsavedData.value ?? props.content)
const xmlName = computed(() => xmlElementName(editor.config.xema, props.elementName))
const { componentData, valueComponent, showChildren, updateValue, commitContent } = useFieldValue(props, emit, () => calculatedContent.value)
provideEditorDraft(() => unsavedData.value, updatePopup,
   () => ({ elementName: props.elementName, parentElementName: props.parentElementName }))
onBeforeUnmount(() => setPopupDirty(popupId, false))

function openPopup() {
   unsavedData.value = JSON.parse(JSON.stringify(props.content))
   showPopup.value = true
}

function updatePopup(content: Element) {
   unsavedData.value = content
   setPopupDirty(popupId, serializeDraft(content) !== serializeDraft(props.content))
}

function updatePopupValue(value: ValueUpdate) {
   updatePopup(updateValue(calculatedContent.value, value))
}

function handleCancel() {
   setPopupDirty(popupId, false)
   showPopup.value = false
   unsavedData.value = null
}

function handleSave() {
   const content = unsavedData.value
   handleCancel()
   if (content) commitContent(content)
}
</script>

<style lang="scss" scoped>
.preview-body { position: relative; flex: 1; }
.preview-body .preview-open {
  position: absolute;
  inset: 0;
  width: 100%;
  border: 0;
  background: transparent;
  cursor: pointer;
}
.preview-body .preview-open:focus-visible { outline: 2px solid #005fcc; }

.popup-component {
  padding: 8px 16px;
  margin-bottom: 8px;

  &.element-hidden {
    padding: 0;
  }

  .preview {
    display: flex;
    padding: 8px;
    text-align: left;
    cursor: pointer;
    transition: 0.3s all;


    &:hover {
      box-shadow: 0px 2px 14px rgba(24, 24, 24, 0.2);
    }

    .actions-button {
      margin-right: 8px;
    }

    .preview-element {
      margin-left: -8px;
    }
  }
}

</style>
