<template>
   <span class="raw-html" v-html="sanitized"/>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { sanitizeHtml } from '../js/sanitize-html.ts'

const props = defineProps<{ content?: string | null }>()
const sanitized = computed(() => sanitizeHtml(props.content ?? ''))
</script>
