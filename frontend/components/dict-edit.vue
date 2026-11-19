<template>
<dict-edit>
   <LoadingOverlay v-if="myDictionaries.loading || activeDictionary.isDictionaryLoading"/>
   <DictNav :links="[['edit', 'Edit']]"/>
   <h1 class="header">
      {{ activeDictionary.title }}
      <span v-if="activeDictionary.entryCount"
            class="totalEntries">total {{ activeDictionary.entryCount }} entries</span>
   </h1>
   <template v-if="activeDictionary.config && !myDictionaries.loading">
      <div v-if="activeDictionary.doctypes.length > 1"
            class="doctypes">
         <ul class="tabs">
            <li v-for="type in activeDictionary.doctypes" :key="type" :active="type === activeDictionary.doctype" class="tab col s2">
               <a @click="doChangeDoctype(type)">{{ type }}</a>
            </li>
         </ul>
      </div>
      <div id="dictEditContainer" >
         <div ref="entryColumn" class="dictLeftCol"
               :style="{ width: state.columnWidth || `max(${activeDictionary.config.flagging.flags.length ? '25vw' : '20vw'}, 250px)` }">
            <template v-if="activeDictionary.entryList">
               <DictEntryFilter @search="searchEntriesFromRoute"/>
               <DictEntryPagination/>
               <div class="entry-list collection">
                  <div v-for="(entry, idx) in activeDictionary.entryList" :key="entry.id"
                        :data-idx="idx" class="collection-item"
                        :class="{ saving: entry.isSaving, selected: entry.id == activeDictionary.entryId, focused: idx + 1 === state.cursorPosition }"
                        @click="onHeadwordClick(entry.id, $event)">
                     <span class="lineNum">{{ idx + 1 }}.</span>
                     <RouterLink :to="{ name: 'edit', params: { dictId: activeDictionary.dictId, doctype: activeDictionary.doctype, entryId: entry.id, mode: activeDictionary.mode }, query: $route.query }"
                           class="headword-link" :class="{ 'red-text': entry.id == activeDictionary.entryId }"
                           @click.stop="onDocumentClick">
                        <RawHtml :content="entry.title || '&amp;nbsp;' "/>
                     </RouterLink>
                     <span v-if="activeDictionary.config.flagging.flags.length"
                           @click.stop="onOpenFlagMenuClick(entry, $event)"
                           class="flag" :class="entry.flag ? 'badge' : 'noFlag'"
                           :style="getFlagStyle(entry.flag)">
                        {{ flagsByName.get(entry.flag)?.label || entry.flag || "No flag" }}
                     </span>
                  </div>
                  <div v-if="!activeDictionary.entryList.length && !activeDictionary.isEntryListLoading"
                        style="padding-top: 10vh;">
                     <h2 class="grey-text center-align">No entries</h2>
                  </div>
               </div>
               <ul v-if="activeDictionary.config.flagging.flags.length"
                     id="flagDropdown"
                     class="dropdown-content flagDropdown">
                  <li data-flag="">
                     <i class="material-symbols-outlined"
                           style="color: grey">label_outline</i>
                     <div>no flag</div>
                     <div class="right flagKey">delete</div>
                  </li>
                  <li v-for="flag in activeDictionary.config.flagging.flags" :key="flag.name"
                        :data-flag="flag.name">
                     <i class="material-symbols-outlined" :style="{ color: flag.color }">label</i>
                     <div>{{ flag.label }}</div>
                     <div class="right flagKey">{{ flag.key }}</div>
                  </li>
               </ul>
            </template>
            <LoadingOverlay v-if="activeDictionary.isEntryListLoading"/>
         </div>
         <div class="resizeHandle"
               @mousedown="onResizeHandleMouseDown"></div>
         <div class="dictRightCol">
            <DictEditEntry ref="entryEditor" :dictionary-config="activeDictionary.config"/>
         </div>
      </div>
   </template>
</dict-edit>
</template>

<script>
import Materialize from '../libs/materialize/materialize.min.js'
import { flagTextColor } from './entry-flags.js'
import { activeDictionary, dictionaryWorkspace } from '../js/dictionary-workspace.ts'
import { myDictionaries } from '../js/my-dictionaries.ts'
import { searchEntriesFromRoute } from '../js/entry-search.ts'
import DictEditEntry from './dict-edit-entry.vue'
import DictEntryFilter from './dict-entry-filter.vue'
import DictEntryPagination from './dict-entry-pagination.vue'
import DictNav from './dict-nav.vue'
import LoadingOverlay from './loading-overlay.vue'
import RawHtml from './raw-html.vue'

export default {
   setup: () => ({ activeDictionary, myDictionaries, searchEntriesFromRoute }),
   components: { DictEditEntry, DictEntryFilter, DictEntryPagination, DictNav, LoadingOverlay, RawHtml },
   data() {
      return {
         state: {
            focused: false,
            columnWidth: '',
            mousePos: null,
            cursorPosition: null,
            selectFirst: null
         }
      }
   },

   computed: {
      flagsByName() {
         return new Map(this.activeDictionary.config?.flagging.flags.map(flag => [flag.name, flag]))
      }
   },

   watch: {
      'activeDictionary.entryList'(entries) {
         this.setCursorByEntryId()
         if (entries && this.state.selectFirst === this.activeDictionary.doctype) {
            this.state.selectFirst = null
            if (entries.length) this.selectEntry(entries[0].id)
         }
      },
      'activeDictionary.entryId': 'setCursorByEntryId'
   },

   mounted() {
      document.addEventListener('click', this.onDocumentClick)
      document.addEventListener('keydown', this.onDocumentKeyDown)
      this.setCursorByEntryId()
   },

   beforeUnmount() {
      document.removeEventListener('click', this.onDocumentClick)
      document.removeEventListener('keydown', this.onDocumentKeyDown)
      this.onDocumentMouseUp()
      this.state.clearFlagMenu?.()
   },

   methods: {
      getFlagStyle(flag){
         const bgColor = this.flagsByName.get(flag)?.color || 'initial'
         let color = flagTextColor(bgColor)
         return `color: ${color}; background-color: ${bgColor}`
      },

      onHeadwordClick(entryId, event) {
         this.onDocumentClick(event)
         if (!(event.ctrlKey || event.metaKey || event.shiftKey || event.altKey)) this.selectEntry(entryId)
      },

      selectEntry(entryId) {
         if (entryId === this.activeDictionary.entryId) return
         const { dictId, doctype, mode } = this.activeDictionary
         return this.$router.push({ name: 'edit', params: { dictId, doctype, entryId, mode }, query: this.$route.query })
      },

      onOpenFlagMenuClick(entry, evt){
         this.state.clearFlagMenu?.()
         const trigger = evt.currentTarget
         const menu = this.$el.querySelector('#flagDropdown').cloneNode(true)
         // Materialize moves its menu into the body, so give it a copy of the Vue-owned node.
         menu.id = 'entryFlagMenu'
         document.body.append(menu)
         menu.addEventListener('click', event => {
            const flag = event.target.closest('li')?.dataset.flag
            if (flag !== undefined) dictionaryWorkspace.setEntryFlag(entry.id, flag)
         })
         trigger.dataset.target = menu.id
         const dropdown = Materialize.Dropdown.init(trigger, {
            constrainWidth: false,
            coverTrigger: false,
            container: document.body,
            onCloseEnd: () => this.state.clearFlagMenu?.()
         })
         this.state.clearFlagMenu = () => {
            dropdown.destroy()
            menu.remove()
            delete trigger.dataset.target
            this.state.clearFlagMenu = null
         }
         dropdown.open()
      },

      onDocumentClick(evt){
         const entryList = this.$el.querySelector('.entry-list')
         if(entryList && evt.target.isConnected){
            let inComponent = entryList.contains(evt.target)
            if(inComponent || inComponent != this.state.focused){
               this.state.focused = inComponent
               const index = inComponent && evt.target.closest('.collection-item')?.dataset.idx
               this.state.cursorPosition = index ? Number(index) + 1 : null
               this.updateCursor()
            }
         }
      },

      onDocumentKeyDown(event) {
         const key = event.key.toLowerCase()
         if ((event.ctrlKey || event.metaKey) && event.shiftKey && ['e', 's'].includes(key)) {
            event.preventDefault()
            event.stopImmediatePropagation()
            if (key === 'e') this.$refs.entryEditor?.toggleEditing()
            else this.$refs.entryEditor?.save()
            return
         }
         if (!this.state.focused || !this.activeDictionary.entryList?.length ||
             event.target.closest?.('input, textarea, select, [contenteditable]')) return
         const entry = this.activeDictionary.entryList[this.state.cursorPosition - 1]
         switch (event.key) {
            case 'ArrowUp': this.moveCursorUp(1); break
            case 'ArrowDown': this.moveCursorDown(1); break
            case 'PageUp': this.moveCursorUp(10); break
            case 'PageDown': this.moveCursorDown(10); break
            case 'Enter': if (entry) this.selectEntry(entry.id, event); break
            default: {
               const flags = this.activeDictionary.config.flagging.flags
               const flag = event.key === 'Delete' && flags.length
                  ? '' : flags.find(item => item.key === event.key)?.name
               if (!entry || flag === undefined) return
               dictionaryWorkspace.setEntryFlag(entry.id, flag)
            }
         }
         event.preventDefault()
      },

      onResizeHandleMouseDown(evt){
         this.state.mousePos = evt.x
         document.addEventListener("mouseup", this.onDocumentMouseUp, false)
         document.addEventListener("mousemove", this.resizeColumn, false)
         document.body.style.userSelect = 'none'
      },

      onDocumentMouseUp(){
         document.removeEventListener("mousemove", this.resizeColumn, false)
         document.removeEventListener("mouseup", this.onDocumentMouseUp, false)
         document.body.style.userSelect = ''
      },

      async doChangeDoctype(doctype) {
         if (doctype === this.activeDictionary.doctype) return
         const dictId = this.activeDictionary.dictId
         this.state.selectFirst = doctype
         const failure = await this.$router.push({ name: 'edit', params: { dictId, doctype, entryId: '', mode: '' } })
         if (failure && this.state.selectFirst === doctype) this.state.selectFirst = null
      },

      moveCursorDown(step){
         if(!this.state.cursorPosition){
            this.state.cursorPosition = 1
         } else{
            this.state.cursorPosition = Math.min(this.state.cursorPosition + (step || 1), this.activeDictionary.entryList.length)
         }
         this.updateCursor()
      },

      moveCursorUp(step){
         if(!this.state.cursorPosition){
           this.state.cursorPosition = this.activeDictionary.entryList.length
         } else {
            this.state.cursorPosition = Math.max(1,  this.state.cursorPosition - (step || 1))
         }
         this.updateCursor()
      },

      updateCursor(){
         this.$nextTick(this.scrollSelectedIntoView)
      },

      scrollSelectedIntoView(){
         const list = this.$el.querySelector('.entry-list')
         if(!list){
            return
         }
         const selectedItem = list.querySelector('.focused')
         if(selectedItem){
            let offsetTop = selectedItem.offsetTop
            let rowHeight = selectedItem.clientHeight
            let min = list.scrollTop
            let max = list.scrollTop + list.clientHeight - rowHeight
            if(offsetTop < min){
               list.scrollTop = offsetTop
            } else if(offsetTop > max){
               list.scrollTop = offsetTop - list.clientHeight + rowHeight
            }
         }
      },

      resizeColumn(evt){
         const distance = evt.x - this.state.mousePos
         this.state.mousePos = evt.x
         const column = this.$refs.entryColumn
         this.state.columnWidth = Math.max(200, column.getBoundingClientRect().width + distance) + 'px'
      },

      setCursorByEntryId(){
         if(this.activeDictionary.entryId && this.activeDictionary.entryList){
            let idx = this.activeDictionary.entryList.findIndex(e => e.id == this.activeDictionary.entryId)
            if(idx != -1){
               this.state.cursorPosition = idx + 1
               this.updateCursor()
            }
         }
      }
   }
}
</script>

<style>
dict-edit #dictEditContainer{
   display: flex;
}
dict-edit .totalEntries{
   font-size: 0.85rem;
   color: #b8b8b8;
   margin-left: 1.3rem;
   text-transform: none;
}
dict-edit ul.select-dropdown,
dict-edit ul.dropdown-content {
   width: 200% !important;
}
dict-edit li > span {
   white-space: nowrap;
}
dict-edit .resizeHandle{
   cursor: ew-resize;
   width: 5px;
   min-height: 100%;
   background-color: whitesmoke;
   margin: 0 10px;
}
dict-edit .resizeHandle:hover{
   background-color: #cfcfcf;
}
dict-edit .entry-list {
   max-height: 80vh;
   overflow-y: auto;
   margin: 0;
}
dict-edit .dictLeftCol{
   min-width: 200px;
   min-height: 50vh;
   position: relative;
   display: flex;
   flex-direction: column;
   gap: 0.25rem;
}
dict-edit .dictRightCol{
   min-width: 500px;
   flex: 1;
}
dict-edit .collection-item{
   position: relative;
   display: flex;
   border-left: 5px solid white;
   padding-left: 0.2rem;
}
dict-edit .collection-item.selected{
   border-left-color: #000;
}
dict-edit .collection-item .headword-link{
   text-decoration: none;
   font-size: 1.2rem;
   letter-spacing: 1px;
   margin-right: auto;
}
dict-edit .collection-item .flag{
   cursor: pointer;
}
dict-edit .collection-item .flagKey{
   font-family: monospace;
}
dict-edit .collection-item .badge{
   font-weight: bold;
   font-size: 1rem;
   color: #fff;
   white-space: nowrap;
   min-width: auto;
   border-radius: 2px;
   box-shadow: 0 2px 2px 0 rgb(0 0 0 / 14%),
      0 3px 1px -2px rgb(0 0 0 / 12%),
      0 1px 5px 0 rgb(0 0 0 / 20%);
}
dict-edit .collection-item .noFlag{
   font-size: 1rem;
   color: grey;
}
dict-edit .collection-item.saving::before{
   content: '';
   position: absolute;
   left: 0;
   right: 0;
   top: 0;
   bottom: 0;
   background-color: #ffffffe8;
   line-height: 100%;
   z-index: 500;
}
dict-edit .collection-item.saving::after{
   content: 'saving...';
   position: absolute;
   transform: translateX(-50%) translateY(-50%);
   left: 50%;
   top: 50%;
   color: #6e6e6e;
   z-index: 501;
   font-size: 1.3rem;
   text-transform: uppercase;
}
dict-edit .collection-item.focused{
   background-color: #eceff1;
}
dict-edit .lineNum{
   font-size: 0.8rem;
   color: #b8b8b8;
   margin-right: 10px;
   min-width: 30px;
   text-align: right;
}
</style>
