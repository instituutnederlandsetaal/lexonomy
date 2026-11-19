import { inject, provide, toRaw, type ComputedRef, type InjectionKey, type Ref } from 'vue'
import type { Element } from 'xml-js'
import { findDraftHeadword, findMoveParents, moveNode, type DraftScope, type ParentCandidate } from './editor-schema.ts'

import type { WorkspaceConfig } from '../../js/dictionary-workspace.ts'
import type { MyDictionary } from '../../js/my-dictionaries.ts'

export type EditorContext = {
   readonly config: WorkspaceConfig
   readonly dictId: string
   readonly userDicts: readonly MyDictionary[]
}
export const editorContextKey: InjectionKey<EditorContext> = Symbol('Editor context')
const editorDraftKey: InjectionKey<{
   moveParents: (node: Element, elementName: string) => ParentCandidate[]
   move: (node: Element, elementName: string, destination: Element) => void
   headword: () => string
}> = Symbol('Editor draft')
export const requiredFieldsKey: InjectionKey<Set<() => string | undefined>> = Symbol('Required fields')
export const schemaAncestorsKey: InjectionKey<ComputedRef<string[]>> = Symbol('Schema ancestors')
export const notifyLinksChangedKey: InjectionKey<() => void> = Symbol('Link change callback')
export const editorLockedKey: InjectionKey<Readonly<Ref<boolean>>> = Symbol('Editor mutation in progress')
export const setPopupDirtyKey: InjectionKey<(popup: symbol, dirty: boolean) => void> = Symbol('Popup draft callback')

export function useEditorDraft() {
   return inject(editorDraftKey)!
}

export function provideEditorDraft(read: () => Element | null, update: (content: Element) => void, scope?: () => DraftScope) {
   const editor = inject(editorContextKey)!
   const outer = inject(editorDraftKey, null)

   function moveParents(node: Element, elementName: string) {
      const draft = read()
      return draft ? findMoveParents(editor.config, draft, node, elementName, scope?.()) : []
   }

   provide(editorDraftKey, {
      moveParents,
      move(node, elementName, destination) {
         const draft = read()
         if (!draft || !moveParents(node, elementName).some(candidate => toRaw(candidate.node) === toRaw(destination))) return
         const moved = moveNode(draft, { node, destination })
         if (moved) update(moved)
      },
      headword() {
         const draft = read()
         const { xema, titling } = editor.config
         const id = titling.headword || xema.elements[xema.root]?.children?.[0]?.name
         return (draft && id ? findDraftHeadword(xema, draft, id, scope?.()) : undefined) ?? outer?.headword() ?? ''
      }
   })
}
