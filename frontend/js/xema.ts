// Stored schemas can omit fields that are irrelevant to an element's filling.
export type XemaValue = { value: string; caption: string }
export type XemaFilling = 'inl' | 'txt' | 'chd' | 'emp' | 'lst' | 'med'

export type XemaChild = { name: string; min: number | string; max: number | string | null }

export type XemaAttribute = {
   optionality: 'optional' | 'obligatory'
   filling: 'txt' | 'lst'
   values?: XemaValue[] | null
}

export type XemaElement = {
   elementName?: string | null
   filling?: XemaFilling
   values?: XemaValue[]
   children?: XemaChild[]
   attributes?: Record<string, XemaAttribute>
}

export type Xema = {
   root: string
   elements: Record<string, XemaElement>
   _dtd?: string
   _newXml?: string
   _xonomyDocSpec?: string
   newXml?: string
}

export function maximumChildCount(max: XemaChild['max']) {
   const count = Number(max)
   // Shipped legacy schemas encode an unbounded maximum as a string "0".
   if (max == null || (typeof max === 'string' && count === 0)) return Infinity
   return Number.isSafeInteger(count) && count >= 0 ? count : Infinity
}

export function xmlElementName(xema: Xema, id: string) {
   return xema.elements[id]?.elementName || id
}

export function xemaChildId(xema: Xema, parentId: string | undefined, name: string) {
   return parentId ? xema.elements[parentId]?.children?.find(child => xmlElementName(xema, child.name) === name)?.name : undefined
}

export function xemaElementId(xema: Xema, name: string, parentId?: string) {
   const child = xemaChildId(xema, parentId, name)
   if (child) return child
   if (xmlElementName(xema, xema.root) === name) return xema.root
   return Object.keys(xema.elements).find(id => xmlElementName(xema, id) === name) ?? name
}
