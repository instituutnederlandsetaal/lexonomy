<template>
   <div class="block">
      <div class="title">Values</div>
      <table>
         <tbody>
            <tr v-for="(value, index) in values" :key="index">
               <td class="cell1">
                  <input class="textbox val" placeholder="value" aria-label="Value" :value="value.value"
                     @input="update(index, 'value', $event)">
                  <input class="textbox cap" placeholder="caption" aria-label="Caption" :value="value.caption"
                     @input="update(index, 'caption', $event)">
               </td>
               <td class="cell9">
                  <button type="button" class="iconOnly iconCross" aria-label="Delete value"
                     @click="emit('update', values.filter((_, row) => row !== index))">&nbsp;</button>
               </td>
            </tr>
         </tbody>
      </table>

      <button v-if="!adding" type="button" class="butNewValue iconAdd" @click="begin">Add...</button>
      <form v-else @submit.prevent="add">
         <input ref="valueInput" v-model="newValue" class="textbox new val" placeholder="value" aria-label="New value" required>
         <input v-model="newCaption" class="textbox new cap" placeholder="caption" aria-label="New caption">
         <button type="submit" class="butNewValueOK iconAccept" :disabled="!newValue">Add</button>
         <button type="button" class="butNewValueCancel iconCancel" @click="adding = false">Cancel</button>
         <div v-if="duplicate" class="warn" role="alert">This value already exists.</div>
      </form>
   </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { type XemaValue } from '../../js/xema.ts'

const props = defineProps<{ values?: XemaValue[] | null }>()
const emit = defineEmits<{ update: [values: XemaValue[]] }>()

const values = computed(() => props.values ?? [])
const adding = ref(false)
const newValue = ref('')
const newCaption = ref('')
const valueInput = ref<HTMLInputElement>()
const duplicate = computed(() => Boolean(newValue.value) && values.value.some(value => value.value === newValue.value))

async function begin() {
   newValue.value = newCaption.value = ''
   adding.value = true
   await nextTick()
   valueInput.value?.focus()
}

function update(index: number, key: keyof XemaValue, event: Event) {
   if (event.target instanceof HTMLInputElement) {
      const value = event.target.value
      emit('update', values.value.map((item, row) => row === index ? { ...item, [key]: value } : item))
   }
}

function add() {
   if (!newValue.value || duplicate.value) return
   emit('update', [...values.value, { value: newValue.value, caption: newCaption.value }])
   newValue.value = newCaption.value = ''
   valueInput.value?.focus()
}
</script>
