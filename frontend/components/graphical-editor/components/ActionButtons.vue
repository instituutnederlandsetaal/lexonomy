<template>
   <DropdownMenuRoot v-if="!isRootElement" :modal="false">
      <DropdownMenuTrigger type="button" class="button--sm secondary" :disabled="editorLocked || disable || !hasAction"
                           @click.stop>
         {{ buttonText }}
      </DropdownMenuTrigger>
      <DropdownMenuPortal>
         <DropdownMenuContent class="graphical-action-menu" :inert="editorLocked" align="start" :side-offset="4" :collision-padding="8">
            <DropdownMenuItem v-if="canMoveUp" @select="emit('move-element-up')">
               Move {{ displayName }} <img :src="arrowUp" alt="up">
            </DropdownMenuItem>
            <DropdownMenuItem v-if="canMoveDown" @select="emit('move-element-down')">
               Move {{ displayName }} <img :src="arrowDown" alt="down">
            </DropdownMenuItem>
            <DropdownMenuSeparator v-if="canMoveUp || canMoveDown" class="break"/>
            <DropdownMenuItem v-if="canAdd && !subentryElement" @select="emit('add-element')">
               Create new {{ displayName }}
            </DropdownMenuItem>
            <DropdownMenuItem v-if="canAdd && elementEditorConfig.enableCopying && numberOfElements > 0" @select="emit('clone-element')">
               Duplicate {{ displayName }}
            </DropdownMenuItem>
            <DropdownMenuItem v-if="canAdd && subentryElement" @select="emit('link-element')">
               Add new {{ displayName }} subentry
            </DropdownMenuItem>
            <DropdownMenuItem v-if="canChangeParent" @select="emit('select-new-parent')">
               Change parent of {{ displayName }}
            </DropdownMenuItem>
            <DropdownMenuItem v-if="canAddLink" @select="emit('add-link')">Link to another element</DropdownMenuItem>
            <DropdownMenuSeparator v-if="canAdd && canRemove" class="break"/>
            <DropdownMenuItem v-if="canRemove" @select="emit('remove-element')">Remove selected {{ displayName }}</DropdownMenuItem>
         </DropdownMenuContent>
      </DropdownMenuPortal>
   </DropdownMenuRoot>
</template>

<script setup lang="ts">
import { editorLockedKey, editorContextKey } from '../editor-context.ts'
import { computed, inject } from 'vue'
import { DropdownMenuContent, DropdownMenuItem, DropdownMenuPortal, DropdownMenuRoot, DropdownMenuSeparator, DropdownMenuTrigger } from 'reka-ui'
import { maximumChildCount, xmlElementName } from '../../../js/xema.ts'
import type { ElementDisplay } from '../editor-schema.ts'
import arrowUp from '../../../assets/img/svg/arrow-up.svg'
import arrowDown from '../../../assets/img/svg/arrow-down.svg'

const props = defineProps<{
   elementName: string
   elementEditorConfig: ElementDisplay
   parentElementName?: string
   numberOfElements: number
   editorChildNumber: number
   linkSourceId?: string | number
   subentryElement?: boolean
   disable?: boolean
}>()
const emit = defineEmits<{
   'move-element-down': []; 'move-element-up': []; 'add-element': []; 'select-new-parent': [];
   'add-link': []; 'clone-element': []; 'remove-element': []; 'link-element': []
}>()
const editor = inject(editorContextKey)!
const editorLocked = inject(editorLockedKey)!
const xema = computed(() => editor.config.xema)
const isRootElement = computed(() => !props.parentElementName)
const displayName = computed(() => xmlElementName(xema.value, props.elementName))
const buttonText = computed(() => {
   if (/^sensenum[0-3]$/.test(props.elementEditorConfig.gutter ?? '')) {
      return `${props.editorChildNumber + 1}. ${displayName.value}`
   }
   return displayName.value
})
const rule = computed(() => props.parentElementName
   ? xema.value.elements[props.parentElementName]?.children?.find(child => child.name === props.elementName)
   : undefined)
const canAdd = computed(() => Boolean(rule.value && props.numberOfElements < maximumChildCount(rule.value.max)))
const canRemove = computed(() => Boolean(rule.value && props.numberOfElements > (Number(rule.value.min) || 0)))
const canMoveUp = computed(() => Boolean(props.elementEditorConfig.enablePositionChange && props.editorChildNumber > 0))
const canMoveDown = computed(() => Boolean(props.elementEditorConfig.enablePositionChange && props.editorChildNumber < props.numberOfElements - 1))
const canChangeParent = computed(() => Boolean(props.elementEditorConfig.enableParentChange && canRemove.value))
const canAddLink = computed(() => Boolean(props.linkSourceId && editor.config.linking[props.elementName]))
const hasAction = computed(() => canAdd.value || canRemove.value || canMoveUp.value || canMoveDown.value || canAddLink.value || canChangeParent.value)
</script>

<style>
.graphical-action-menu {
   width: max-content;
   min-width: 160px;
   background: #fff;
   color: #2c3e50;
   border: 1px solid #d9eaff;
   border-radius: 4px;
   box-shadow: 0 8px 16px #0003;
   z-index: 1100;
}
.graphical-action-menu [role="menuitem"] {
   padding: 6px 12px;
   cursor: pointer;
   outline: none;
}
.graphical-action-menu [data-highlighted] { background: #d9eaff; }
.graphical-action-menu img { width: 1em; height: 1em; }
.graphical-action-menu .break { border-bottom: 1px solid #d9eaff; }
</style>
