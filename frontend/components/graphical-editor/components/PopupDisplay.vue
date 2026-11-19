<template>
   <DialogRoot :open="modelValue" @update:open="open => { if (!open) cancel() }">
      <DialogPortal>
         <DialogOverlay class="editor-dialog-overlay" :style="{ zIndex }"/>
         <DialogContent v-bind="$attrs" class="editor editor-dialog" :class="{ 'full-height': fullHeight }"
                        :style="{ zIndex }" :inert="editorLocked" :aria-describedby="undefined"
                        @interact-outside="maybePreventOutsideDismiss" @close-auto-focus="restoreFocus">
            <VisuallyHidden as-child><DialogTitle>{{ title }}</DialogTitle></VisuallyHidden>
            <button type="button" class="close" aria-label="Close dialog" @click="cancel">×</button>
            <slot/>
            <div v-if="!hideActions" class="default-actions">
               <button type="button" :disabled="saveDisabled" @click="emit('save')">Ok</button>
               <button type="button" @click="cancel">Cancel</button>
            </div>
         </DialogContent>
      </DialogPortal>
   </DialogRoot>
</template>

<script setup lang="ts">
import { editorLockedKey } from '../editor-context.ts'
import { inject, watch } from 'vue'
import { DialogContent, DialogOverlay, DialogPortal, DialogRoot, DialogTitle, VisuallyHidden } from 'reka-ui'

defineOptions({ inheritAttrs: false })
const props = withDefaults(defineProps<{
   modelValue: boolean
   title: string
   zIndex?: string
   fullHeight?: boolean
   preventOutsideDismiss?: boolean
   hideActions?: boolean
   saveDisabled?: boolean
}>(), { zIndex: '20', fullHeight: true })
const emit = defineEmits<{ 'update:modelValue': [open: boolean]; cancel: []; save: [] }>()
const editorLocked = inject(editorLockedKey)!
let trigger: HTMLElement | null = null
watch(() => props.modelValue, open => {
   if (open) trigger = document.activeElement instanceof HTMLElement ? document.activeElement : null
}, { immediate: true })

function cancel() {
   emit('update:modelValue', false)
   emit('cancel')
}

function maybePreventOutsideDismiss(event: Event) {
   if (props.preventOutsideDismiss) event.preventDefault()
}

function restoreFocus(event: Event) {
   if (!trigger?.isConnected) return
   event.preventDefault()
   trigger.focus()
}
</script>

<style scoped>
.editor-dialog-overlay {
   position: fixed;
   inset: 0;
   background: #0006;
}
.editor-dialog {
   position: fixed;
   top: 50%;
   left: 50%;
   transform: translate(-50%, -50%);
   width: 80%;
   max-height: 70vh;
   overflow-y: auto;
   padding: 15px 12px;
   border: 1px solid #888;
   border-radius: 16px;
   background: #fefefe;
}
.editor-dialog.full-height { height: calc(100vh - 60px); max-height: calc(100vh - 60px); }
.editor-dialog .close {
   border: 0;
   background: none;
   padding: 0 4px;
   color: #637383;
   float: right;
   font-size: 28px;
   cursor: pointer;
}
.editor-dialog .close:hover { color: #000; }
.default-actions {
   display: flex;
   flex-direction: row-reverse;
   gap: 16px;
   position: sticky;
   bottom: 0;
   margin-top: 24px;
   padding: 8px 0;
   background: #fff;
}
</style>
