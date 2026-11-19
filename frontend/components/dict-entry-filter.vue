<template>
<dict-entry-filter>
   <div class="filterForm">
      <input type="text"
            id="searchBox"
            placeholder="search"
            class="input-field"
            v-model="searchText"
            @keyup.enter="search()"/>
      <button type="button" aria-label="Clear search" @click="onClearFilterClick"
         class="material-symbols-outlined clearFilterIcon grey-text">close</button>

      <button type="button" class="dropdown-btn" :class="{ active: activeDictionary.modifier !== 'start' }"
            aria-label="Search type" :aria-expanded="showSearchType" @click.stop="toggleSearchTypeDropdown">
         <i class="material-symbols-outlined" aria-hidden="true">filter_list</i>
         <span v-if="activeDictionary.modifier !== 'start'" class="active-badge" aria-hidden="true">•</span>
      </button>
      <ul class="custom-dropdown" v-show="showSearchType">
         <li v-for="option in searchTypeOptions" :key="option.value">
            <button type="button" :aria-pressed="activeDictionary.modifier === option.value"
                  @click.stop="selectSearchType(option.value)">{{ option.label }}</button>
         </li>
      </ul>

      <button v-if="activeDictionary.config?.flagging.flags.length"
              type="button" class="dropdown-btn" :class="{ active: activeDictionary.searchflag }"
              aria-label="Filter by flag" :aria-expanded="showFlag" @click.stop="toggleFlagDropdown">
         <i class="material-symbols-outlined" aria-hidden="true">label</i>
         <span v-if="activeDictionary.searchflag" class="active-badge" aria-hidden="true">•</span>
      </button>
      <ul v-if="activeDictionary.config?.flagging.flags.length"
          class="custom-dropdown" v-show="showFlag">
         <li>
            <button type="button" :aria-pressed="!activeDictionary.searchflag" @click.stop="selectFlag('')">
               <i class="material-symbols-outlined grey-text" aria-hidden="true">label_outline</i>
               <span>Any flag</span>
            </button>
         </li>
         <li v-for="flag in activeDictionary.config.flagging.flags" :key="flag.name">
            <button type="button" :aria-pressed="activeDictionary.searchflag === flag.name" @click.stop="selectFlag(flag.name)">
               <span class="flag-dot" :style="{ background: flag.color }"></span>
               <span>{{ flag.label }}</span>
            </button>
         </li>
      </ul>
   </div>
</dict-entry-filter>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { activeDictionary, type EntrySearch } from '../js/dictionary-workspace.ts'

const emit = defineEmits<{ search: [criteria: Partial<EntrySearch>] }>()
const searchText = ref(activeDictionary.searchtext)
const showSearchType = ref(false)
const showFlag = ref(false)
const searchTypeOptions = [
   { value: 'start', label: 'starts like this' },
   { value: 'exact', label: 'is exactly' },
   { value: 'wordstart', label: 'contains a word that starts like this' },
   { value: 'substring', label: 'contains this sequence of characters' }
]

watch(() => activeDictionary.searchtext, value => { searchText.value = value })
onMounted(() => document.addEventListener('click', closeDropdowns))
onUnmounted(() => document.removeEventListener('click', closeDropdowns))

function search(changes: Partial<EntrySearch> = {}) {
   emit('search', { searchtext: searchText.value, ...changes })
}

function onClearFilterClick() {
   if (!searchText.value) return
   searchText.value = ''
   search()
}

function toggleSearchTypeDropdown() {
   showSearchType.value = !showSearchType.value
   showFlag.value = false
}

function toggleFlagDropdown() {
   showFlag.value = !showFlag.value
   showSearchType.value = false
}

function selectSearchType(modifier: string) {
   closeDropdowns()
   search({ modifier })
}

function selectFlag(searchflag: string) {
   closeDropdowns()
   search({ searchflag })
}

function closeDropdowns() {
   showSearchType.value = false
   showFlag.value = false
}
</script>

<style>
dict-entry-filter{
   display: block;
   position: relative;
}
dict-entry-filter .filterForm{
   display: flex;
   position: relative;
   border: 1px solid #9e9e9e;
   height: 42px;
}
dict-entry-filter .filterForm input{
   flex: 1;
   border: none !important;
   border-radius: 0 !important;
   margin: 0 !important;
   height: 100% !important;
   box-shadow: none !important;
   padding-left: 10px !important;
   padding-right: 35px !important;
}
dict-entry-filter .filterForm input:focus{
   border: none !important;
   box-shadow: none !important;
}
dict-entry-filter .clearFilterIcon{
   position: absolute;
   right: 95px;
   top: 9px;
   background: none;
   border: 0;
   padding: 0;
   cursor: pointer;
   font-size: 1.3rem;
   z-index: 1;
}
dict-entry-filter .dropdown-btn{
   background: #f5f5f5;
   border: none;
   border-left: 1px solid #9e9e9e;
   width: 42px;
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
dict-entry-filter .dropdown-btn:hover{
   background: #e0e0e0;
}
dict-entry-filter .dropdown-btn.active{
   background: #e3f2fd;
   border-left-color: #2196f3;
}
dict-entry-filter .dropdown-btn.active i{
   color: #1976d2;
}
dict-entry-filter .dropdown-btn i{
   font-size: 1.3rem;
   color: #666;
}
dict-entry-filter .active-badge{
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
dict-entry-filter .custom-dropdown{
   position: absolute;
   top: 100%;
   right: 0;
   background: white;
   border: 1px solid #e0e0e0;
   border-radius: 4px;
   box-shadow: 0 2px 8px rgba(0,0,0,0.15);
   list-style: none;
   margin: 4px 0 0 0;
   padding: 4px 0;
   z-index: 1000;
   min-width: 200px;
   max-width: 300px;
}
dict-entry-filter .custom-dropdown button{
   background: none;
   color: inherit;
   border: 0;
   width: 100%;
   padding: 8px 16px;
   cursor: pointer;
   transition: background-color 0.2s;
   display: flex;
   align-items: center;
   gap: 8px;
   white-space: nowrap;
}
dict-entry-filter .custom-dropdown button:hover{
   background: #f5f5f5;
}
dict-entry-filter .custom-dropdown button[aria-pressed="true"]{
   background: #e3f2fd;
   font-weight: 500;
}
dict-entry-filter .custom-dropdown button i{
   font-size: 1.2rem;
}
dict-entry-filter .flag-dot {
   width: 1em;
   height: 1em;
   display: inline-block;
   border-radius: 100%;
   flex-shrink: 0;
}
</style>
