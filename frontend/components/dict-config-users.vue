<template>
<div class="dict-config-users">
   <LoadingOverlay v-if="loading || saving"/>
   <DictNav :links="[['config', 'Configure'], ['config-users', 'Users']]"/>
   <h1>Users</h1>
   <form v-if="ready" ref="form" @submit.prevent="saveData">
      <DictConfigButtons :dict-id="dictId" :save-data="saveData" :disabled="saving"/>
      <h2 v-if="!users.length" class="grey-text center-align">No users</h2>
      <table v-else>
         <thead>
            <tr>
               <th scope="col">User email</th>
               <th v-for="permission in permissions" :key="permission.key" scope="col">{{ permission.label }}</th>
               <th scope="col">Actions</th>
            </tr>
         </thead>
         <tbody>
            <tr v-for="(user, index) in users" :key="user.id">
               <td>
                  <input v-if="user.isEditable" v-model.trim="user.email" :aria-label="`Email for row ${index + 1}`"
                     type="email" class="validate" required style="max-width: 300px;">
                  <span v-else>{{ user.email }}</span>
               </td>
               <td v-for="permission in permissions" :key="permission.key">
                  <label>
                     <input v-model="user.access[permission.key]" type="checkbox"
                        :aria-label="`${permission.label} permission for ${user.email || 'new user'}`">
                     <span></span>
                  </label>
               </td>
               <td>
                  <button type="button" class="btn btn-floating delete-user" :aria-label="`Remove ${user.email || 'new user'}`"
                     @click="users.splice(index, 1)">
                     <i class="material-symbols-outlined">delete</i>
                  </button>
               </td>
            </tr>
         </tbody>
      </table>
      <br>
      <button type="button" class="btn" :disabled="saving" @click="addUser">
         <i class="material-symbols-outlined right">add</i>
         Add new user
      </button>
      <p v-if="validationError" id="userConfigError" role="alert">{{ validationError }}</p>
   </form>
   <p v-else-if="!loading">Settings could not be loaded. <button class="btn-flat" type="button" @click="load">Retry</button></p>
</div>
</template>

<script setup lang="ts">
import { nextTick, ref } from 'vue'
import type { DictionarySettings } from '../js/dictionary-config-api.ts'
import { useDictionarySetting } from '../js/use-dictionary-setting.ts'
import DictConfigButtons from './dict-config-buttons.vue'
import DictNav from './dict-nav.vue'
import LoadingOverlay from './loading-overlay.vue'

const props = defineProps<{ dictId: string }>()
const permissions = [
   { key: 'canEdit', label: 'Edit' },
   { key: 'canConfig', label: 'Configure' },
   { key: 'canDownload', label: 'Download' },
   { key: 'canUpload', label: 'Upload' }
] as const
type Access = DictionarySettings['users'][string]
type User = { id: number; email: string; access: Access; isEditable?: boolean }
const form = ref<HTMLFormElement>()
const users = ref<User[]>([])
const validationError = ref('')
let nextId = 0
const { loading, ready, saving, load, save } = useDictionarySetting(() => props.dictId, 'users', content => {
   validationError.value = ''
   users.value = Object.entries(content).map(([email, access]) => ({ id: nextId++, email, access }))
})

async function addUser() {
   users.value.push({ id: nextId++, email: '', isEditable: true,
      access: { canEdit: false, canConfig: false, canDownload: false, canUpload: false } })
   await nextTick()
   Array.from(form.value?.querySelectorAll<HTMLInputElement>('input[type="email"]') ?? []).at(-1)?.focus()
}

async function saveData() {
   validationError.value = ''
   if (!form.value?.reportValidity()) return
   const emails = users.value.map(user => user.email.toLowerCase())
   if (new Set(emails).size !== users.value.length) {
      validationError.value = 'Each email address should appear only once.'
      return
   }
   if (!users.value.some(user => user.access.canConfig)) {
      validationError.value = 'At least one user must have Configure permission.'
      return
   }
   await save(Object.fromEntries(users.value.map((user, index) => [emails[index], user.access])))
}
</script>

<style>
.dict-config-users .delete-user {
   float: right;
}
.dict-config-users #userConfigError {
   color: red;
}
</style>
