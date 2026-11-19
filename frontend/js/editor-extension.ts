import type { DeepReadonly } from 'vue'
import { createInitialElement } from '../widgets/xematron.ts'
import type { DictionarySettings } from './dictionary-config-api.ts'
import { entryEditorApi, type EntryDraft, type LoadedEntry, type RelatedEntry } from './entry-editor-api.ts'
import { xmlElementName, type Xema } from './xema.ts'

type SubentryDefinitions = DictionarySettings['subbing']

type EntryServices = {
   readEntry(id: number): Promise<LoadedEntry | null>
   subentries: {
      readonly definitions: DeepReadonly<SubentryDefinitions>
      search(lemma: string, schemaId: string): Promise<RelatedEntry[]>
      referenceXml(entry: RelatedEntry): string
   }
   createInitialElement(schemaId: string): string
}

export type EditorExtensionEntry = Pick<EntryDraft, 'id' | 'content' | 'subentries' | 'parententries'> & {
   schemaId: string
   doctype: string
   revisionId?: number
}

export type EditorExtensionEntryContext = EntryServices & {
   readonly dictionaryId: string
   readonly schema: DeepReadonly<Xema>
   readonly entry: DeepReadonly<EditorExtensionEntry>
   readonly readOnly: boolean
   readonly signal: AbortSignal
   readonly headwordElement?: string
}

export type EditorExtensionContext = EditorExtensionEntryContext & {
   readonly element: HTMLDivElement
   markDirty(): void
   openEntry(entry: Pick<RelatedEntry, 'id' | 'doctype'>): void
}

export type EditorExtensionInstance = {
   harvest(): string | Promise<string>
   dispose?(): void
}

export type EditorExtension = {
   initialXml?(context: EditorExtensionEntryContext): string
   mount(context: EditorExtensionContext): EditorExtensionInstance
}

export function compileEditorExtension(source: string): () => unknown {
   return new Function(`"use strict"; return (\n${source}\n)`) as () => unknown
}

export function loadEditorExtension(source: string): EditorExtension {
   const extension = compileEditorExtension(source)()
   if (!extension || typeof extension !== 'object' || !('mount' in extension) || typeof extension.mount !== 'function') {
      throw new Error('The editor extension must provide mount(context).')
   }
   if ('initialXml' in extension && extension.initialXml !== undefined && typeof extension.initialXml !== 'function') {
      throw new Error('The initialXml property must be a function.')
   }
   return extension as EditorExtension
}

export function subentryReferenceXml({ id, doctype, title }: RelatedEntry): string {
   const attribute = (value: string | number) => String(value)
      .replaceAll('&', '&amp;').replaceAll('"', '&quot;').replaceAll("'", '&apos;')
      .replaceAll('<', '&lt;').replaceAll('>', '&gt;')
      .replaceAll('\r', '&#13;').replaceAll('\n', '&#10;').replaceAll('\t', '&#9;')
   return `<lxnm:subentryParent xmlns:lxnm="http://www.lexonomy.eu/" id="${attribute(id)}" doctype="${attribute(doctype)}" title="${attribute(title)}"/>`
}

export function createEditorExtensionServices(
   dictionaryId: string, schema: Xema, definitions: SubentryDefinitions, signal: AbortSignal
): EntryServices {
   return {
      async readEntry(id) {
         const result = await entryEditorApi.read(dictionaryId, id, signal)
         return result.success ? result : null
      },
      subentries: {
         definitions,
         async search(lemma, schemaId) {
            signal.throwIfAborted()
            const term = lemma.trim()
            if (!term) return []
            if (!Object.hasOwn(schema.elements, schemaId)) throw new Error(`Unknown schema element: ${schemaId}`)
            const result = await entryEditorApi.subentries(dictionaryId, term, xmlElementName(schema, schemaId), schemaId, signal)
            if (!result.success) throw new Error('Subentry search rejected.')
            return result.entries
         },
         referenceXml: subentryReferenceXml
      },
      createInitialElement(schemaId) {
         if (!Object.hasOwn(schema.elements, schemaId)) throw new Error(`Unknown schema element: ${schemaId}`)
         return createInitialElement(schema, schemaId)
      }
   }
}
