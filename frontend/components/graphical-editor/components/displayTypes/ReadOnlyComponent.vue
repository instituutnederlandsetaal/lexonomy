<template>
  <div>
    <section v-if="elementData.shown">
      <p v-if="showPreview" :class="textClass">{{ label }} </p>
      <span :class="textClass"> {{ content.text }}</span>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Element } from 'xml-js'
import type { ElementDisplay } from '../../editor-schema.ts'

const props = defineProps<{ elementData: ElementDisplay; content: Element; showPreview?: boolean }>()
const textClass = computed(() => props.showPreview ? 'text--xs' : 'text--md')
const label = computed(() => props.elementData.hideElementName ? '' : props.elementData.editorLabel + ':')
</script>

<style lang="scss" scoped>
p {
  margin: 0;
  padding: 0;
  padding-bottom: 4px;
}
</style>
