<template>
<dict-config-users>
   <LoadingOverlay v-if="state.isLoading || state.isSaving"/>
   <DictNav :links="[['config', 'Configure'], ['config-users', 'Users']]"/>
   <h1>Users</h1>
   <template v-if="!state.isLoading">
      <div v-if="!state.data.users.length"
            class="grey-text center-align">
         <h2>No users</h2>
         <br>
         <button class="btn btn-primary"
               @click="doAddUser">
            <i class="material-symbols-outlined right">add</i>
            Add new user
         </button>
         <br><br><br><br>
         <div class="buttons"
               style="justify-content: center;">
            <DictConfigButtons :save-data="saveData"></DictConfigButtons>
         </div>
      </div>
      <div>

      <div v-if="state.data.users.length">
         <DictConfigButtons :save-data="saveData"></DictConfigButtons>
         <table>
            <thead>
               <tr style="border-bottom: none;">
                  <th>
                  </th>
                  <th colspan="5">Privileges</th>
               </tr>
               <tr>
                  <th>User email</th>
                  <th>Edit</th>
                  <th>Configure</th>
                  <th>Download</th>
                  <th>Upload</th>
                  <th></th>
               </tr>
            </thead>
            <tbody>
               <tr v-for="(user, idx) in state.data.users"
                     :key="user.id">
                  <td>
                     <span v-if="user.isEditable">
                        <input id="new-email"
                              type="email"
                              class="validate"
                              @input="onEmailInput(idx, $event)"
                              style="max-width: 300px;">
                     </span>
                     <span v-if="!user.isEditable">
                        {{ user.email }}
                     </span>
                  </td>
                  <td>
                     <label>
                        <input type="checkbox"
                              name="canEdit"
                              :checked="user.canEdit"
                              @change="onPermissionChange(idx, $event)"/>
                        <span></span>
                     </label>
                  </td>
                  <td>
                     <label>
                        <input type="checkbox"
                              name="canConfig"
                              :checked="user.canConfig"
                              @change="onPermissionChange(idx, $event)"/>
                        <span></span>
                     </label>
                  </td>
                  <td>
                     <label>
                        <input type="checkbox"
                              name="canDownload"
                              :checked="user.canDownload"
                              @change="onPermissionChange(idx, $event)"/>
                        <span></span>
                     </label>
                  </td>
                  <td>
                     <label>
                        <input type="checkbox"
                              name="canUpload"
                              :checked="user.canUpload"
                              @change="onPermissionChange(idx, $event)"/>
                        <span></span>
                     </label>
                  </td>
                  <td>
                     <a class="btn btn-floating delete-user"
                           @click="doDeleteUser(idx)">
                        <i class="material-symbols-outlined">delete</i>
                     </a>
                  </td>
               </tr>
            </tbody>
         </table>
         <br>
         <div>
            <button class="btn"
                  @click="doAddUser">
               <i class="material-symbols-outlined right">add</i>
               Add new user
            </button>
         </div>
         <br><br>
         <div id="userConfigError" v-if="missingConfigurer">At least one user must have <i>Configure</i> permission.</div>
      </div>
   </div>
</template></dict-config-users>
</template>

<script>
import { dictionaryWorkspace } from '../js/dictionary-workspace.ts'
import DictConfigButtons from './dict-config-buttons.vue'
import DictNav from './dict-nav.vue'
import LoadingOverlay from './loading-overlay.vue'
export default {
   components: { DictConfigButtons, DictNav, LoadingOverlay },
   data() {
      return {
         missingConfigurer: false,
         state: {
            isLoading: true,
            isSaving: false,
            nextUserId: 0,
            data: {users: []}
         }
      }
   },

   async mounted() {
      const response = await dictionaryWorkspace.loadDictionaryConfig('users')
      if (response) {
         this.state.data = {users:[]}
         for (var key in response.content) {
            var info = response.content[key]
            info.email = key
            info.id = this.state.nextUserId++
            this.state.data.users.push(info)
         }
      }
      this.state.isLoading = false
   },

   methods: {
      onEmailInput(idx, evt){
         this.state.data.users[idx].email = evt.target.value
      },

      onPermissionChange(idx, evt){
         this.state.data.users[idx][evt.target.name] = evt.target.checked
      },

      doDeleteUser(idx) {
         this.state.data.users.splice(idx, 1)

      },

      doAddUser() {
         this.state.data.users.push({
            id: this.state.nextUserId++,
            email: "",
            canEdit: false,
            canConfig: false,
            canDownload: false,
            canUpload: false,
            isEditable: true
         })

         this.$nextTick(() => [...this.$el.querySelectorAll('table input[type="email"]')].at(-1)?.focus())
      },

      async saveData() {
         this.missingConfigurer = !this.state.data.users.some(row => row.canConfig)
         if (!this.missingConfigurer) {
            let data = {}
            this.state.data.users.forEach(u => {
               data[u.email] = {
                  canEdit: u.canEdit,
                  canConfig: u.canConfig,
                  canDownload: u.canDownload,
                  canUpload: u.canUpload
               }
            })
            this.state.isSaving = true
            await dictionaryWorkspace.updateDictionaryConfig('users', data)
            this.state.isSaving = false
         }
      }
   }
}
</script>

<style>
dict-config-users .user-checkbox {
   padding-right: 2em;
}
dict-config-users .delete-user, dict-config-users .add-user {
   float: right;
}
dict-config-users #userConfigError {
   margin-left: 1em;
   color: red;
}
</style>
