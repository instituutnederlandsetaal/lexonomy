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
        @move-element-down="moveElementDown"
        @move-element-up="moveElementUp"
        @add-element="createSibling"
        @select-new-parent="selectNewParent"
        @add-link="addLink"
        @clone-element="cloneElement"
        @remove-element="deleteElement"
      />
      <component :is="editorComponents[valueComponent]"
                 class="value-display"
                 :class="{'value-display--attribute': isAttribute}"
                 :elementName="elementName"
                 :elementData="elementData"
                 :content="componentData"
                 :children="children"
                 :isAttribute="isAttribute"
                 :parentElementName="parentElementName"
                 :showPreview="showElementsPreview"
                 @hide-children="hideChildren"
                 @input="handleValueUpdate"
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
      <component :is="editorComponents[valueComponent]"
                 :class="{'read-only-element': !showElementsPreview}"
                 :elementName="elementName"
                 :elementData="elementData"
                 :content="componentData"
                 :children="children"
                 :isAttribute="isAttribute"
                 :parentElementName="parentElementName"
                 :showPreview="showElementsPreview"
                 @hide-children="hideChildren"
      />
    </section>
    <ComponentGeneratorComponent
      v-if="valueComponent !== 'TextInputWithMarkupComponent'"
      :children="children"
      :elementName="elementName"
      :content="calculatedContent"
      :showElementsPreview="showElementsPreview"
      :maxDisplayedChildren="maxDisplayedChildren"
      @input="handleChildUpdate"
    />
    <SelectElementFromArray
      v-if="showSelectNewParent"
      v-model="showSelectNewParent"
      :element-name="elementName"
      :possible-parent-elements="newPossibleParents"
      :parentElementName="parentElementName"
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

<script>

import ComponentGeneratorComponent from "../ComponentGeneratorComponent.vue"
import ActionButtons from "../ActionButtons.vue"
import layoutElementMixin from "../../shared-resources/mixins/layoutElementMixin.js"
import SelectElementFromArray from "../SelectElementFromArray.vue"
import LinkingElementSelector from "../LinkingElementSelector.vue"

export default {
  inject: ['editorState', 'editorComponents'],
  name: "InlineComponent",
  components: {
    LinkingElementSelector,
    SelectElementFromArray,
    ActionButtons,
    ComponentGeneratorComponent
  },
  mixins: [
    layoutElementMixin
  ],
  emits: ['input', 'move-element', 'create-element', 'delete-element', 'clone-element'],
  props: {
    children: Array,
    elementData: Object,
    elementName: String,
    parentElementName: String,
    numberOfElements: Number,
    content: {
      type: [Object, Array],
      required: true
    },
    childrenContent: Object,
    editorChildNumber: Number,
    isAttribute: Boolean,
    showElementsPreview: {
      type: Boolean,
      default: false
    },
    hideEmptyElements: {
      type: Boolean,
      default: false
    },
    maxDisplayedChildren: {
      type: Number,
      default: -1
    }
  },
  computed: {
    isElementHidden() {
      if (!this.elementData.shown) {
        return true
      }
      if (this.hideEmptyElements) {
        const xema = this.editorState.entry.dictConfigs.xema.elements[this.elementName]
        return xema ? ["chd", "emp"].includes(xema && xema.filling) : false
      }
      return false
    }
  }
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
