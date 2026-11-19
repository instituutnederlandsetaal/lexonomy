import type {
   Xonomy, XonomyDocSpecExternal, XonomyElementDefinitionExternal,
   XonomyElementInstance, XonomyMenuActionExternal
} from '@elexis-eu/xonomy'
import { maximumChildCount, xemaChildId, xmlElementName, type Xema, type XemaChild } from '../js/xema.ts'

function minimumCount(child: XemaChild) {
   const minimum = Number(child.min)
   return Number.isSafeInteger(minimum) && minimum > 0 ? minimum : 0
}

function requiredAttributes(xema: Xema, id: string) {
   return Object.entries(xema.elements[id]?.attributes ?? {})
      .filter(([, attribute]) => attribute.optionality === 'obligatory')
      .map(([name]) => ` ${name}=''`).join('')
}

export function createInitialElement(xema: Xema, id: string): string {
   const ancestors = new Set<string>()

   function build(elementId: string): string {
      const name = xmlElementName(xema, elementId)
      const element = xema.elements[elementId]
      const attributes = requiredAttributes(xema, elementId)
      // A recursive schema can require endless descendants. Leave a finite starter document.
      if (ancestors.has(elementId) || ancestors.size >= 10 || element?.filling !== 'chd') {
         return `<${name}${attributes}></${name}>`
      }
      ancestors.add(elementId)
      const children = (element.children ?? []).map(child => {
         const count = minimumCount(child)
         return count ? build(child.name).repeat(count) : ''
      }).join('')
      ancestors.delete(elementId)
      return `<${name}${attributes}>${children}</${name}>`
   }

   return build(id)
}

export function createInitialXml(xema: Xema) {
   return xema._newXml || xema.newXml || createInitialElement(xema, xema.root)
}

function indexSchema(xema: Xema) {
   const idsByTag = new Map<string, string>()
   const orderedChildren = new Map<string, Map<string, number>>()
   const parentsByChild = new Map<string, string[]>()
   const visited = new Set<string>()
   const pending = [xema.root]

   for (const id of pending) {
      if (visited.has(id)) continue
      visited.add(id)
      const name = xmlElementName(xema, id)
      if (!idsByTag.has(name)) idsByTag.set(name, id)
      for (const child of xema.elements[id]?.children ?? []) pending.push(child.name)
   }
   for (const [id, element] of Object.entries(xema.elements)) {
      if (element.filling !== 'chd') continue
      const positions = new Map<string, number>()
      for (const [offset, child] of (element.children ?? []).entries()) {
         if (positions.has(child.name)) continue
         positions.set(child.name, offset)
         const parents = parentsByChild.get(child.name) ?? []
         parents.push(id)
         parentsByChild.set(child.name, parents)
      }
      orderedChildren.set(id, positions)
   }
   return { idsByTag, orderedChildren, parentsByChild }
}

type SchemaIndex = ReturnType<typeof indexSchema>

function validateElement(xonomy: Xonomy, xema: Xema, schema: SchemaIndex, node: XonomyElementInstance) {
   if (node.elementName === 'lxnm:subentryParent') return
   const warn = (htmlID: string | undefined, text: string) => {
      if (htmlID) xonomy.warnings.push({ htmlID, text })
   }
   const definition = xema.elements[node.id]
   const parent = node.parent()
   const label = `<${node.elementName}>`
   if (!parent && node.id !== xema.root) {
      warn(node.htmlID, `The top element should be <${xmlElementName(xema, xema.root)}>.`)
      return
   }
   if (!definition) {
      warn(node.htmlID, `No ${label} element should exist here.`)
      return
   }

   for (const [name, attribute] of Object.entries(definition.attributes ?? {})) {
      if (attribute.optionality === 'obligatory' && !node.hasAttribute(name)) {
         warn(node.htmlID, `The ${label} element is missing the @${name} attribute.`)
      }
   }
   for (const { name, value, htmlID } of node.attributes) {
      if (name.startsWith('lxnm:') || xonomy.isNamespaceDeclaration(name)) continue
      const attribute = definition.attributes?.[name]
      if (!attribute) warn(htmlID, `The ${label} element should not have an attribute called @${name}.`)
      else if (!value) warn(htmlID, `The @${name} attribute should not be empty.`)
      else if (attribute.filling === 'lst' && !attribute.values?.some(option => option.value === value)) {
         warn(htmlID, `The @${name} attribute should not have the value "${xonomy.xmlEscape(value)}".`)
      }
   }

   const filling = definition.filling
   if (filling === 'emp' && node.children.length) warn(node.htmlID, `The ${label} element should be empty.`)
   if (filling === 'txt' || filling === 'inl' || filling === 'lst') {
      const value = node.getText()
      if (!value) warn(node.htmlID, `The ${label} element should have some text.`)
      else if (filling === 'lst' && !definition.values?.some(option => option.value === value)) {
         warn(node.htmlID, `The ${label} element should not have the value "${xonomy.xmlEscape(value)}".`)
      }
   }
   if (filling === 'chd' && node.children.some(child => child.type === 'text' && child.value.trim())) {
      warn(node.htmlID, `The ${label} element should not have any text.`)
   }

   const allowedChildren = definition.children ?? []
   const childElements = node.children.flatMap(child => {
      if (child.type !== 'element') return []
      if (child.elementName !== 'lxnm:subentryParent') {
         return [{ child, id: child.id, name: child.elementName, htmlID: child.htmlID }]
      }
      const name = child.getAttributeValue('doctype')
      const id = name && xemaChildId(xema, node.id, name)
      return id ? [{ child, id, name, htmlID: node.htmlID }] : []
   })
   if (filling === 'chd' || filling === 'inl') {
      for (const child of allowedChildren) {
         const children = childElements.filter(item => item.id === child.name)
         const minimum = minimumCount(child)
         const maximum = maximumChildCount(child.max)
         if (children.length >= minimum && children.length <= maximum) continue
         const limit = minimum > 0 && maximum !== Infinity ? `between ${minimum} and ${maximum}`
            : minimum > 0 ? `at least ${minimum}` : `at most ${maximum}`
         const warning = `The ${label} element should have ${limit} <${xmlElementName(xema, child.name)}> child elements.`
         for (const item of children.length ? children : [node]) warn(item.htmlID, warning)
      }
   }

   const positions = schema.orderedChildren.get(node.id)
   let furthest = -1
   for (const { child, id, name, htmlID } of childElements) {
      if (!allowedChildren.some(item => item.name === id)) {
         warn(htmlID, `The ${label} element should not have a child called <${name}>.`)
         continue
      }
      const offset = positions?.get(id)
      if (offset != null) {
         if (offset < furthest) warn(htmlID, `The <${name}> element is out of order.`)
         furthest = Math.max(furthest, offset)
      }
      validateElement(xonomy, xema, schema, child)
   }
}

export function createDocSpec(xonomy: Xonomy, xema: Xema, stringAsker?: string): XonomyDocSpecExternal {
   const schema = indexSchema(xema)
   const asker = stringAsker === 'askString' ? xonomy.askString.bind(xonomy) : xonomy.askLongString.bind(xonomy)
   const picklist = xonomy.askPicklist.bind(xonomy)
   const elements: Record<string, XonomyElementDefinitionExternal> = Object.create(null)
   const initialXml = new Map<string, string>()
   function starter(id: string) {
      const existing = initialXml.get(id)
      if (existing !== undefined) return existing
      const xml = createInitialElement(xema, id)
      initialXml.set(id, xml)
      return xml
   }

   for (const [id, element] of Object.entries(xema.elements)) {
      const name = xmlElementName(xema, id)
      const hasText = ['inl', 'txt', 'lst', 'med'].includes(element.filling ?? '')
      const parents = schema.parentsByChild.get(id) ?? []
      const children = element.children ?? []
      const attributes: NonNullable<XonomyElementDefinitionExternal['attributes']> = Object.create(null)
      const attributeMenu: XonomyMenuActionExternal[] = []
      const shortcut = (key: number): Pick<XonomyMenuActionExternal, 'keyTrigger'> => ({
         keyTrigger: event => Boolean((event.ctrlKey || event.metaKey) && event.shiftKey && event.which === key)
      })
      const remove = { ...shortcut(88), keyCaption: 'Ctrl + Shift + X' }

      const inInlineParent = (node: XonomyElementInstance) => xema.elements[node.parent()?.id ?? '']?.filling === 'inl'
      const canEditSibling = (node: XonomyElementInstance) => Boolean(node.parent() && !inInlineParent(node))
      const action = (caption: string, run: (htmlID: string) => void,
         available: (node: XonomyElementInstance) => boolean = canEditSibling,
         keyboard: Pick<XonomyMenuActionExternal, 'keyTrigger' | 'keyCaption'> = {}): XonomyMenuActionExternal => ({
         caption, action: run, hideIf: node => node.type !== 'element' || !available(node), ...keyboard
      })
      const menu: XonomyMenuActionExternal[] = [{
         caption: 'This element',
         expanded: true,
         menu: [
            action(`Unwrap <${name}>`, xonomy.unwrap.bind(xonomy), inInlineParent, remove),
            action(`Remove <${name}>`, htmlID => xonomy.deleteElement(htmlID, undefined), canEditSibling, remove),
            action(`Duplicate <${name}>`, xonomy.duplicateElement.bind(xonomy), canEditSibling,
               { ...shortcut(68), keyCaption: 'Ctrl + Shift + D' }),
            action(`Move <${name}> up`, xonomy.moveElementUp.bind(xonomy),
               node => canEditSibling(node) && Boolean(node.htmlID && xonomy.canMoveElementUp(node.htmlID)),
               { ...shortcut(38), keyCaption: 'Ctrl + Shift + Up' }),
            action(`Move <${name}> down`, xonomy.moveElementDown.bind(xonomy),
               node => canEditSibling(node) && Boolean(node.htmlID && xonomy.canMoveElementDown(node.htmlID)),
               { ...shortcut(40), keyCaption: 'Ctrl + Shift + Down' }),
            action(`Merge <${name}> with previous`, htmlID => xonomy.mergeWithPrevious(htmlID, undefined),
               node => canEditSibling(node) && node.getPrecedingSibling()?.id === id,
               { keyTrigger: event => Boolean(event.altKey && event.shiftKey && event.which === 38), keyCaption: 'Alt + Shift + Up' }),
            action(`Merge <${name}> with next`, htmlID => xonomy.mergeWithNext(htmlID, undefined),
               node => canEditSibling(node) && node.getFollowingSibling()?.id === id,
               { keyTrigger: event => Boolean(event.altKey && event.shiftKey && event.which === 40), keyCaption: 'Alt + Shift + Down' })
         ]
      }]

      for (const [attribute, definition] of Object.entries(element.attributes ?? {})) {
         attributes[attribute] = {
            asker: definition.filling === 'lst' ? picklist : asker,
            askerParameter: definition.values ?? [],
            menu: [{ caption: `Remove @${attribute}`, action: xonomy.deleteAttribute.bind(xonomy), ...remove }]
         }
         attributeMenu.push({
            caption: `Add @${attribute}`, action: xonomy.newAttribute.bind(xonomy),
            actionParameter: { name: attribute, value: '' },
            hideIf: node => node.type !== 'element' || node.hasAttribute(attribute)
         })
      }
      if (attributeMenu.length) menu.push({ caption: 'Attributes', menu: attributeMenu })
      if (element.filling === 'chd' && children.length) {
         menu.push({ caption: 'Child elements', menu: children.map(child =>
            action(`Add <${xmlElementName(xema, child.name)}>`,
               htmlID => xonomy.newElementChild(htmlID, starter(child.name)), () => true))
         })
      }

      function siblings(parentId: string | undefined, before: boolean) {
         const positions = schema.orderedChildren.get(parentId ?? '')
         const offset = positions?.get(id)
         if (!positions || offset == null) return []
         return Array.from(positions).filter(([, position]) => before ? position < offset : position > offset)
            .map(([sibling]) => sibling)
      }

      function addSiblings(before: boolean) {
         const add = before ? xonomy.newElementBefore.bind(xonomy) : xonomy.newElementAfter.bind(xonomy)
         const candidates = new Set(parents.flatMap(parent => siblings(parent, before)))
         return [
            ...Array.from(candidates, candidate => action(`Add <${xmlElementName(xema, candidate)}>`,
               htmlID => add(htmlID, starter(candidate)), node => {
                  const parent = node.parent()
                  const neighbour = before ? node.getPrecedingSibling() : node.getFollowingSibling()
                  return Boolean(parent && canEditSibling(node) && neighbour?.id !== id &&
                     !parent.hasChildElement(candidate) && siblings(parent.id, before).includes(candidate))
               })),
            action(`Add another <${name}> ${before ? 'before' : 'after'}`, htmlID => add(htmlID, starter(id)))
         ]
      }

      menu.push({ caption: 'Sibling elements', menu: [
         ...addSiblings(true), ...addSiblings(false),
         action(`Remove all <${name}> siblings`, htmlID => xonomy.deleteEponymousSiblings(htmlID, undefined),
            node => canEditSibling(node) && (node.parent()?.getChildElements(id).length ?? 0) >= 2,
            { ...shortcut(90), keyCaption: 'Ctrl + Shift + Z' })
      ] })

      elements[id] = {
         elementName: name,
         attributes, menu, hasText, oneliner: hasText,
         asker: element.filling === 'lst' ? picklist : asker,
         askerParameter: element.values ?? [],
         collapsible: element.filling === 'chd',
         collapsed: node => Boolean(node.parent()),
         canDropTo: parents,
         mustBeAfter: node => siblings(node.parent()?.id, true),
         mustBeBefore: node => siblings(node.parent()?.id, false),
         inlineMenu: element.filling === 'inl' ? children.map(child => {
            const tag = xmlElementName(xema, child.name)
            return {
               caption: `Wrap with <${tag}>`, action: xonomy.wrap.bind(xonomy),
               actionParameter: { template: `<${tag}${requiredAttributes(xema, child.name)}>$</${tag}>`, placeholder: '$' }
            }
         }) : []
      }
   }

   return {
      elements,
      getElementId(name, parent) {
         return xemaChildId(xema, parent, name) ?? schema.idsByTag.get(name) ?? name
      },
      unknownElement: name => name.startsWith('lxnm:') ? { isReadOnly: true, isInvisible: true } : {
         oneliner: node => !node.hasElements(),
         menu: [{ caption: 'Delete', action: xonomy.deleteElement.bind(xonomy), hideIf: node => !node.parent() }]
      },
      unknownAttribute: (name, attribute = name) => attribute.startsWith('lxnm:')
         ? { isReadOnly: true, isInvisible: true }
         : { menu: [{ caption: 'Delete', action: xonomy.deleteAttribute.bind(xonomy) }] },
      validate: node => validateElement(xonomy, xema, schema, node)
   }
}
