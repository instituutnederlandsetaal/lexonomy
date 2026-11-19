<template>
   <div class="dict-entry-filter filterForm">
      <div class="search-control">
         <input id="searchBox" type="search" placeholder="search" aria-label="Search entries"
                v-model="searchText" @keydown.enter="submitSearch"/>
         <button v-if="searchText" type="button" aria-label="Clear search" @click="clearSearch"
                 class="material-symbols-outlined clearFilterIcon grey-text">close</button>
      </div>

      <DropdownMenuRoot :modal="false">
         <DropdownMenuTrigger class="dropdown-btn" :class="{ active: criteria.modifier !== 'start' }"
                              aria-label="Search type">
            <i class="material-symbols-outlined" aria-hidden="true">filter_list</i>
            <span v-if="criteria.modifier !== 'start'" class="active-badge" aria-hidden="true">•</span>
         </DropdownMenuTrigger>
         <DropdownMenuPortal>
            <DropdownMenuContent class="entry-filter-options" align="end" :side-offset="4" :collision-padding="8">
               <DropdownMenuRadioGroup :model-value="criteria.modifier"
                                       @update:model-value="value => search({ modifier: String(value) })">
                  <DropdownMenuRadioItem v-for="option in searchTypeOptions" :key="option.value" :value="option.value">
                     {{ option.label }}
                  </DropdownMenuRadioItem>
               </DropdownMenuRadioGroup>
            </DropdownMenuContent>
         </DropdownMenuPortal>
      </DropdownMenuRoot>

      <DropdownMenuRoot v-if="flags.length" :modal="false">
         <DropdownMenuTrigger class="dropdown-btn" :class="{ active: criteria.searchflag }" aria-label="Filter by flag">
            <i class="material-symbols-outlined" aria-hidden="true">label</i>
            <span v-if="criteria.searchflag" class="active-badge" aria-hidden="true">•</span>
         </DropdownMenuTrigger>
         <DropdownMenuPortal>
            <DropdownMenuContent class="entry-filter-options" align="end" :side-offset="4" :collision-padding="8">
               <DropdownMenuRadioGroup :model-value="criteria.searchflag"
                                       @update:model-value="value => search({ searchflag: String(value) })">
                  <DropdownMenuRadioItem value="">
                     <i class="material-symbols-outlined grey-text" aria-hidden="true">label_outline</i>
                     <span>Any flag</span>
                  </DropdownMenuRadioItem>
                  <DropdownMenuRadioItem v-for="flag in flags" :key="flag.name" :value="flag.name">
                     <span class="flag-dot" :style="{ background: flag.color }"></span>
                     <span>{{ flag.label }}</span>
                  </DropdownMenuRadioItem>
               </DropdownMenuRadioGroup>
            </DropdownMenuContent>
         </DropdownMenuPortal>
      </DropdownMenuRoot>
   </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
   DropdownMenuContent, DropdownMenuPortal, DropdownMenuRadioGroup, DropdownMenuRadioItem,
   DropdownMenuRoot, DropdownMenuTrigger
} from 'reka-ui'
import type { EntrySearch } from '../js/dictionary-workspace.ts'
import type { Flag } from '../js/dictionary-config-api.ts'
import { searchEntriesFromRoute } from '../js/entry-search.ts'
import { readEntrySearch } from '../js/router.ts'

defineProps<{ flags: readonly Flag[] }>()
const route = useRoute()
const criteria = computed(() => readEntrySearch(route.query))
const searchText = ref(criteria.value.searchtext)
const searchTypeOptions = [
   { value: 'start', label: 'starts like this' },
   { value: 'exact', label: 'is exactly' },
   { value: 'wordstart', label: 'contains a word that starts like this' },
   { value: 'substring', label: 'contains this sequence of characters' }
]

watch([() => route.params.dictId, () => criteria.value.searchtext], ([, value]) => {
   searchText.value = value
})

function search(changes: Partial<EntrySearch> = {}) {
   void searchEntriesFromRoute({ searchtext: searchText.value, ...changes })
}

function submitSearch(event: KeyboardEvent) {
   if (!event.isComposing) search()
}

function clearSearch() {
   searchText.value = ''
   search()
}
</script>

<style>
.dict-entry-filter{
   display: flex;
   position: relative;
   border: 1px solid #9e9e9e;
   height: 42px;
}
.dict-entry-filter .search-control {
   flex: 1;
   position: relative;
   min-width: 0;
}
.dict-entry-filter input {
   box-sizing: border-box;
   width: 100%;
   border: none !important;
   border-radius: 0 !important;
   margin: 0 !important;
   height: 100% !important;
   box-shadow: none !important;
   padding-left: 10px !important;
   padding-right: 35px !important;
}
.dict-entry-filter input:focus-visible {
   outline-offset: -2px;
}
.dict-entry-filter input::-webkit-search-cancel-button { display: none; }
.dict-entry-filter .clearFilterIcon{
   position: absolute;
   right: 8px;
   top: 9px;
   background: none;
   border: 0;
   padding: 0;
   cursor: pointer;
   font-size: 1.3rem;
   z-index: 1;
}
.dict-entry-filter .dropdown-btn{
   background: #f5f5f5;
   border: none;
   border-left: 1px solid #9e9e9e;
   width: 42px;
   flex-shrink: 0;
   height: 100%;
   cursor: pointer;
   display: flex;
   align-items: center;
   justify-content: center;
   transition: background-color 0.2s;
   padding: 0;
   margin: 0;
   position: relative;
}
.dict-entry-filter .dropdown-btn:hover{
   background: #e0e0e0;
}
.dict-entry-filter .dropdown-btn.active{
   background: #e3f2fd;
   border-left-color: #2196f3;
}
.dict-entry-filter .dropdown-btn.active i{
   color: #1976d2;
}
.dict-entry-filter .dropdown-btn i{
   font-size: 1.3rem;
   color: #666;
}
.dict-entry-filter .active-badge{
   position: absolute;
   top: 6px;
   right: 6px;
   width: 12px;
   height: 12px;
   background: #ff5722;
   border-radius: 50%;
   display: flex;
   align-items: center;
   justify-content: center;
   font-size: 14px;
   line-height: 1;
   color: white;
   font-weight: bold;
   pointer-events: none;
}
.entry-filter-options {
   background: white;
   border: 1px solid #e0e0e0;
   border-radius: 4px;
   box-shadow: 0 2px 8px #0002;
   padding: 4px 0;
   z-index: 1000;
   min-width: 200px;
   max-width: 300px;
}
.entry-filter-options [role="menuitemradio"] {
   padding: 8px 16px;
   cursor: pointer;
   display: flex;
   align-items: center;
   gap: 8px;
   outline: none;
}
.entry-filter-options [data-highlighted] { background: #f5f5f5; }
.entry-filter-options [data-state="checked"] {
   background: #e3f2fd;
   font-weight: 500;
}
.entry-filter-options .flag-dot {
   width: 1em;
   height: 1em;
   border-radius: 100%;
   flex-shrink: 0;
}
</style>
