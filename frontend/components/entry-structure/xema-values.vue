<template>
   <div class="block">
      <div class="title">Values</div>
      <ul v-if="values.length" class="value-list">
         <li v-for="(value, index) in values" :key="index" class="value-row">
            <input class="textbox val" placeholder="value" aria-label="Value" :value="value.value"
               @input="update(index, 'value', $event)">
            <input class="textbox" placeholder="caption" aria-label="Caption" :value="value.caption"
               @input="update(index, 'caption', $event)">
            <button type="button" class="iconOnly iconCross" aria-label="Delete value"
               @click="emit('update', values.filter((_, row) => row !== index))">&nbsp;</button>
         </li>
      </ul>

      <button v-if="!adding" type="button" class="butNewValue iconAdd" @click="begin">Add...</button>
      <form v-else class="value-row" @submit.prevent="add">
         <input ref="valueInput" v-model="newValue" class="textbox val" placeholder="value" aria-label="New value" required>
         <input v-model="newCaption" class="textbox" placeholder="caption" aria-label="New caption">
         <div class="value-actions">
            <button type="submit" class="iconAccept" :disabled="!newValue">Add</button>
            <button type="button" class="iconCancel" @click="adding = false">Cancel</button>
         </div>
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

<style scoped>
.value-list {
   margin: 0 0 .5rem;
}
.value-row {
   display: grid;
   grid-template-columns: minmax(0, 2fr) minmax(0, 3fr) 2rem;
   align-items: center;
   gap: .5rem;
}
.value-list > li {
   padding: .35rem 0;
   border-bottom: 1px solid #ddd;
}
#editor.designer .value-row .textbox {
   width: 100%;
   height: 2.25rem;
   margin: 0;
}
#editor.designer .value-row .val {
   font-family: monospace;
   color: #0268cb;
}
#editor.designer .value-row .iconOnly {
   margin: 0;
}
.value-actions, .warn {
   grid-column: 1 / -1;
}
</style>
