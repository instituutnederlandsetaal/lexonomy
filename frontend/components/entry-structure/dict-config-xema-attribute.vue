<template>
<div class="dict-config-xema-attribute">
    <div class="block">
        <div class="title">Attribute</div>
        <form @submit.prevent="emit('rename', newName)">
            <input v-model="newName" class="textbox tech atName" aria-label="Attribute name">
            <button v-if="canRename" class="butRename iconAccept" type="submit">Rename</button>
            <div v-if="newName !== attributeId && !isValidXmlName(newName)" class="warn">Cannot rename, not a valid XML name.</div>
            <div v-else-if="newName !== attributeId && Object.hasOwn(attributes, newName)" class="warn">Cannot rename, this attribute already exists.</div>
        </form>
    </div>
    <div class="block">
        <div class="title">Content</div>
        <label class="radio"><input type="radio" name="attribute-filling" value="txt" @change="setFilling('txt')" :checked="config.filling !== 'lst'">Text</label>
        <label class="radio"><input type="radio" name="attribute-filling" value="lst" @change="setFilling('lst')" :checked="config.filling === 'lst'">Value from list</label>
    </div>
    <XemaValues v-if="config.filling === 'lst'" :values="config.values" @update="values => emit('update', { ...config, values })"/>
</div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { isValidXmlName } from '../../js/xml.ts'
import { type XemaAttribute } from '../../js/xema.ts'
import XemaValues from './xema-values.vue'

const props = defineProps<{ attributeId: string; attributes: Record<string, XemaAttribute>; config: XemaAttribute }>()
const emit = defineEmits<{ update: [config: XemaAttribute]; rename: [name: string] }>()
const newName = ref(props.attributeId)
const canRename = computed(() => newName.value !== props.attributeId && isValidXmlName(newName.value) &&
   !Object.hasOwn(props.attributes, newName.value))

function setFilling(filling: XemaAttribute['filling']) {
   emit('update', { ...props.config, filling })
}
</script>
