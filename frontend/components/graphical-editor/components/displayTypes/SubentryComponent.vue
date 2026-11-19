<template>
  <div class="subentry-component">
    <div>
      <section v-if="elementData.shown" class="subentry-element read-only">
        <ActionButtons
          v-if="!isAttribute"
          class="actions-button"
          :elementName="elementName"
          :elementEditorConfig="elementData"
          :editorChildNumber="editorChildNumber"
          :parentElementName="parentElementName"
          :numberOfElements="numberOfElements"
          :subentryElement="true"
          v-on="actions"
          @link-element="linkNewSubentry"
        />

        <RouterLink v-if="subentryLocation" :to="subentryLocation">{{ elementData.hideElementName ? "" : xmlName + ":" }} {{ displayValue }}</RouterLink>
      </section>
    </div>

    <SelectElementFromArray
      v-if="showSelectNewParent"
      v-model="showSelectNewParent"
      :name="elementData.editorLabel"
      :possible-parent-elements="newPossibleParents"
      @selected-element="handleSelectedNewParent"
    />
    <PopupDisplay
      z-index="10"
      v-model="showSubentriesSearchPopup"
      :hideActions="true"
      :title="`Link new ${xmlName}`"
      class="subentry-search-modal"
    >
      <h2>Link new {{ xmlName }}</h2>
      <div class="search-box">
        <input v-model="searchTerm" placeholder="Headword" aria-label="Headword" type="search" @keydown.enter.stop.prevent="getSubentries">
        <button @click="getSubentries">Search</button>
      </div>
      <p v-if="searching" role="status">Searching…</p>
      <p v-else-if="message" role="status">{{ message }}</p>
      <div v-else class="subentries">
        <label v-for="entry in subentries" :key="entry.id" class="subentry">
          <input type="checkbox" v-model="entry.checked" :disabled="!entry.checked && selectedCount >= availableSlots">
          <span class="text--xs"><RawHtml :content="entry.title"/></span>
        </label>
      </div>

      <div class="actions">
        <button @click="showSubentriesSearchPopup = false">Cancel</button>
        <button :disabled="!selectedCount || selectedCount > availableSlots" @click="saveSelectedSubentries">Save
          {{ selectedCount || "" }}
        </button>
      </div>
    </PopupDisplay>
  </div>
</template>

<script setup lang="ts">
import { computed, inject, onScopeDispose, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { editorContextKey, useEditorDraft } from '../../editor-context.ts'
import { entryEditorApi, type RelatedEntry } from '../../../../js/entry-editor-api.ts'
import { maximumChildCount, xmlElementName } from '../../../../js/xema.ts'
import { valueDefinition } from '../../editor-schema.ts'
import { useFieldActions, type EditorFieldProps, type EmitField } from '../../use-editor-field.ts'
import RawHtml from '../../../raw-html.vue'
import ActionButtons from '../ActionButtons.vue'
import PopupDisplay from '../PopupDisplay.vue'
import SelectElementFromArray from '../SelectElementFromArray.vue'

const props = defineProps<EditorFieldProps>()
const emit = defineEmits<EmitField>()
const { actions, newPossibleParents, showSelectNewParent, handleSelectedNewParent } = useFieldActions(props, emit)
const editor = inject(editorContextKey)!
const draft = useEditorDraft()
const route = useRoute()
const xema = computed(() => editor.config.xema)
const xmlName = computed(() => xmlElementName(xema.value, props.elementName))
const subentryLocation = computed(() => {
   const entryId = props.content.attributes?.id
   if (entryId) return {
      name: 'edit', params: { dictId: editor.dictId, doctype: xmlName.value, entryId, mode: 'edit' },
      query: route.query
   }
})
const displayValue = computed(() => {
   const definition = valueDefinition(xema.value, props.elementName, props.parentElementName, props.isAttribute)
   const title = props.content.attributes?.title
   return definition?.values?.find(item => item.value === title)?.caption ?? title ?? ''
})
const availableSlots = computed(() => {
   const rule = props.parentElementName && xema.value.elements[props.parentElementName]?.children?.find(child => child.name === props.elementName)
   return rule ? Math.max(0, maximumChildCount(rule.max) - props.numberOfElements) : 0
})
const showSubentriesSearchPopup = ref(false)
const searchTerm = ref('')
const subentries = ref<(RelatedEntry & { checked: boolean })[]>([])
const selectedCount = computed(() => subentries.value.filter(entry => entry.checked).length)
const searching = ref(false)
const message = ref('')
let subentryRequest: ReturnType<typeof entryEditorApi.subentries> | undefined
watch(showSubentriesSearchPopup, open => {
   if (!open) {
      subentryRequest = undefined
      searching.value = false
   }
})
onScopeDispose(() => { subentryRequest = undefined })

function linkNewSubentry() {
   searchTerm.value = draft.headword()
   showSubentriesSearchPopup.value = true
   void getSubentries()
}

async function getSubentries() {
   const request = entryEditorApi.subentries(editor.dictId, searchTerm.value.trim(), xmlName.value, props.elementName)
   subentryRequest = request
   subentries.value = []
   message.value = ''
   searching.value = true
   try {
      const result = await request
      if (subentryRequest !== request) return
      if (!result.success) throw new Error('Subentry search rejected')
      subentries.value = result.entries.map(entry => ({ ...entry, checked: false }))
      if (!subentries.value.length) message.value = 'No results found.'
   } catch {
      if (subentryRequest === request) message.value = 'Could not search subentries.'
   } finally {
      if (subentryRequest === request) searching.value = false
   }
}

function saveSelectedSubentries() {
   const selected = subentries.value.filter(entry => entry.checked)
   if (!selected.length || selected.length > availableSlots.value) return
   emit('create-element', selected.map(entry => ({
      name: props.elementName,
      content: { type: 'element', name: 'lxnm:subentryParent', attributes: {
         doctype: entry.doctype, id: entry.id, title: entry.sortkey ?? ''
      } }
   })))
   showSubentriesSearchPopup.value = false
}
</script>

<style lang="scss" scoped>
.subentry-component {
  padding: 8px 16px;
  margin-bottom: 8px;

  .subentry-element {
    display: flex;
    align-items: center;
    padding: 8px;
    color: #0000FF;
    text-align: left;
    text-decoration: underline;
    transition: 0.3s all;

    a {
      cursor: pointer;

      &:hover {
        color: #004494;
      }

      &:focus {
        border: 1px solid #f48c06;
      }
    }

    .actions-button {
      margin-right: 8px;
    }

    .preview-element {
      margin-left: -8px;
    }
  }

  .subentry-search-modal {
    .modal {
      max-height: 100%;
    }

    .modal-content {
      height: 70%;

    }

    .search-box {
      display: flex;
      align-items: center;
      justify-content: center;

      .type-toggle {
        margin-right: 16px;

        .lever {
          background-color: #005FCC !important;

          &:after {
            background-color: #F1F1F1 !important
          }
        }
      }

      input {
        max-width: 400px;
        margin: 0;
      }

      button {
        margin: 0 16px;
      }
    }

    .subentries {
      margin: 24px 0;
      max-height: calc(100% - 235px);
      overflow-Y: auto;
    }

    .subentry {
      display: flex;
      align-items: center;
      gap: 8px;
      color: inherit;
      text-align: left;
      padding: 4px;

      &:not(:first-child) {
        border-top: 1px solid #637383;
      }
    }

    .actions {
      position: absolute;
      margin-top: 24px;
      bottom: 46px;
      right: calc(10% + 16px);

      button {
        margin-left: 16px;
      }
    }
  }
}

</style>
