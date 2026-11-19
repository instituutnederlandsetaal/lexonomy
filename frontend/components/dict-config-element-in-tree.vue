<template>
<div class="dict-config-element-in-tree container" :class="{ collapsed: !expanded, hasChildren }">
    <div class="horizontal">
        <button v-if="hasChildren" type="button" class="plusminus"
            :aria-label="expanded ? 'Collapse element' : 'Expand element'" :aria-expanded="expanded" @click="expanded = !expanded"/>
    </div>

    <button type="button" class="clickable element" :class="{ current: currentElement === id && !currentAttribute }"
        @click="emit('select', id)">
        <span class="tech">
            <span class="brak">&lt;</span>
            <span class="elm">{{ xmlElementName(xema, id) }}</span>
            <span class="brak">&gt;</span>
        </span>
    </button>

    <div v-if="hasChildren && expanded" class="children">
        <DictConfigAttributeInTree v-for="attribute in attributes"
            :key="attribute"
            :id="attribute"
            :selected="currentAttribute === attribute && currentElement === id"
            @select="emit('select', id, attribute)"
        />
        <DictConfigElementInTree v-for="(child, index) in children"
            :key="`${child.name}-${index}`"
            :id="child.name"
            :ancestors="[...ancestors, id]"
            :xema="xema"
            :current-element="currentElement"
            :current-attribute="currentAttribute"
            @select="(element, attribute) => emit('select', element, attribute)"
        />
    </div>
</div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { xmlElementName, type Xema } from '../js/xema.ts'
import DictConfigAttributeInTree from './dict-config-attribute-in-tree.vue'

const props = withDefaults(defineProps<{
   id: string
   xema: Xema
   ancestors?: string[]
   currentElement?: string
   currentAttribute?: string
}>(), { ancestors: () => [] })
const emit = defineEmits<{ select: [element: string, attribute?: string] }>()

const expanded = ref(props.ancestors.length < 3)
const element = computed(() => props.xema.elements[props.id])
const attributes = computed(() => Object.keys(element.value?.attributes ?? {}).sort((a, b) => a.localeCompare(b)))
const children = computed(() => (element.value?.children ?? []).filter(child => Object.hasOwn(props.xema.elements, child.name)))
const hasChildren = computed(() => !props.ancestors.includes(props.id) && Boolean(attributes.value.length || children.value.length))
</script>

<style>
.dict-config-element-in-tree {
    position: relative;
    display: block;
    width: auto!important;
}
/* Hide the part of the parent line below the last child. */
.dict-config-element-in-tree:last-child:before {
    content: "";
    display: block;
    position: absolute;
    left: -16px;
    bottom: 0;
    width: 2px;
    top: 16px;
    background: white;
}
.dict-config-element-in-tree .horizontal button.plusminus,
.dict-config-element-in-tree button.clickable,
.dict-config-attribute-in-tree button.clickable {
    border: 0;
    background-color: transparent;
}
</style>
