<template>
<div class="dict-config-attribute-in-tree container">
    <div class="horizontal"></div>
    <button type="button" class="clickable attribute" :class="{ current: selected }" @click="emit('select')">
        <span class="tech"><span class="ats">@</span><span class="att">{{ id }}</span></span>
    </button>
</div>
</template>

<script setup lang="ts">
defineProps<{ id: string; selected: boolean }>()
const emit = defineEmits<{ select: [] }>()
</script>

<style>
.dict-config-attribute-in-tree {
    position: relative;
    display: inline-block;
}
.dict-config-attribute-in-tree .attribute {
    display: inline-block;
}
</style>
