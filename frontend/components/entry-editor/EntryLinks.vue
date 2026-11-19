<template>
   <section v-for="section in sections" :id="section.id" :key="section.id">
      <h2>{{ section.heading }}</h2>
      <ul>
         <li v-for="item in section.links" :key="item.link.link_id">
            {{ item.label }} {{ section.arrow }}
            <RouterLink v-if="item.to" :to="item.to">{{ item.peer }}</RouterLink>
            <template v-else>{{ item.peer }}</template>
            {{ item.link.confidence ? `(${item.link.confidence})` : '' }}
            <button v-if="canDelete && !section.incoming" class="linkdelete" type="button"
                    :disabled="removing.has(item.link.link_id)" @click="remove(item.link)">×delete</button>
         </li>
      </ul>
   </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import Materialize from '../../libs/materialize/materialize.min.js'
import { entryEditorApi, type EntryLink, type EntryLinks } from '../../js/entry-editor-api.ts'
import { linkedEntryLocation } from '../../js/linked-entry-location.ts'

const props = defineProps<{ dictId: string; entryId: number; canDelete?: boolean }>()
const links = ref<EntryLinks>({ in: [], out: [] })
const removing = reactive(new Set<number>())
let revision = 0
let mounted = true

const sections = computed(() => [
   { id: 'outlinks', heading: 'Outgoing links', arrow: '→', links: links.value.out, incoming: false },
   { id: 'inlinks', heading: 'Incoming links', arrow: '←', links: links.value.in, incoming: true }
].filter(section => section.links.length).map(section => ({
   ...section,
   links: section.links.map(link => {
      const prefix = section.incoming ? 'source' : 'target'
      const dict = link[`${prefix}_dict`]
      return {
         link,
         peer: [dict, section.incoming && link.source_hw, link[`${prefix}_el`], link[`${prefix}_id`]].filter(Boolean).join(' : '),
         label: section.incoming ? link.target_id : link.source_preview || link.source_id,
         to: dict === 'BABELNET' ? null : linkedEntryLocation(link, prefix)
      }
   })
})))

watch([() => props.dictId, () => props.entryId], () => {
   links.value = { in: [], out: [] }
   void load()
}, { immediate: true })
onBeforeUnmount(() => {
   revision++
   mounted = false
})
defineExpose({ load })

async function load() {
   const request = ++revision
   try {
      const result = await entryEditorApi.links(props.dictId, props.entryId)
      if (request === revision) links.value = result.links
   } catch {
      if (request === revision) Materialize.toast({ html: 'Could not load entry links.' })
   }
}

async function remove(link: EntryLink) {
   if (removing.has(link.link_id) || !window.confirm('Really delete link?')) return
   const { dictId, entryId } = props
   removing.add(link.link_id)
   try {
      const { success } = await entryEditorApi.removeLink(link.source_dict, link.link_id)
      if (!success) throw new Error('Link deletion rejected')
      if (mounted && props.dictId === dictId && props.entryId === entryId) await load()
   } catch {
      Materialize.toast({ html: 'Failed to delete link.' })
   } finally {
      removing.delete(link.link_id)
   }
}
</script>
