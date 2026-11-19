<template>
<dict-config-buttons class="buttons">
   <RouterLink :to="{ name: 'config', params: { dictId: activeDictionary.dictId } }"
         class="btn btn-secondary" :class="{ 'btn-flat': showSave }">
      Back
   </RouterLink>
   <button v-if="showSave !== false"
         class="btn waves-effect waves-light"
         @click="saveData"
         type="button"
         id="submit_button">
      {{ label }}
      <i class="material-symbols-outlined right">edit</i>
   </button>

   <slot/>

</dict-config-buttons>
</template>

<script>
import { activeDictionary } from '../js/dictionary-workspace.ts'
export default {
   setup: () => ({ activeDictionary }),
   props: {
      showSave: { type: Boolean, default: undefined },
      saveData: Function,
      label: { type: String, default: 'Save' }
   }
}
</script>

<style>
dict-config-buttons{
   margin-top: 20px;
}
</style>
