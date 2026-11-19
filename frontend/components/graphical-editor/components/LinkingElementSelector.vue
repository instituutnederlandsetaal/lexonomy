<template>
  <PopupDisplay
    class="linking-element-selector"
    :z-index="zIndex"
    :model-value="modelValue"
    @cancel="cancelAddLink"
    @save="linkToElement"
  >
    <h2>Link selected {{ computedElementName }} to:</h2>
    <div class="popup-header">
        <p class="text--md">Dictionary:</p>
        <select ref="dictionary" name="dictionary" v-model="selectedDictionary">
          <option v-for="dict in linkableDicts" :key="dict.id" :value="dict.id">{{ dict.title }}</option>
        </select>
      <input v-model="searchTerm" placeholder="Filter" type="text">
    </div>
    <div class="links">
      <div v-for="(el, i) in displayedLinks"
           :key="i"
           class="link"
           :class="{'selected': selectedElement === i}"
           @click="selectedElement = i"
      >
        <p>{{ el.element }}: {{ el.link }} ({{ el.preview }})</p>
      </div>
    </div>
  </PopupDisplay>
</template>

<script>
import Materialize from '../../../libs/materialize/materialize.min.js'
import { api } from '../../../js/api.ts'
import PopupDisplay from "./PopupDisplay.vue"
import computedElementName from "../shared-resources/mixins/computedElementName.js"

export default {
  inject: ['editorState', 'notifyLinksChanged'],
  name: "LinkingElementSelector",
  components: {PopupDisplay},
  mixins: [
    computedElementName
  ],
  emits: ['update:modelValue'],
  props: {
    modelValue: {
      type: Boolean,
      required: true
    },
    zIndex: {
      type: String,
      default: "100"
    },
    elementName: {
      type: String,
      default: ""
    },
    sourceId: {
      type: String,
      default: null
    },
  },
  computed: {
    linkableDicts() {
      return (this.editorState.entry.userDicts || []).filter(dict => dict.hasLinks)
    },
    displayedLinks() {
      const term = this.searchTerm.toLowerCase()
      return this.availableLinks.filter(link =>
        [link.element, link.link, link.preview].some(value => value.toLowerCase().includes(term))
      ).slice(0, 40)
    }
  },
  watch: {
    selectedDictionary() {
      this.getLinkableElements()
    },
    searchTerm() {
      this.selectedElement = null
    }
  },
  data() {
    return {
      selectedDictionary: null,
      selectedElement: null,
      searchTerm: "",
      availableLinks: [],
      saving: false
    }
  },
  created() {
    this.selectedDictionary = this.linkableDicts[0] && this.linkableDicts[0].id
  },
  mounted() {
    if (this.$refs.dictionary) {
      Materialize.FormSelect.init(this.$refs.dictionary)
    }
  },
  beforeUnmount() {
    if (this.$refs.dictionary) {
      Materialize.FormSelect.getInstance(this.$refs.dictionary)?.destroy()
    }
  },
  methods: {
    async getLinkableElements() {
      this.selectedElement = null
      this.availableLinks = []
      const dictionary = this.selectedDictionary
      if (!dictionary) return
      const request = api.get(`${encodeURIComponent(dictionary)}/linkablelist.json`)
      this.linkRequest = request
      try {
        const { links } = await request
        if (this.linkRequest === request) this.availableLinks = links
      } catch {
        if (this.linkRequest === request) Materialize.toast({ html: 'Could not load link targets.' })
      }
    },
    cancelAddLink() {
      this.$emit("update:modelValue", false)
    },
    async linkToElement() {
      const selectedEl = this.displayedLinks[this.selectedElement]
      if (!selectedEl || this.saving) return
      const params = {
        source_el: this.elementName,
        source_id: this.sourceId,
        target_dict: this.selectedDictionary,
        target_el: selectedEl.element,
        target_id: selectedEl.link,
      }
      this.saving = true
      try {
        const { success } = await api.get(`${encodeURIComponent(this.editorState.entry.dictId)}/links/add`, params)
        if (!success) throw new Error('Link rejected')
        this.notifyLinksChanged()
        Materialize.toast({html: "Linked!"})
        this.$emit("update:modelValue", false)
      } catch {
        Materialize.toast({html: "Could not add the link."})
      } finally {
        this.saving = false
      }
    }
  }
}
</script>

<style lang="scss">
.linking-element-selector {
  .popup-header {
    display: flex;
    align-items: center;

    p {
      margin-right: 8px;
    }

    .select-wrapper {
      max-width: fit-content;
      margin-right: 15px;
    }

    input {
      max-width: 400px;
      margin: 0;
    }

    button {
      margin: 0 16px;
    }

  }

  .links {
    margin: 24px 0;
    max-height: calc(100% - 165px);
    overflow-Y: auto;
  }

  .link {
    text-align: left;
    padding: 4px;
    cursor: pointer;

    &.selected {
      background: #dedede;
    }

    &:not(:first-child) {
      border-top: 1px solid #637383;
    }
  }
}
</style>
