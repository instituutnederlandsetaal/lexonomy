import { toRaw } from 'vue'
import type { Element } from 'xml-js'
import type { WorkspaceConfig } from '../../js/dictionary-workspace.ts'
import { maximumChildCount, xemaElementId, xmlElementName, type Xema, type XemaFilling } from '../../js/xema.ts'
import { readFormattingFields, type FormattingFields } from '../../js/xemplate.ts'

export type EditorChild = { name: string; isAttribute?: boolean }
export type ElementDisplay = Omit<FormattingFields, 'shown' | 'displayType'> & {
   shown: boolean
   displayType: 'inline' | 'popup'
   editorLabel: string
}

export function elementId(xema: Xema, node: Element, parentId?: string) {
   if (node.type !== 'element' || !node.name) return undefined
   const name = node.name === 'lxnm:subentryParent' ? node.attributes?.doctype : node.name
   return typeof name === 'string' ? xemaElementId(xema, name, parentId) : undefined
}

export function childrenFor(xema: Xema, id: string, content: Element): EditorChild[] {
   const schema = xema.elements[id]
   const defined = new Set(schema?.children?.map(child => child.name))
   for (const node of content.elements ?? []) {
      const name = elementId(xema, node, id)
      if (name) defined.add(name)
   }
   return [
      ...Object.keys(schema?.attributes ?? {}).map(name => ({ name, isAttribute: true })),
      ...Array.from(defined, name => ({ name }))
   ]
}

export function valueDefinition(xema: Xema, id: string, parentId?: string, isAttribute = false) {
   return isAttribute && parentId ? xema.elements[parentId]?.attributes?.[id] : xema.elements[id]
}

export function valueInputKind(xema: Xema, node: Element, id: string, parentId?: string, isAttribute = false): XemaFilling {
   const filling = valueDefinition(xema, id, parentId, isAttribute)?.filling ?? 'txt'
   if (filling === 'txt' && !isAttribute && node.elements?.length &&
       (node.elements.length > 1 || node.elements.some(child => child.type !== 'text'))) return 'inl'
   return filling
}

export function emptyElement(xema: Xema, id: string): Element {
   return { type: 'element', name: xmlElementName(xema, id) }
}

export function elementDisplay(xemplate: WorkspaceConfig['xemplate'], xema: Xema, id: string, parentId?: string, isAttribute = false): ElementDisplay {
   const definitionId = isAttribute ? parentId ?? '' : id
   const settings = readFormattingFields(xemplate, definitionId, xmlElementName(xema, definitionId), isAttribute ? id : undefined)
   const shown = !('shown' in settings) || (Boolean(settings.shown) && settings.shown !== 'false')
   const optionality = xema.elements[definitionId]?.attributes?.[id]?.optionality
   const editorLabel = isAttribute ? id + (optionality === 'obligatory' ? '*' : '') : xmlElementName(xema, id)
   return { ...settings, shown, editorLabel, displayType: settings.displayType === 'popup' ? 'popup' : 'inline' }
}

export type ParentCandidate = { node: Element; elementName: string; parentElementName?: string }
export type ParentChange = { node: Element; destination: Element }
export type DraftScope = Omit<ParentCandidate, 'node'>

export function containsNode(root: Element, node: Element): boolean {
   return toRaw(root) === toRaw(node) || Boolean(root.elements?.some(child => containsNode(child, node)))
}

export function canReceiveNode(xema: Xema, parentId: string, parent: Element, childId: string, node: Element) {
   const rule = xema.elements[parentId]?.children?.find(child => child.name === childId)
   if (!rule || containsNode(node, parent) || parent.elements?.some(child => toRaw(child) === toRaw(node))) return false
   const max = maximumChildCount(rule.max)
   return !Number.isFinite(max) || (parent.elements?.filter(child => elementId(xema, child, parentId) === childId).length ?? 0) < max
}

export function findMoveParents(config: Pick<WorkspaceConfig, 'xema' | 'xemplate' | 'subbing'>, draft: Element,
   node: Element, elementName: string, scope?: DraftScope): ParentCandidate[] {
   if (!containsNode(draft, node)) return []
   const { xema, xemplate, subbing } = config
   const candidates: ParentCandidate[] = []

   function visit(parent: Element, id: string, parentId?: string, scopeRoot = false) {
      if (parent.name === 'lxnm:subentryParent' || toRaw(parent) === toRaw(node)) return
      if (canReceiveNode(xema, id, parent, elementName, node)) {
         candidates.push({ node: parent, elementName: id, parentElementName: parentId })
      }
      // Inline fields keep rendering their children even when their own controls are hidden or read-only.
      // Popup children belong to the dialog draft, and markup children belong to the text input.
      if (valueInputKind(xema, parent, id) === 'inl' ||
          (!scopeRoot && ((subbing[id] && id !== xema.root) || elementDisplay(xemplate, xema, id).displayType === 'popup'))) return
      for (const child of parent.elements ?? []) {
         const childId = elementId(xema, child, id)
         if (childId) visit(child, childId, id)
      }
   }

   if (scope) visit(draft, scope.elementName, scope.parentElementName, true)
   else for (const child of draft.elements ?? []) {
      const id = elementId(xema, child)
      if (id) visit(child, id)
   }
   return candidates
}

export function findDraftHeadword(xema: Xema, draft: Element, headword: string, scope?: DraftScope): string | undefined {
   function find(node: Element, parentId?: string, id = elementId(xema, node, parentId)): string | undefined {
      if (id === headword) return String(node.elements?.find(child => child.type === 'text')?.text ?? '')
      for (const child of node.elements ?? []) {
         const value = find(child, id)
         if (value !== undefined) return value
      }
      return undefined
   }
   return find(draft, scope?.parentElementName, scope?.elementName)
}

export function moveNode(root: Element, { node, destination }: ParentChange): Element | null {
   if (containsNode(node, destination) || !containsNode(root, node) || !containsNode(root, destination)) return null
   const rewrite = (parent: Element): Element => {
      const nodes = parent.elements ?? []
      const target = toRaw(parent) === toRaw(destination)
      if (target && nodes.some(child => toRaw(child) === toRaw(node))) return parent
      const children = nodes.filter(child => toRaw(child) !== toRaw(node)).map(rewrite)
      if (target) children.push(toRaw(node))
      return children.length !== nodes.length || children.some((child, index) => child !== nodes[index])
         ? { ...parent, elements: children } : parent
   }
   return rewrite(root)
}

function escapeXml(value: string | number | boolean): string {
   return String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('\r', '&#13;')
}

export function serializeDraft(node: Element): string {
   switch (node.type) {
      case 'element': {
         const attributes = Object.entries(node.attributes ?? {}).map(([name, value]) => value == null ? '' :
            ` ${name}="${escapeXml(value).replaceAll('"', '&quot;').replaceAll('\n', '&#10;').replaceAll('\t', '&#9;')}"`).join('')
         return node.elements?.length
            ? `<${node.name}${attributes}>${node.elements.map(serializeDraft).join('')}</${node.name}>`
            : `<${node.name}${attributes}/>`
      }
      case 'text':
         return escapeXml(node.text ?? '')
      case 'cdata':
         return `<![CDATA[${(node.cdata ?? '').replaceAll(']]>', ']]]]><![CDATA[>')}]]>`
      case 'comment':
         return `<!--${node.comment ?? ''}-->`
      case 'instruction':
         return `<?${node.name}${node.instruction ? ' ' + node.instruction : ''}?>`
      case 'doctype':
         return `<!DOCTYPE ${node.doctype}>`
      default:
         return node.elements?.map(serializeDraft).join('') ?? ''
   }
}

export function updateValueChildren(content: Element, next: Element[], updateAll: boolean): Element {
   if (updateAll || !content.elements?.length) return { ...content, elements: next }
   const elements = [...content.elements]
   const index = elements.findIndex(node => node.type === 'text')
   elements.splice(index < 0 ? 0 : index, index < 0 ? 0 : 1, ...next)
   return { ...content, elements }
}
