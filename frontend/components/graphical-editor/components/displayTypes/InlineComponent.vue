<template>
  <div class="inline-component" :class="{'read-only': showElementsPreview, 'element-hidden': !elementData.shown}"
       :style="configStyles">
    <section v-if="elementData.shown && !readOnly" class="content">
      <ActionButtons
        v-if="!isAttribute"
        class="actions-button"
        :elementName="elementName"
        :elementEditorConfig="elementData"
        :editorChildNumber="editorChildNumber"
        :parentElementName="parentElementName"
        :numberOfElements="numberOfElements"
        :link-source-id="content.attributes?.['lxnm:linkable']"
        v-on="actions"
        @add-link="showSelectLinkedElement = true"
      />
      <component :is="valueComponent"
                 class="value-display"
                 :class="{'value-display--attribute': isAttribute}"
                 :elementName="elementName"
                 :elementData="elementData"
                 :content="componentData"
                 v-bind="showChildren ? {} : { children }"
                 :isAttribute="isAttribute"
                 :parentElementName="parentElementName"
                 :showPreview="showElementsPreview"
                 @input="commitValue"
      />
    </section>
    <section v-if="!isElementHidden && readOnly" class="content">
        <ActionButtons
                v-if="!showElementsPreview && !isAttribute"
                class="actions-button"
                :elementName="elementName"
                :elementEditorConfig="elementData"
                :editorChildNumber="editorChildNumber"
                :parentElementName="parentElementName"
                :numberOfElements="numberOfElements"
                :disable="true"
        />
      <component :is="valueComponent"
                 :class="{'read-only-element': !showElementsPreview}"
                 :elementName="elementName"
                 :elementData="elementData"
                 :content="componentData"
                 v-bind="showChildren ? {} : { children }"
                 :isAttribute="isAttribute"
                 :parentElementName="parentElementName"
                 :showPreview="showElementsPreview"
      />
    </section>
    <ComponentGeneratorComponent
      v-if="showChildren"
      :children="children"
      :elementName="elementName"
      :content="content"
      :showElementsPreview="showElementsPreview"
      :maxDisplayedChildren="maxDisplayedChildren"
      @input="change => commitContent(change.content)"
    />
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
      :sourceId="content.attributes && content.attributes['lxnm:linkable']"
      :element-name="elementName"
    />

  </div>
</template>

<script setup lang="ts">
import { computed, inject, ref } from 'vue'
import { editorContextKey } from '../../editor-context.ts'
import { useFieldActions, useFieldValue, type EditorFieldProps, type EmitField, type ValueUpdate } from '../../use-editor-field.ts'
import ActionButtons from '../ActionButtons.vue'
import ComponentGeneratorComponent from '../ComponentGeneratorComponent.vue'
import LinkingElementSelector from '../LinkingElementSelector.vue'
import SelectElementFromArray from '../SelectElementFromArray.vue'

const props = withDefaults(defineProps<EditorFieldProps & { hideEmptyElements?: boolean; maxDisplayedChildren?: number }>(),
   { maxDisplayedChildren: -1 })
const emit = defineEmits<EmitField>()
const { actions, newPossibleParents, showSelectNewParent, handleSelectedNewParent } = useFieldActions(props, emit)
const showSelectLinkedElement = ref(false)
const { componentData, valueComponent, showChildren, updateValue, commitContent } = useFieldValue(props, emit)
const editor = inject(editorContextKey)!
const readOnly = computed(() => props.elementData.readOnly || props.showElementsPreview)
const configStyles = computed(() => !props.showElementsPreview && props.elementData.border
   ? { border: `1px ${props.elementData.border} #B3D6FF` } : undefined)
const isElementHidden = computed(() => {
   if (!props.elementData.shown) return true
   const filling = editor.config.xema.elements[props.elementName]?.filling
   return props.hideEmptyElements && (filling === 'chd' || filling === 'emp')
})

function commitValue(value: ValueUpdate) {
   commitContent(updateValue(props.content, value))
}
</script>

<style lang="scss" scoped>
.inline-component {
  margin-bottom: 8px;
  padding: 8px 4px 0 4px;

  .actions-button {
    margin-right: 8px;

    &.hide {
      display: block !important;
      visibility: hidden;
      opacity: 0;
      pointer-events: none;
    }
  }

  .content {
    display: flex;

    .value-display {
      flex: 1;
      &.value-display--attribute {
        margin-left: 14px;
      }
    }

    .read-only-element {
      display: flex;
      align-items: center;
    }
  }

  &.element-hidden {
    padding: 0;
  }

  &.read-only {
    padding: 0;
    margin-bottom: 0;
    text-align: left;

    p {
      padding: 0;
      padding-bottom: 4px;
    }

  }

}

</style>
