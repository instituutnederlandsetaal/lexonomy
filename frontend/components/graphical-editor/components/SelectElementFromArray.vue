<template>
   <PopupDisplay :model-value="modelValue" :title="`Move selected ${name}`"
                 :z-index="zIndex" hide-actions @update:model-value="emit('update:modelValue', $event)">
      <h2>Move selected {{ name }} to:</h2>
      <div v-if="possibleParentElements.length" class="parents">
         <ReadOnlyComponentGenerator :content="possibleParentElements" @selected-element="select"/>
      </div>
      <p v-else>No other parent can contain this element.</p>
      <div class="actions">
         <button type="button" @click="emit('update:modelValue', false)">Cancel</button>
      </div>
   </PopupDisplay>
</template>

<script setup lang="ts">
import type { ParentCandidate } from '../editor-schema.ts'
import PopupDisplay from './PopupDisplay.vue'
import ReadOnlyComponentGenerator from './ReadOnlyComponentGenerator.vue'

withDefaults(defineProps<{
   modelValue: boolean
   zIndex?: string
   name: string
   possibleParentElements: ParentCandidate[]
}>(), { zIndex: '100' })
const emit = defineEmits<{ 'update:modelValue': [open: boolean]; 'selected-element': [candidate: ParentCandidate] }>()

function select(candidate: ParentCandidate) {
   emit('selected-element', candidate)
   emit('update:modelValue', false)
}
</script>

<style scoped>
.parents { margin: 24px 0; }
</style>
