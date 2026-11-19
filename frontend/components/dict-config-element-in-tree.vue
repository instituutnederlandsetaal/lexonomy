<template>
<dict-config-element-in-tree class="container" :class="{ collapsed: !expanded, hasChildren }">
    <div class="horizontal">
        <span v-if="hasChildren" class="plusminus" @click="expanded = !expanded"></span>
    </div>

    <div class="clickable element" :class="{ current: currentElement === data.id && !currentAttribute }"
        @click="selectElementOrAttribute(data.id, undefined)">
        <span class="tech">
            <span class="brak">&lt;</span>
            <span class="elm">{{ data.elementName || data.id }}</span>
            <span class="brak">&gt;</span>
        </span>
    </div>

    <div v-if="hasChildren && expanded && depth < 15" class="children">
        <DictConfigAttributeInTree v-for="att in attributes"
            :key="att.id"
            :data="att"
            :parent-element="data"
            :current-element="currentElement"
            :current-attribute="currentAttribute"
            :select-element-or-attribute="selectElementOrAttribute"
        />
        <!-- pass a high depth if this element is recursive, so we stop the recursion. -->
        <DictConfigElementInTree v-for="(child, index) in children"
            :key="index"
            :depth="child.id === data.id ? 100 : depth + 1"
            :data="child"
            :xema="xema"
            :current-element="currentElement"
            :current-attribute="currentAttribute"
            :select-element-or-attribute="selectElementOrAttribute"
        />

    </div>

</dict-config-element-in-tree>
</template>

<script>
import DictConfigAttributeInTree from './dict-config-attribute-in-tree.vue'
export default {
   components: { DictConfigAttributeInTree },
   props: {
      data: Object,
      depth: { type: Number, default: 0 },
      xema: Object,
      currentElement: String,
      currentAttribute: String,
      selectElementOrAttribute: Function
   },

   data() {
      return { expanded: true }
   },

   computed: {
      children() {
         return (this.data.children || []).map(child => ({...this.xema.elements[child.name], id: child.name}))
      },
      attributes() {
         return Object.entries(this.data.attributes || {})
            .map(([id, attribute]) => ({...attribute, id}))
            .sort((a, b) => a.id.localeCompare(b.id))
      },
      hasChildren() {
         return this.children.length > 0 || this.attributes.length > 0
      }
   }
}
</script>

<style>
dict-config-element-in-tree {
    position: relative;
    display: block;
    width: auto!important;
}
/* hide part of the lines in the tree (i.e. borders of the parent) */
dict-config-element-in-tree:last-child:before {
    content: "";
    display: block;
    position: absolute;
    left: -16px;
    bottom: 0;
    width: 2px;
    top: 16px;
    background: white;
}
</style>
