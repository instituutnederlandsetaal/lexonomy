<template>
   <div>
      <section v-for="(candidate, index) in content" :key="index" class="component drop-shadow--100"
               role="button" tabindex="0" @click="emit('selected-element', candidate)"
               @keydown.enter.prevent="emit('selected-element', candidate)"
               @keydown.space.prevent="emit('selected-element', candidate)">
         <InlineComponent :element-name="candidate.elementName" :content="candidate.node"
                    :children="childrenFor(xema, candidate.elementName, candidate.node)"
                    :element-data="{ ...elementDisplay(config.xemplate, xema, candidate.elementName), hideElementName: false }"
                    :parent-element-name="candidate.parentElementName" :editor-child-number="0" :number-of-elements="1"
                    show-elements-preview :max-displayed-children="5"/>
      </section>
   </div>
</template>

<script setup lang="ts">
import { editorContextKey } from '../editor-context.ts'
import { computed, inject } from 'vue'
import { childrenFor, elementDisplay, type ParentCandidate } from '../editor-schema.ts'
import InlineComponent from './displayTypes/InlineComponent.vue'

defineProps<{ content: ParentCandidate[] }>()
const emit = defineEmits<{ 'selected-element': [candidate: ParentCandidate] }>()
const editor = inject(editorContextKey)!
const config = computed(() => editor.config)
const xema = computed(() => config.value.xema)
</script>

<style scoped>
.component {
   display: flex;
   margin: 8px;
   padding: 8px;
   text-align: left;
   cursor: pointer;
}
.component:hover, .component:focus-visible { box-shadow: 0 2px 14px #18181833; }
</style>
