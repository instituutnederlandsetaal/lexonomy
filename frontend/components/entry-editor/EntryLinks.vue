<template>
   <span v-for="section in sections" :id="section.id" :key="section.id">
      <h2>{{ section.heading }}</h2>
      <ul v-for="item in section.links" :key="item.link.link_id">
         {{ item.label }} {{ section.arrow }}
         <RouterLink v-if="item.to" :to="item.to">{{ item.peer }}</RouterLink>
         <template v-else>{{ item.peer }}</template>
         {{ item.link.confidence ? `(${item.link.confidence})` : '' }}
         <button v-if="canDelete && !section.incoming" class="linkdelete" type="button"
                 @click="remove(item.link)">×delete</button>
      </ul>
   </span>
</template>

<script>
import Materialize from '../../libs/materialize/materialize.min.js'
import { api } from '../../js/api.ts'
import { linkedEntryLocation } from '../../js/linked-entry-location.ts'

export default {
   props: { dictId: String, entryId: [String, Number], canDelete: Boolean },
   data() {
      return { links: { in: [], out: [] }, request: 0 }
   },
   computed: {
      sections() {
         return [
            { id: 'outlinks', heading: 'Outgoing links', arrow: '→', links: this.links.out },
            { id: 'inlinks', heading: 'Incoming links', arrow: '←', links: this.links.in, incoming: true },
         ].filter(section => section.links.length).map(section => ({
            ...section,
            links: section.links.map(link => {
               const { incoming } = section
               const prefix = incoming ? 'source' : 'target'
               const dict = link[prefix + '_dict']
               const el = link[prefix + '_el']
               const id = link[prefix + '_id']
               const hw = incoming && link.source_hw
               return {
                  link, peer: [dict, hw, el, id].filter(Boolean).join(' : '),
                  label: incoming ? link.target_id : link.source_preview || link.source_id,
                  to: dict === 'BABELNET' ? null : linkedEntryLocation(link, prefix),
               }
            }),
         }))
      }
   },
   mounted() {
      this.load()
   },
   beforeUnmount() {
      this.request++
   },
   methods: {
      async load() {
         const request = ++this.request
         const result = await api.get(`${encodeURIComponent(this.dictId)}/entrylinks.json`, { id: this.entryId }).catch(() => null)
         if (result && request === this.request) this.links = result.links
      },
      async remove(link) {
         if (!window.confirm('Really delete link?')) return
         const result = await api.get(`${encodeURIComponent(link.source_dict)}/links/delete/${link.link_id}`).catch(() => null)
         if (result?.success) this.load()
         else Materialize.toast({ html: 'Failed to delete link.' })
      }
   }
}
</script>
