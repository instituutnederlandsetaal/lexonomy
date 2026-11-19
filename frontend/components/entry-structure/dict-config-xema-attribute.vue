<template>
<dict-config-xema-attribute class="details">
    <div class="block">
        <div class="title">Attribute</div>
        <form @submit.prevent="saveNewId">
            <input class="textbox tech atName" :value="state.newAttributeId" @input="updateLocalData" data-path="newAttributeId">

            <button v-if="$props.attributeId !== state.newAttributeId && isValidXmlName(state.newAttributeId) && $props.xema.elements[$props.elementId].attributes[state.newAttributeId] == null" class="butRename iconAccept" type="submit">Rename</button>
            <div v-if="!isValidXmlName(state.newAttributeId)" class="warn errInvalidAtName" >Cannot rename, not a valid XML name.</div>
            <div v-if="state.newAttributeId != $props.attributeId && $props.xema.elements[$props.elementId].attributes[state.newAttributeId]" class="warn errAtNameExists">Cannot rename, such attribute already exists.</div>
        </form>
    </div>
    <div class="block">
        <div class="title">Content</div>
        <label class="radio"><input type="radio" name="filling" value="txt" @click="updateLocalData" data-path="config.filling" data-apply :checked="state.config.filling === 'txt'">Text</label>
        <label class="radio"><input type="radio" name="filling" value="lst" @click="updateLocalData" data-path="config.filling" data-apply :checked="state.config.filling === 'lst'">Value from list</label>
    </div>

    <div class="block" v-if="state.config.filling === 'lst'">
        <div class="title">Values</div>
        <table>
            <tbody>
                <tr v-for="(value, index) in state.config.values" :key="index">
                    <td class="cell1">
                        <form @submit.prevent="applyLocalData" style="white-space: nowrap;">
                            <input class="textbox val" placeholder="value" :value="value.value" @input="updateLocalData" :data-path="('config.values[') + (index) + ('].value')">
                            <input class="textbox cap" placeholder="caption" :value="value.caption" @input="updateLocalData" :data-path="('config.values[') + (index) + ('].caption')">
                            <template v-if="value.value !== $props.config.values?.[index]?.value || value.caption !== $props.config.values?.[index]?.caption">
                                <button class="change iconAccept" type="submit">Change</button>
                                <button class="cancel iconCancel" @click="resetLocalData" :data-path="('config.values[') + (index) + (']')" type="button">Cancel</button>
                            </template>
                        </form>
                    </td>
                    <td class="cell9">
                        <!-- <button class="iconOnly iconArrowUp">&nbsp;</button>
                        <button class="iconOnly iconArrowDown">&nbsp;</button> -->
                        <button class="iconOnly iconCross" @click="deleteLocalData" data-apply :data-path="('config.values[') + (index) + (']')">&nbsp;</button>
                    </td>
                </tr>
            </tbody>
        </table>

        <template v-if="!state.isAddingValue">
            <button class="butNewValue iconAdd" @click="beginNewValue">Add...</button>
        </template>
        <form v-if="state.isAddingValue" @submit.prevent="saveNewValue" style="white-space: nowrap;">
            <input class="textbox new val" data-path="newValue" placeholder="value" :value="state.newValue" @input="updateLocalData" autofocus>
            <input class="textbox new cap" data-path="newCaption" placeholder="caption" :value="state.newCaption" @input="updateLocalData">

            <button :style="state.newValue ? '' : 'display: none;'" class="butNewValueOK iconAccept" type="submit">Add</button>
            <button class="butNewValueCancel iconCancel" @click="cancelNewValue" type="button">Cancel</button>
        </form>

    </div>

</dict-config-xema-attribute>
</template>

<script>
import { isValidXmlName } from '../../js/xml.js'
export default {
   props: ["attributeId","xema","elementId","config","applyConfig","renameAttribute"],

   data() {
      return {
         state: {
            config: { values: [], ...JSON.parse(JSON.stringify(this.config || {})) },
            newAttributeId: this.attributeId,
            isAddingValue: false,
            newValue: '',
            newCaption: ''
         }
      }
   },

   methods: {
      updateLocalData(event) {
          // data-path is a string representing a javascript property accessor. such as 'someObject.someProperty[someIndex]'
          const path = event.target.getAttribute('data-path');

          this._setOrGetPath(this.state, path, event.target.value);
          if (event.target.hasAttribute('data-apply') || event.keyCode === 13) this.applyLocalData();

      },

      deleteLocalData(event) {
          const path = event.target.getAttribute('data-path');
          this._deletePath(this.state, path);
          if (event.target.hasAttribute('data-apply')) this.applyLocalData();

      },

      resetLocalData(event) {
          const path = event.target.getAttribute('data-path');
          this._setOrGetPath(this.state, path, this._setOrGetPath(this.$props, path));

      },

      applyLocalData(event) {
          const newConfig = JSON.parse(JSON.stringify(this.state.config));
          this.applyConfig(newConfig);
      },

      saveNewId(event) {
          const parentEl = this.$props.xema.elements[this.$props.elementId];
          if (this.state.newAttributeId === this.attributeId)
              return;
          if (parentEl.attributes[this.state.newAttributeId])
              return;
          if (!this.isValidXmlName(this.state.newAttributeId))
              return;

          this.$props.renameAttribute(this.state.newAttributeId);
          // change should flow down automatically.
      },

      beginNewValue(event) {
          this.state.isAddingValue = true;

      },

      cancelNewValue(event) {
          this.state.isAddingValue = false;
          this.state.newValue = '';
          this.state.newCaption = '';

      },

      saveNewValue(event) {
          if (!this.state.newValue) return
          this.state.config.values ??= []
          this.state.config.values.push({
              value: this.state.newValue,
              caption: this.state.newCaption,
          })
          // Keep open
          // this.state.isAddingValue = false;
          this.state.newValue = '';
          this.state.newCaption = '';
          this.applyLocalData();
          this.$el.querySelector('[data-path="newValue"]').focus();
          event.preventDefault(); // form submit
      },

      _setOrGetPath() {
          const [object, path] = arguments;
          // see if we actually got a new value to set, to differentiate between _setOrGet(state, path) and _setOrGet(state, path, undefined).
          let newValue = undefined;
          let newValueProvided = false;
          if (arguments.length > 2) {
              newValue = arguments[2];
              newValueProvided = true;
          }

          const pathParts = path.split(/[\.\[\]\'\"]/).filter(p => p);
          const lastIndex = newValueProvided ? pathParts.pop() : undefined;
          const v = pathParts.reduce((o, p) => o ? o[p] : undefined, object);
          if (!newValueProvided) return v;
          v[lastIndex] = newValue === undefined ? undefined : JSON.parse(JSON.stringify(newValue));
      },

      _deletePath(object, path) {
          const pathParts = path.split(/[\.\[\]\'\"]/).filter(p => p);
          const lastIndex = pathParts.pop();
          const v = pathParts.reduce((o, p) => o ? o[p] : undefined, object);
          if (Array.isArray(v)) v.splice(lastIndex, 1)
          else delete v[lastIndex]
      },

      isValidXmlName
   }
}
</script>

<style>
dict-config-xema-attribute {
    display: block;
}
</style>
