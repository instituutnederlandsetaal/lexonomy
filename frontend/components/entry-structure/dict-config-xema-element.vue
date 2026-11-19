<template>
<dict-config-xema-element>
    <!-- element name configuration -->
    <div class="block">
        <div class="title">Element</div>

        <input class="textbox tech elName" :value="state.config.elementName" @input="updateLocalData" data-path="config.elementName">
        <button v-if="isRoot" type="button" class="iconOnly iconCross" @click="deleteElement" title="Delete element">&nbsp;</button>

        <template v-if="state.config.elementName !== ($props.config.elementName ? $props.config.elementName : $props.elementId)">
            <button v-if="isValidXmlName(state.config.elementName)"
                type="button"
                class="butRename iconAccept"
                @click="applyLocalData"
            >
                Rename
            </button>
            <button
                type="button"
                class="butRenameCancel iconCancel"
                @click="resetLocalData"
                data-path="config.elementName"
            >
                Cancel renaming
            </button>
            <div v-if="!isValidXmlName(state.config.elementName)" class="warn">{{ state.config.elementName }} is not a valid element name</div>
        </template>
    </div>

    <!-- element attribute list & attribute selector -->
    <div class="block">
        <div class="title tight">Attributes</div>

        <table style="table-layout: auto;">
            <tbody>
                <tr v-for="att in Object.entries(state.config.attributes).sort((a, b) => a[0].localeCompare(b[0]))" :key="att[0]">
                    <td @click="selectAttribute" :data-name="att[0]"><span class="tech"><span class="ats">@</span><span class="att">{{ att[0] }}</span></span></td>
                    <td>
                        <div style="display: flex; flex-wrap: wrap; align-items: center;">
                            <label class="radio"><input type="radio" :name="`optionality[${att[0]}]`" value="optional"   :checked="att[1].optionality === 'optional'" @change="updateLocalData" data-apply :data-path="`config.attributes.${att[0]}.optionality`">optional</label>
                            <label class="radio"><input type="radio" :name="`optionality[${att[0]}]`" value="obligatory" :checked="att[1].optionality === 'obligatory'" @change="updateLocalData" data-apply :data-path="`config.attributes.${att[0]}.optionality`">obligatory</label>
                            <button class="iconOnly iconCross" @click="deleteLocalData" :data-path="`config.attributes.${att[0]}`" data-apply>&nbsp;</button>
                        </div>
                    </td>
                </tr>
            </tbody>
        </table>

        <button
            v-if="!state.isAddingAttribute"
            class="butAtNewOpener iconAdd"
            @click="beginNewAttribute"
        >
            Add...
        </button>

        <template v-if="state.isAddingAttribute">
            <form @submit="saveNewAttribute" @reset="cancelNewAttribute">
                <input class="textbox tech atName txtAtNew" @input="updateLocalData" data-path="newAttributeName" autofocus :value="state.newAttributeName">
                <!-- note: always output this button, only hide in css. If we remove this button pressing enter in the input above will print a console warning because there will be no submit button in the form. -->
                <button :style="!(state.newAttributeName && isValidXmlName(state.newAttributeName)) ? 'display: none;' : ''" type="submit" class="butAtNew iconAccept">Add</button>
                <button class="butAtNewCancel iconCancel" type="reset">Cancel</button>
            </form>

            <div class="warn errInvalidAtName" v-if="!isValidXmlName(state.newAttributeName)">Cannot add, not a valid XML name.</div>
            <div class="warn errAtNameExists" v-if="state.config.attributes[state.newAttributeName]">Cannot add, such attribute already exists.</div>
        </template>
    </div>

    <!-- element content type selection -->
    <div class="block">
        <div class="title">Content</div>
        <label class="radio"><input type="radio" name="filling" value="chd" @change="updateLocalData" data-apply data-path="config.filling" :checked="state.config.filling === 'chd'">Child elements</label>
        <br>
        <label class="radio"><input type="radio" name="filling" value="txt" @change="updateLocalData" data-apply data-path="config.filling" :checked="state.config.filling === 'txt'">Text</label>
        <br>
        <label class="radio"><input type="radio" name="filling" value="inl" @change="updateLocalData" data-apply data-path="config.filling" :checked="state.config.filling === 'inl'">Text with markup</label>
        <br>
        <label class="radio"><input type="radio" name="filling" value="lst" @change="updateLocalData" data-apply data-path="config.filling" :checked="state.config.filling === 'lst'">Value from list</label>
        <br>
        <label class="radio"><input type="radio" name="filling" value="emp" @change="updateLocalData" data-apply data-path="config.filling" :checked="state.config.filling === 'emp'">Empty</label>
        <br>
        <label class="radio"><input type="radio" name="filling" value="med" @change="updateLocalData" data-apply data-path="config.filling" :checked="state.config.filling === 'med'">Media</label>
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
                        <button class="iconOnly iconCross" @click="deleteLocalData" data-apply :data-path="('config.values[') + (index) + (']')">&nbsp;</button>
                    </td>
                </tr>
            </tbody>
        </table>

        <template v-if="!state.isAddingValue">
            <button class="butNewValue iconAdd" @click="beginNewValue">Add...</button>
        </template>
        <form v-if="state.isAddingValue" @submit="saveNewValue" style="white-space: nowrap;">
            <input class="textbox new val" data-path="newValue" placeholder="value" :value="state.newValue" @input="updateLocalData" autofocus>
            <input class="textbox new cap" data-path="newCaption" placeholder="caption" :value="state.newCaption" @input="updateLocalData">

            <button v-if="state.newValue" class="butNewValueOK iconAccept">Add</button>
            <button class="butNewValueCancel iconCancel" @click="cancelNewValue" type="button">Cancel</button>
            <div v-if="state.newValueError" class="warn">{{ state.newValueError }}</div>
        </form>
    </div>

    <!-- child element selection/min-max/creation -->
    <div class="block" v-if="state.config.filling === 'inl' || state.config.filling === 'chd'">
        <div class="title tight">Child elements</div>
        <table v-if="computedChildren.length" style="table-layout: auto;">
            <tbody>
                <tr v-for="(child, index) in computedChildren" :key="index">
                    <td @click="selectElement" :data-name="child.id">
                        <span class="tech">
                            <span class="brak">&lt;</span>
                            <span class="elm">{{ child.elementName }}</span>
                            <span class="brak">&gt;</span>
                        </span>
                    </td>
                    <td style="white-space: nowrap;" >
                        <label>min <input class="textbox min" placeholder="0" type="number" size="2" style="min-width: 3em" :value="child.min" @change="updateLocalData" data-apply :data-path="`config.children[${index}].min`"></label>
                        <label>max <input class="textbox max" placeholder="∞" type="number" size="2" style="min-width: 3em" :value="child.max" @change="updateLocalData" data-apply :data-path="`config.children[${index}].max`"></label>
                    </td>
                    <td style="white-space: nowrap;" >
                        <button class="iconOnly iconArrowUp" type="button" @click="moveChildUp" :data-index="index">&nbsp;</button>
                        <button class="iconOnly iconArrowDown" type="button" @click="moveChildDown" :data-index="index">&nbsp;</button>
                        <button class="iconOnly iconCross" type="button" @click="deleteChild" :data-index="index">&nbsp;</button>
                    </td>

                    <td>
                        <!-- when child is also used elsewhere: make unique (need parent of child) -->
                        <button v-if="child.isUsedElsewhere" @click="makeUnique" :data-name="child.id" style="padding: 5px; margin-left: 15px;">make&nbsp;unique</button>

                        <!-- when child has similarly named elements elsewhere: allow replacing with those similar elements (need parent of child) -->
                        <div v-if="child.hasNameSiblings" style="display: inline-block; margin-left: 15px;">
                            Element {{ child.elementName }} has different configurations:
                            <select :data-name="child.id">
                                <option v-for="sibling in child.nameSiblings" :key="sibling.id" :value="sibling.id">{{ sibling.parentElementName }}/{{ sibling.elementName }}</option>
                            </select>
                            <button @click="replaceWithNameSibling" :data-name="child.id" style="padding: 5px;">use&nbsp;instead</button>
                        </div>

                    </td>
                </tr>
            </tbody>
        </table>

        <button v-if="!state.isAddingElement" class="butElNewOpener iconAdd" @click="beginNewElement">Add...</button>
        <form v-if="state.isAddingElement" @submit="saveNewElement">
            <input class="textbox tech elName txtElNew" :value="state.newElementName" @input="updateLocalData" data-path="newElementName" autofocus>
            <button :style="!(state.newElementName && isValidXmlName(state.newElementName)) ? 'display: none!important;' : ''" class="butElNew iconAccept" type="submit">Add</button>
            <button class="butElNewCancel iconCancel" type="button" @click="cancelNewElement" >Cancel</button>
            <div v-if="state.newElementName && !isValidXmlName(state.newElementName)" class="warn errInvalidElName">Cannot add, not a valid XML name.</div>
        </form>
    </div>

</dict-config-xema-element>
</template>

<script>
import { isValidXmlName } from '../../js/xml.js'
export default {
   props: ["config","elementId","xema","applyConfig","createElement","removeElement","selectElementOrAttribute"],

   data() {
      const config = JSON.parse(JSON.stringify(this.config || {}))
      return {
         state: {
            config: {
               children: [],
               attributes: {},
               filling: 'chd',
               values: [],
               ...config,
               elementName: config.elementName || this.elementId
            },
            isAddingAttribute: false,
            newAttributeName: '',
            isAddingElement: false,
            newElementName: '',
            isAddingValue: false,
            newValue: '',
            newCaption: '',
            newValueError: ''
         }
      }
   },

   computed: {
      isRoot() {
         return !Object.values(this.xema.elements).some(element => element.children?.some(child => child.name === this.elementId))
      },
      computedChildren() {
          const xemaEntries = Object.entries(this.$props.xema.elements).map(([id, config]) => ({
              ...config,
              id,
              elementName: config.elementName || id
          }));

          // Do some preprocessing on this element's children
          // So we can easily see which children are also used elsewhere
          // and which children have similarly named children elsewhere
          return (this.state.config.children || []).map(({name, min, max}) => {
              const id = name;
              const elementName = this.xema.elements[name]?.elementName || id;
              // check if other elements (than this one) may contain this precise child
              const isUsedElsewhere = xemaEntries.some(e => e.children && e.children.some(c => c.name === id) && e.id !== this.$props.elementId);
              // Find other elements with the same name as this child, that have a different ID
              // So in essence: different configs for the same element.
              const nameSiblings = xemaEntries
                  .filter(e => e.elementName === elementName && e.id !== id) // all with the same elementName but different ID
                  .map(nameSibling => {
                      const firstParent = xemaEntries.find(e => e.children && e.children.some(c => c.name === nameSibling.id));
                      return {
                          ...nameSibling,
                          parentElementName: firstParent ? firstParent.elementName : '[no parent]'
                      }
                  });
              const hasNameSiblings = nameSiblings.length > 0;
              return {
                  id,
                  min,
                  max,
                  elementName,
                  isUsedElsewhere,
                  hasNameSiblings,
                  nameSiblings
              }
          });
      }
   },

   methods: {
      updateLocalData(event) {
          // data-path is a string representing a javascript property accessor. such as 'someObject.someProperty[someIndex]'
          const path = event.currentTarget.getAttribute('data-path');

          // apply new value in local state
          this._setOrGetPath(this.state, path, event.target.value);
          if (event.currentTarget.hasAttribute('data-apply') || event.keyCode === 13) this.applyLocalData();

      },

      deleteLocalData(event) {
          const path = event.currentTarget.getAttribute('data-path');
          this._deletePath(this.state, path);
          if (event.currentTarget.hasAttribute('data-apply')) this.applyLocalData();

      },

      resetLocalData(event) {
          const path = event.currentTarget.getAttribute('data-path');
          const previousValue = path === 'config.elementName'
              ? this.config.elementName || this.elementId
              : this._setOrGetPath(this.$props, path);
          this._setOrGetPath(this.state, path, previousValue);

      },

      applyLocalData(event) {
          // sanitize
          const newConfig = JSON.parse(JSON.stringify(this.state.config));
          if (!this.isValidXmlName(newConfig.elementName)) {
              newConfig.elementName = this.$props.config.elementName || this.$props.elementId; // not valid - reset to whatever it was prior to saving
          }

          this.applyConfig(this.$props.elementId, newConfig);
      },

      beginNewAttribute(event) {
          this.state.isAddingAttribute = true;

      },

      cancelNewAttribute(event) {
          event.preventDefault(); // form reset event.
          this.state.isAddingAttribute = false;
          this.state.newAttributeName = '';

      },

      saveNewAttribute(event) {
          // sanity check.
          if (!this.state.config.attributes[this.state.newAttributeName] && this.state.newAttributeName && this.isValidXmlName(this.state.newAttributeName)) {
              this.state.config.attributes[this.state.newAttributeName] = {
                  optionality: 'optional',
                  filling: 'txt',
                  values: []
              }
              this.state.newAttributeName = '';
              this.applyLocalData();

          }
          event.preventDefault(); // usually form submit event.
      },

      beginNewElement(event) {
          this.state.isAddingElement = true;

      },

      cancelNewElement(event) {
          this.state.isAddingElement = false;
          event.preventDefault();

      },

      saveNewElement(event) {
          event.preventDefault();
          if (!this.isValidXmlName(this.state.newElementName)) {
              return;
          }
          const idOfNewChild = this.state.newElementName;
          if (!this.$props.xema.elements[idOfNewChild]) { // doesn't exist (yet) - create!
              this.$props.createElement(this.state.newElementName, {
                  elementName: this.state.newElementName,
                  filling: 'emp',
                  children: [],
                  values: [],
                  attributes: {}
              });
          }

          this.state.newElementName = '';
          this.state.config.children.push({name: idOfNewChild})
          this.applyLocalData();
      },

      makeUnique(event) {
          const currentChildId = event.currentTarget.getAttribute('data-name');
          const currentChildConfig = JSON.parse(JSON.stringify(this.$props.xema.elements[currentChildId]));
          currentChildConfig.elementName = currentChildConfig.elementName || currentChildId; // make sure we set the element name, since the ID will change and so will no longer work as fallback.

          // create a unique id for the clone by appending numbers
          let n = 0;
          let newChildId = currentChildId + n;
          while (this.$props.xema.elements[newChildId]) {
              newChildId = currentChildId + (++n);
          }

          // now clone the child under the new id
          this.$props.createElement(newChildId, currentChildConfig);
          // replace the current child with the new (unique) child.
          this.state.config.children.forEach(c => {
              if (c.name == currentChildId) c.name = newChildId;
          })
          // and save!
          this.applyLocalData(); // propagate to parent

      },

      replaceWithNameSibling(event) {
          const childIdToReplace = event.currentTarget.getAttribute('data-name');
          const childIdToReplaceWith = this.$el.querySelector(`select[data-name="${childIdToReplace}"]`).value; // this.$ is scope selector
          if (!childIdToReplaceWith) return; // user should make a selection first.

          const childHasOtherParents = Object.entries(this.$props.xema.elements).some(([id, element]) => id !== this.$props.elementId && element.children?.some(c => c.name === childIdToReplace));

          // now replace
          // first replace our own child with the chosen one
          this.state.config.children.forEach(c => {
              if (c.name === childIdToReplace) c.name = childIdToReplaceWith;
          });

          this.applyLocalData();
          if (!childHasOtherParents) this.removeElement(childIdToReplace);

      },

      deleteElement() {
          this.removeElement(this.$props.elementId);
      },

      deleteChild(event) {
          const index = event.currentTarget.getAttribute('data-index');
          const child = this.computedChildren[index];
          this.state.config.children.splice(index, 1);
          this.applyLocalData();
          if (!child.isUsedElsewhere) {
              this.removeElement(child.id);
          }
      },

      swapItems(collection, from, to) {
          const tmp = collection[to];
          collection[to] = collection[from]
          collection[from] = tmp
      },

      moveChildDown(event) {
          const from = Number(event.currentTarget.getAttribute('data-index'));
          const to = from + 1;
          this.swapItems(this.state.config.children, from, to);
          this.applyLocalData();

      },

      moveChildUp(event) {
          const from = Number(event.currentTarget.getAttribute('data-index'));
          const to = from - 1;
          this.swapItems(this.state.config.children, from, to);
          this.applyLocalData();

      },

      beginNewValue(event) {
          this.state.isAddingValue = true;

      },

      cancelNewValue(event) {
          this.state.isAddingValue = false;
          this.state.newValue = '';
          this.state.newCaption = '';
          this.state.newValueError = '';

      },

      saveNewValue(event) {
          if (event) event.preventDefault(); // form submit

          const value = this.state.newValue;
          const caption = this.state.newCaption;
          if (this.state.config.values?.find(v => v.value === value)) {
              this.state.newValueError = `Value ${value} already exists`;
              return;
          }

          this.state.config.values ??= []
          this.state.config.values.push({
              value: this.state.newValue,
              caption: this.state.newCaption,
          })
          this.state.newValueError = '';
          // Keep open, nice and simple.
          // this.state.isAddingValue = false;
          this.state.newValue = '';
          this.state.newCaption = '';
          this.applyLocalData();
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

      selectAttribute(event) {
          // focus attribute
          this.$props.selectElementOrAttribute(this.$props.elementId, event.currentTarget.getAttribute('data-name'));
      },

      selectElement(event) {
          this.$props.selectElementOrAttribute(event.currentTarget.getAttribute('data-name'), undefined);
      },

      isValidXmlName
   }
}
</script>

<style>

</style>
