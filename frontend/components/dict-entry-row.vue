<template>
   <li class="dict-entry-row collection-item" :data-idx="index"
       :class="{ selected, saving: entry.isSaving }" @click="activate">
      <span class="lineNum">{{ index + 1 }}.</span>
      <a :href="entry.isSaving ? undefined : href" :aria-disabled="entry.isSaving || undefined"
         :tabindex="entry.isSaving ? -1 : undefined" :aria-current="selected ? 'true' : undefined"
         class="headword-link" :class="{ 'red-text': selected }">
         <RawHtml :content="entry.title || '&amp;nbsp;'"/>
      </a>
      <DropdownMenuRoot v-if="flags.length" v-slot="{ open }" :modal="false">
         <DropdownMenuTrigger as-child :disabled="!canChangeFlag">
            <button type="button" class="flag" :class="entry.flag ? 'badge' : 'noFlag'"
                    :style="flagStyle"
                    :aria-label="'Flag for entry ' + entry.id" :aria-controls="open ? menuId : undefined" @click.stop>
               {{ currentFlag?.label || entry.flag || 'No flag' }}
            </button>
         </DropdownMenuTrigger>
         <DropdownMenuPortal v-if="open">
            <DropdownMenuContent :id="menuId" class="entry-flag-menu" align="end" :side-offset="4" :collision-padding="8">
               <DropdownMenuItem @select="emit('update:flag', '')">
                  <i class="material-symbols-outlined grey-text" aria-hidden="true">label_outline</i>
                  <span>No flag</span>
                  <kbd>Delete</kbd>
               </DropdownMenuItem>
               <DropdownMenuItem v-for="flag in flags" :key="flag.name" @select="emit('update:flag', flag.name)">
                  <i class="material-symbols-outlined" :style="{ color: flag.color }" aria-hidden="true">label</i>
                  <span>{{ flag.label }}</span>
                  <kbd v-if="flag.key">{{ flag.key }}</kbd>
               </DropdownMenuItem>
            </DropdownMenuContent>
         </DropdownMenuPortal>
      </DropdownMenuRoot>
   </li>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { START_LOCATION, useRouter, type RouteLocationRaw } from 'vue-router'
import {
   DropdownMenuContent, DropdownMenuItem, DropdownMenuPortal, DropdownMenuRoot, DropdownMenuTrigger
} from 'reka-ui'
import type { Flag } from '../js/dictionary-config-api.ts'
import type { EntrySummary } from '../js/dictionary-workspace.ts'
import { flagTextColor } from './entry-flags.js'
import RawHtml from './raw-html.vue'

const props = defineProps<{
   entry: EntrySummary
   index: number
   locateEntry: (entryId: number) => RouteLocationRaw
   selected: boolean
   canChangeFlag: boolean
   flags: readonly Flag[]
}>()
const emit = defineEmits<{
   select: [entryId: number]
   'update:flag': [flag: string]
}>()

const router = useRouter()
// Resolve the complete route without depending on the currently selected entry.
const href = computed(() => router.resolve(props.locateEntry(props.entry.id), START_LOCATION).href)
const menuId = computed(() => 'entry-flag-menu-' + props.entry.id)
const currentFlag = computed(() => props.flags.reduce<Flag | undefined>(
   (match, flag) => flag.name === props.entry.flag ? flag : match, undefined))
const flagStyle = computed(() => {
   const backgroundColor = currentFlag.value?.color ?? 'initial'
   return { color: flagTextColor(backgroundColor), backgroundColor }
})

function activate(event: MouseEvent) {
   if (event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return
   event.preventDefault()
   if (props.entry.isSaving) return
   const row = event.currentTarget as HTMLLIElement
   row.querySelector<HTMLAnchorElement>('.headword-link')?.focus({ preventScroll: true })
   emit('select', props.entry.id)
}
</script>

<style>
.dict-entry-row.collection-item{
   position: relative;
   display: flex;
   border-left: 5px solid white;
   padding-left: 0.2rem;
}
.dict-entry-row.collection-item.selected{
   border-left-color: #000;
}
.dict-entry-row.collection-item .headword-link{
   text-decoration: none;
   font-size: 1.2rem;
   letter-spacing: 1px;
   margin-right: auto;
}
.dict-entry-row.collection-item .flag {
   border: 0;
   background: transparent;
   cursor: pointer;
}
.dict-entry-row.collection-item .flag:disabled { cursor: default; opacity: 0.7; }
.entry-flag-menu {
   background: #fff;
   color: #333;
   box-shadow: 0 2px 8px #0002;
   min-width: 150px;
   max-height: var(--reka-dropdown-menu-content-available-height);
   overflow: auto;
   z-index: 1000;
}
.entry-flag-menu [role="menuitem"] {
   cursor: pointer;
   display: flex;
   align-items: center;
   gap: 8px;
   padding: 8px 12px;
   outline: none;
}
.entry-flag-menu [data-highlighted] { background: #eee; }
.entry-flag-menu kbd { margin-left: auto; }
.dict-entry-row.collection-item .badge{
   font-weight: bold;
   font-size: 1rem;
   color: #fff;
   white-space: nowrap;
   min-width: auto;
   border-radius: 2px;
   box-shadow: 0 2px 2px 0 rgb(0 0 0 / 14%),
      0 3px 1px -2px rgb(0 0 0 / 12%),
      0 1px 5px 0 rgb(0 0 0 / 20%);
}
.dict-entry-row.collection-item .noFlag{
   font-size: 1rem;
   color: grey;
}
.dict-entry-row.collection-item.saving::before{
   content: '';
   position: absolute;
   left: 0;
   right: 0;
   top: 0;
   bottom: 0;
   background-color: #ffffffe8;
   line-height: 100%;
   z-index: 500;
}
.dict-entry-row.collection-item.saving::after{
   content: 'saving...';
   position: absolute;
   transform: translateX(-50%) translateY(-50%);
   left: 50%;
   top: 50%;
   color: #6e6e6e;
   z-index: 501;
   font-size: 1.3rem;
   text-transform: uppercase;
}
.dict-entry-row.collection-item:focus-within{
   background-color: #eceff1;
}
.dict-entry-row .lineNum{
   font-size: 0.8rem;
   color: #b8b8b8;
   margin-right: 10px;
   min-width: 30px;
   text-align: right;
}
</style>
