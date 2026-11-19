<template>
  <div class="editor">
    <EntryDisplay ref="entry" @dirty-change="$emit('dirty-change', $event)" />
  </div>
</template>

<script>
import { xml2js } from 'xml-js'
import EntryDisplay from './components/EntryDisplay.vue'
import InlineComponent from './components/displayTypes/InlineComponent.vue'
import PopupComponent from './components/displayTypes/PopupComponent.vue'
import SubentryComponent from './components/displayTypes/SubentryComponent.vue'
import ReadOnlyComponent from './components/displayTypes/ReadOnlyComponent.vue'
import DropdownComponent from './components/displayTypes/DropdownComponent.vue'
import MediaComponent from './components/displayTypes/MediaComponent.vue'
import TextInputComponent from './components/displayTypes/TextInputComponent.vue'
import TextInputWithMarkupComponent from './components/displayTypes/TextInputWithMarkupComponent.vue'

const editorComponents = {
  InlineComponent, PopupComponent, SubentryComponent, ReadOnlyComponent,
  DropdownComponent, MediaComponent, TextInputComponent, TextInputWithMarkupComponent
}

export default {
  components: { EntryDisplay },
  props: {
    entry: { type: Object, required: true }
  },
  emits: ['dirty-change', 'links-changed'],
  data() {
    const xml2jsConfig = { compact: false, captureSpacesBetweenElements: true }
    const { dictId, userDicts, doctype, dictConfigs, xml } = this.entry
    return {
      editorState: {
        entry: {
          dictId, userDicts, doctype,
          dictConfigs: JSON.parse(JSON.stringify(dictConfigs)),
          content: xml2js(xml, xml2jsConfig)
        },
        xml2jsConfig,
        initialContent: xml2js(xml, xml2jsConfig),
        headwordElement: null,
        headwordData: null,
        openedPopups: []
      }
    }
  },
  provide() {
    return {
      editorState: this.editorState,
      editorComponents,
      editorBus: new EventTarget(),
      requiredFields: new Set(),
      notifyLinksChanged: () => this.$emit('links-changed', this.entry.id)
    }
  },
  methods: {
    harvest() {
      return this.$refs.entry.getXmlData()
    }
  }
}
</script>

<style lang="scss" >
$blue-100: #D9EAFF;
$blue-200: #B3D6FF;
$blue-300: #0077FF;
$blue-400: #005FCC;
$blue-500: #004494;
$blue-600: #023672;

.editor {
  font-family: 'Cairo', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: left;
  color: #2c3e50;

  .read-only {
    margin-bottom: 4px;
    display: inline-flex;

    p {
      margin: 0;
      margin-right: 4px;
      text-align: left;
      //font-size: 14px;
      //line-height: 18px;
    }
  }

  h1 {
    font-size: 32px;
    line-height: 40px;
    font-weight: bold;
  }

  h2 {
    font-size: 24px;
    line-height: 30px;
    font-weight: bold;
    margin: 0 0 1.424rem 0;
  }

  h3 {
    font-size: 16px;
    line-height: 20px;
    font-weight: bold;
  }

  .sub-h1 {
    font-size: 24px;
    line-height: 30px;
    font-weight: 500;
  }

  .sub-h1 {
    font-size: 20px;
    line-height: 28px;
    font-weight: 500;
  }

  .sub-h3 {
    font-size: 14px;
    line-height: 16px;
    font-weight: 500;
  }

  .text {
    &--lg {
      font-size: 18px;
      line-height: 24px;
    }

    &--md {
      font-size: 16px;
      line-height: 20px;
    }

    &--sm {
      font-size: 14px;
      line-height: 18px;
    }

    &--xs {
      font-size: 12px;
      line-height: 16px;
    }
  }

  .drop-shadow {
    &--100 {
      box-shadow: 0px 0px 8px rgba(0, 0, 0, 0.1);
      border-radius: 8px;
    }
  }

  button {
    margin: 0;
    padding: 2.5px 14px;
    color: #fff;
    border: 1px solid $blue-400;
    border-radius: 8px;
    background-color: $blue-400;
    font-size: 14px;
    line-height: 28px;
    font-weight: 600;
    cursor: pointer;
    transition: 0.1s all;

    &.secondary {
      color: $blue-500;
      background-color: $blue-100;
      border-color: $blue-100;
      box-shadow: none;

      &:hover {
        color: #fff;
        background-color: $blue-400;
        border-color: $blue-400;
      }

      &:focus {
        color: $blue-500;
        background-color: $blue-100;
        border-color: #F48C06;
      }
    }

    &.tertiary {
      color: $blue-400;
      background-color: transparent;
      border-color: transparent;
      box-shadow: none;

      &:hover {
        color: $blue-500;
        background-color: transparent;
        border-color: transparent;
      }

      &:focus {
        color: $blue-400;
        background-color: transparent;
        border-color: #F48C06;
      }

      &:disabled,
      &[disabled] {
        background-color: transparent;
        color: #B6BFC9;
        border-color: transparent;
        pointer-events: none;
        cursor: not-allowed;
      }
    }

    &:hover {
      background-color: $blue-500;
      border-color: $blue-500;
    }

    &:focus {
      border-color: #E85D04;
    }

    &.button--lg {
      padding: 10px 24px;
      font-size: 18px;
      line-height: 28px;
    }

    &.button--md {
      padding: 5px 16px;
      font-size: 16px;
      line-height: 30px;
    }

    &.button--sm {
      padding: 2.5px 14px;
      font-size: 14px;
      line-height: 28px;
    }


    &:disabled,
    &[disabled] {
      border-color: #C7D0DD;
      background-color: #C7D0DD;
      color: #8599AD;
      pointer-events: none;
      cursor: not-allowed;
    }
  }

  span[contenteditable] {
    margin: 0;
    padding: 14px 0 14px 17px;
    color: $blue-400;
    font-size: 14px;
    line-height: 18px;
    font-weight: 400;
    border-radius: 4px;
    outline: none;
    transition: 0.1s all;

    &::placeholder {
      color: #B6BFC9;
    }

    &:disabled,
    &[disabled] {
      border: 1px solid #C7D0DD;
      color: #B6BFC9;
    }
  }


  .dropdown-content {
    background: #FFFFFF;
    box-shadow: 0px 2px 14px rgba(2, 54, 114, 0.3);
    border-radius: 4px;

    li {
      &:hover,
      &.selected {
        span {
          background-color: #EDF1F7;
        }
      }

      span {
        color: #637383;
      }

    }
  }

}

#editor {
  .content {
    min-height: 0;
  }

  .select-wrapper {
    flex: 1;

    ul {
      width: 100% !important;
    }
  }

  .error {
    input,
    textarea {
      color: #637383 !important;
      border-color: #FB4646 !important;
      background-color: #FFF2F2 !important;

      &::placeholder {
        color: #637383;
      }
    }

    .select-wrapper {
      .caret {
        z-index: 1;
      }
    }
  }

  input,
  textarea {
    margin: 0;
    padding: 14px 0 14px 17px;
    color: $blue-400;
    font-size: 14px;
    line-height: 18px;
    font-weight: 400;
    border: 1px solid $blue-400;
    border-radius: 4px;
    outline: none;
    transition: 0.1s all;

    &::placeholder {
      color: #B6BFC9;
      //color: #637383;
    }

    &:hover {
      color: $blue-500;
      border: 1px solid $blue-500;
    }

    &:focus {
      color: #637383;
      border: 1px solid #E85D04;
    }

    &.error {
      color: #637383;
      border-color: #FB4646;
      background-color: #FFF2F2;
    }

    &:disabled,
    &[disabled] {
      border: 1px solid #C7D0DD;
      color: #B6BFC9;
    }
  }
}
</style>
