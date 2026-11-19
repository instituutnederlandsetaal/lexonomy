<template>
   <div ref="surface" class="editor">
      <EntryDisplay ref="entryDisplay" :content="content" :original-xml="xml"
                    @dirty-change="reportEntryDirty"/>
   </div>
</template>

<script setup lang="ts">
import { editorContextKey, notifyLinksChangedKey, requiredFieldsKey, schemaAncestorsKey, setPopupDirtyKey } from './editor-context.ts'
import { computed, provide, ref } from 'vue'
import { xml2js, type Element } from 'xml-js'
import type { EditorContext } from './editor-context.ts'
import EntryDisplay from './components/EntryDisplay.vue'

const props = defineProps<EditorContext & { xml: string }>()
const emit = defineEmits<{ 'dirty-change': [dirty: boolean]; 'links-changed': [] }>()
const entryDisplay = ref<InstanceType<typeof EntryDisplay> | null>(null)
const surface = ref<HTMLElement | null>(null)
const entryDirty = ref(false)
const dirtyPopups = new Set<symbol>()
const content = xml2js(props.xml, { compact: false, captureSpacesBetweenElements: true }) as Element
provide(editorContextKey, props)
provide(schemaAncestorsKey, computed(() => []))
provide(requiredFieldsKey, new Set<() => string | undefined>())
provide(notifyLinksChangedKey, () => emit('links-changed'))
provide(setPopupDirtyKey, (popup, dirty) => {
   if (dirty) dirtyPopups.add(popup)
   else if (!dirtyPopups.delete(popup)) return
   emit('dirty-change', entryDirty.value || Boolean(dirtyPopups.size))
})

function reportEntryDirty(dirty: boolean) {
   entryDirty.value = dirty
   emit('dirty-change', dirty || Boolean(dirtyPopups.size))
}
defineExpose({
   harvest() {
      const focused = document.activeElement
      if (focused instanceof HTMLElement && surface.value?.contains(focused)) focused.blur()
      return entryDisplay.value?.harvest()
   }
})
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



}

#editor {
  .content {
    min-height: 0;
  }

  .error {
    input,
    textarea,
    .form-select-trigger {
      color: #637383 !important;
      border-color: #FB4646 !important;
      background-color: #FFF2F2 !important;

      &::placeholder {
        color: #637383;
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
