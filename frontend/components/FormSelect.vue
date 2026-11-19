<script setup lang="ts" generic="Value extends string | number | boolean">
import { computed } from 'vue'
import {
   SelectContent, SelectIcon, SelectItem, SelectItemText, SelectPortal,
   SelectRoot, SelectTrigger, SelectValue, SelectViewport
} from 'reka-ui'

defineOptions({ inheritAttrs: false })

const props = defineProps<{
   modelValue?: Value | null
   options: { value: Value; label: string; disabled?: boolean }[]
   placeholder?: string
   disabled?: boolean
}>()

const emit = defineEmits<{
   'update:modelValue': [value: Value]
   change: [value: Value]
}>()

// Reka reserves the empty string. Give each choice a distinct internal value.
function optionKey(value: Value) {
   return `${typeof value}:${value}`
}

const selected = computed(() => props.options.find(option => option.value === props.modelValue))

function select(key: string) {
   const option = props.options.find(option => optionKey(option.value) === key)
   if (option && !option.disabled) {
      emit('update:modelValue', option.value)
      emit('change', option.value)
   }
}
</script>

<template>
   <SelectRoot :model-value="selected ? optionKey(selected.value) : ''" :disabled="disabled"
         @update:model-value="select">
      <SelectTrigger v-bind="$attrs" type="button" class="form-select-trigger">
         <SelectValue :placeholder="placeholder">{{ selected?.label }}</SelectValue>
         <SelectIcon as="span" class="form-select-icon" aria-hidden="true">▾</SelectIcon>
      </SelectTrigger>
      <SelectPortal>
         <SelectContent position="popper" align="start" class="form-select-content">
            <SelectViewport>
               <SelectItem v-for="option in options" :key="optionKey(option.value)" :value="optionKey(option.value)"
                     :disabled="option.disabled" class="form-select-option">
                  <SelectItemText>{{ option.label }}</SelectItemText>
               </SelectItem>
            </SelectViewport>
         </SelectContent>
      </SelectPortal>
   </SelectRoot>
</template>

<style>
.form-select-trigger {
   display: flex;
   align-items: center;
   justify-content: space-between;
   gap: .5em;
   width: 100%;
   min-height: 3rem;
   padding: 0;
   margin: 0 0 8px;
   border: 0;
   border-bottom: 1px solid #9e9e9e;
   color: inherit;
   background: transparent;
   text-align: left;
   cursor: pointer;
}
.form-select-trigger:focus-visible {
   outline: 2px solid #26a69a;
   outline-offset: 2px;
}
.form-select-trigger:disabled {
   opacity: .55;
   cursor: default;
}
.form-select-icon {
   font-size: .85rem;
}
.form-select-content {
   z-index: 1500;
   min-width: var(--reka-select-trigger-width);
   max-width: var(--reka-select-content-available-width);
   max-height: var(--reka-select-content-available-height);
   overflow-y: auto;
   background: #fff;
   box-shadow: 0 2px 5px #0004;
}
.form-select-option {
   padding: 12px 16px;
   color: #18756f;
   cursor: pointer;
}
.form-select-option[data-state="checked"], .form-select-option[data-highlighted] {
   background: #eee;
}
.form-select-option[data-disabled] {
   color: #999;
   cursor: default;
}
</style>
