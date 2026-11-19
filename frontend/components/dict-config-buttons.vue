<template>
<div class="dict-config-buttons buttons">
   <RouterLink :to="{ name: 'config', params: { dictId } }"
         class="btn btn-secondary" :class="{ 'btn-flat': showSave !== false }">
      Back
   </RouterLink>
   <button v-if="showSave !== false"
         class="btn waves-effect waves-light"
         @click="saveData"
         :disabled="disabled"
         type="button">
      {{ label }}
      <i class="material-symbols-outlined right">edit</i>
   </button>

   <slot/>

</div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
   dictId: string
   showSave?: boolean
   saveData?: () => void | Promise<unknown>
   label?: string
   disabled?: boolean
}>(), { showSave: true, label: 'Save' })

</script>

<style>
.dict-config-buttons{
   margin-top: 20px;
}
</style>
