<template>
<dict-entry-pagination>
   <div class="paginationWrapper" v-if="totalPages > 1">
      <button class="btn-small btn-flat" 
            @click="dictionaryWorkspace.previousPage()"
            :disabled="activeDictionary.isEntryListLoading || activeDictionary.currentPage <= 1">
         <i class="material-symbols-outlined">chevron_left</i>
      </button>
      <span class="paginationInfo">{{ pageRange }}</span>
      <button class="btn-small btn-flat" 
            @click="dictionaryWorkspace.nextPage()"
            :disabled="activeDictionary.isEntryListLoading || activeDictionary.currentPage >= totalPages">
         <i class="material-symbols-outlined">chevron_right</i>
      </button>
   </div>
   <div class="entriesCountInfo" v-else>
      {{ activeDictionary.entryCount + ' entries' }}
   </div>
</dict-entry-pagination>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { activeDictionary, dictionaryWorkspace, entryPageSize } from '../js/dictionary-workspace.ts'

const totalPages = computed(() => Math.ceil(activeDictionary.entryCount / entryPageSize.value))
const pageRange = computed(() => {
   const end = Math.min(activeDictionary.currentPage * entryPageSize.value, activeDictionary.entryCount)
   const start = (activeDictionary.currentPage - 1) * entryPageSize.value + 1
   return `${start}-${end} of ${activeDictionary.entryCount}`
})
</script>

<style>
dict-entry-pagination{
   display: block;
}
dict-entry-pagination .paginationWrapper{
   display: flex;
   align-items: center;
   justify-content: center;
   gap: 8px;
}
dict-entry-pagination .paginationWrapper .btn-small {
   padding: 0 8px;
   min-width: auto;
   height: 24px;
   line-height: 24px;
}
dict-entry-pagination .paginationWrapper .btn-small i{
   font-size: 1.2rem;
}
dict-entry-pagination .paginationWrapper .btn-small:disabled{
   color: #ccc;
   cursor: not-allowed;
}
dict-entry-pagination .paginationInfo{
   font-size: 0.85rem;
   color: #666;
   white-space: nowrap;
}
dict-entry-pagination .entriesCountInfo{
   font-size: 0.85rem;
   color: #b8b8b8;
   text-align: center;
}
</style>
