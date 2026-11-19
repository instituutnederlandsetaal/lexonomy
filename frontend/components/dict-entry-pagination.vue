<template>
<div class="dict-entry-pagination">
   <div class="paginationWrapper" v-if="totalPages > 1">
      <button type="button" class="btn-small btn-flat" aria-label="Previous page"
            @click="emit('previous')"
            :disabled="loading || page <= 1">
         <i class="material-symbols-outlined" aria-hidden="true">chevron_left</i>
      </button>
      <span class="paginationInfo">{{ pageRange }}</span>
      <button type="button" class="btn-small btn-flat" aria-label="Next page"
            @click="emit('next')"
            :disabled="loading || page >= totalPages">
         <i class="material-symbols-outlined" aria-hidden="true">chevron_right</i>
      </button>
   </div>
   <div class="entriesCountInfo" v-else>
      {{ entryCount + ' entries' }}
   </div>
</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ entryCount: number; pageSize: number; page: number; loading: boolean }>()
const emit = defineEmits<{ previous: []; next: [] }>()
const totalPages = computed(() => Math.ceil(props.entryCount / props.pageSize))
const pageRange = computed(() => {
   const { page, pageSize, entryCount } = props
   const end = Math.min(page * pageSize, entryCount)
   const start = (page - 1) * pageSize + 1
   return `${start}-${end} of ${entryCount}`
})
</script>

<style>
.dict-entry-pagination{
   display: block;
}
.dict-entry-pagination .paginationWrapper{
   display: flex;
   align-items: center;
   justify-content: center;
   gap: 8px;
}
.dict-entry-pagination .paginationWrapper .btn-small {
   padding: 0 8px;
   min-width: auto;
   height: 24px;
   line-height: 24px;
}
.dict-entry-pagination .paginationWrapper .btn-small i{
   font-size: 1.2rem;
}
.dict-entry-pagination .paginationWrapper .btn-small:disabled{
   color: #ccc;
   cursor: not-allowed;
}
.dict-entry-pagination .paginationInfo{
   font-size: 0.85rem;
   color: #666;
   white-space: nowrap;
}
.dict-entry-pagination .entriesCountInfo{
   font-size: 0.85rem;
   color: #b8b8b8;
   text-align: center;
}
</style>
