<template>
  <div class="popup-component" :class="{'element-hidden': !elementData.shown}">
    <div>
      <section v-if="elementData.shown" class="preview drop-shadow--100" @click="openPopup">
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
        <section>
          <component :is="editorComponents[valueComponent]"
                     class="preview-element text--md"
                     :elementName="elementName"
                     :elementData="elementData"
                     :content="componentData"
                     :isAttribute="isAttribute"
                     :parentElementName="parentElementName"
                     :showPreview="true"
                     @hide-children="hideChildren"
          />

          <ComponentGeneratorComponent
            v-if="showChildren"
            class="preview-components"
            :children="children"
            :elementName="elementName"
            :content="viewOnlyContent"
            :showElementsPreview="true"
            :hideEmptyElements="true"
            :maxDisplayedChildren="5"
          />
        </section>
      </section>
      <PopupDisplay v-model="showPopup"
                    :fullHeight="false"
                    :forceButtonClose="true"
                    @cancel="handleCancel"
                    @save="handleSave"
      >
        <component
          v-if="elementData.shown"
          :is="editorComponents[valueComponent]"
          :elementName="elementName"
          :elementData="elementData"
          :content="componentData"
          :isAttribute="isAttribute"
          :parentElementName="parentElementName"
          @hide-children="hideChildren"
          @input="handleTempValueUpdate"
        />
        <ComponentGeneratorComponent
          v-if="showChildren"
          :children="children"
          :elementName="elementName"
          :content="calculatedContent"
          @input="handleTempChildUpdate"
        />
      </PopupDisplay>
    </div>
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
import PopupDisplay from "../PopupDisplay.vue"
import SelectElementFromArray from "../SelectElementFromArray.vue"
import LinkingElementSelector from "../LinkingElementSelector.vue"

export default {
  inject: ['editorComponents'],
  name: "PopupComponent",
  components: {
    LinkingElementSelector,
    ComponentGeneratorComponent,
    ActionButtons,
    PopupDisplay,
    SelectElementFromArray
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
    editorChildNumber: Number,
    isAttribute: Boolean,
    showElementsPreview: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    viewOnlyContent() {
      return this.updatedContent || this.content
    },
    calculatedContent() {
      return this.unsavedData || this.viewOnlyContent
    }
  },
  data() {
    return {
      showPopup: false,
      showChildren: true,
      updatedContent: null,
      unsavedData: null
    }
  },
  methods: {
    openPopup() {
      this.unsavedData = JSON.parse(JSON.stringify(this.viewOnlyContent))
      this.showPopup = true
    },
    handleCancel() {
      this.showPopup = false
      this.unsavedData = null
    },
    handleSave() {
      const content = this.unsavedData
      this.handleCancel()
      if (this.isAttribute) {
        this.handleValueUpdate({ attributes: { [content.name]: content.text } })
      } else {
        this.handleChildUpdate({ content })
      }
    },
    handleTempValueUpdate(data) {
      if (this.isAttribute) {
        this.unsavedData.text = data.attributes[this.unsavedData.name]
      } else {
        this.unsavedData.elements = data.elements
      }
    },
    handleTempChildUpdate(data) {
      this.unsavedData = data.content
    }
  }
}
</script>

<style lang="scss" scoped>
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
