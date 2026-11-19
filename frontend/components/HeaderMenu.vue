<script lang="ts">
import type { RouteLocationRaw } from 'vue-router'

export type NavigationItem = { label: string } & ({ to: RouteLocationRaw } | { action: () => void })
</script>

<script setup lang="ts">
import {
   DropdownMenuContent, DropdownMenuItem, DropdownMenuPortal, DropdownMenuRoot,
   DropdownMenuSeparator, DropdownMenuTrigger
} from 'reka-ui'

defineProps<{ groups: NavigationItem[][]; label?: string }>()
</script>

<template>
   <DropdownMenuRoot :modal="false">
      <DropdownMenuTrigger type="button" class="header-menu-trigger" :aria-label="label">
         <slot/>
      </DropdownMenuTrigger>
      <DropdownMenuPortal>
         <DropdownMenuContent align="end" :side-offset="2" class="header-menu-content">
            <template v-for="(group, index) in groups" :key="index">
               <DropdownMenuSeparator v-if="index" class="header-menu-divider"/>
               <template v-for="item in group" :key="item.label">
                  <DropdownMenuItem v-if="'to' in item" as-child class="header-menu-item">
                     <RouterLink :to="item.to">{{ item.label }}</RouterLink>
                  </DropdownMenuItem>
                  <DropdownMenuItem v-else class="header-menu-item" @select="item.action">
                     {{ item.label }}
                  </DropdownMenuItem>
               </template>
            </template>
         </DropdownMenuContent>
      </DropdownMenuPortal>
   </DropdownMenuRoot>
</template>

<style>
.header-menu-trigger {
   display: flex;
   align-items: center;
   gap: 0.25em;
   height: 80px;
   max-width: 35vw;
   padding: 0 15px;
   border: 0;
   background: transparent;
   color: inherit;
   cursor: pointer;
}
.header-menu-trigger:focus-visible {
   outline: 2px solid currentColor;
   outline-offset: -4px;
}
.header-menu-trigger:hover,
.header-menu-trigger[data-state="open"] {
   background: rgb(0 0 0 / 10%);
}
.header-menu-trigger .menu-label {
   overflow: hidden;
   text-overflow: ellipsis;
   white-space: nowrap;
}
.header-menu-trigger .material-symbols-outlined {
   height: auto;
   line-height: 1;
}
.header-menu-content {
   min-width: 140px;
   max-height: var(--reka-dropdown-menu-content-available-height);
   overflow-y: auto;
   z-index: 1500;
   padding: 4px 0;
   background: white;
   box-shadow: 0 2px 5px #0004;
}
.header-menu-item {
   display: block;
   padding: 12px 16px;
   color: #18756f;
   cursor: pointer;
   outline: none;
}
.header-menu-item[data-highlighted] {
   background: #eee;
}
.header-menu-divider {
   height: 1px;
   margin: 4px 0;
   background: #e0e0e0;
}
</style>
