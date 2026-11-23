<template>
<div class="tree-node">
    <button type="button" class="clickable" :class="{ current: selected }" @click="emit('select')">
        <span class="tech"><span class="ats">@</span><span class="att">{{ id }}</span></span>
    </button>
</div>
</template>

<script setup lang="ts">
defineProps<{ id: string; selected: boolean }>()
const emit = defineEmits<{ select: [] }>()
</script>
