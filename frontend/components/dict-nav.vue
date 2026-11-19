<template>
   <nav class="nav-breadcrumbs" aria-label="Breadcrumb">
      <div class="nav-wrapper">
         <RouterLink :to="{ name: session ? 'home' : 'public-list' }"
               class="breadcrumb">Dictionaries</RouterLink>
         <template v-if="$route.params.dictId">
            <RouterLink :to="{ name: 'dictionary', params: { dictId: $route.params.dictId } }"
                  class="breadcrumb">{{ activeDictionary.title }}</RouterLink>
            <RouterLink v-for="[name, label, params] in links" :key="name"
                  :to="{ name, params: { dictId: $route.params.dictId, ...params } }"
                  class="breadcrumb">{{ label }}</RouterLink>
         </template>
      </div>
   </nav>
</template>

<script setup lang="ts">
import type { RouteParamsRaw } from 'vue-router'
import { activeDictionary } from '../js/dictionary-workspace.ts'
import { session } from '../js/auth.ts'

defineProps<{ links?: [name: string, label: string, params?: RouteParamsRaw][] }>()
</script>
