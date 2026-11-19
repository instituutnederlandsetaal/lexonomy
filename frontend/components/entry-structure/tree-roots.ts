import { type Xema } from '../../js/xema.ts'

export function treeRoots(xema?: Xema | null) {
   if (!xema) return []
   const { elements, root } = xema
   const ids = Object.keys(elements)
   const children = new Set(Object.values(elements).flatMap(el => (el.children ?? []).map(child => child.name)))
   const roots: string[] = []
   const visited = new Set<string>()

   function visit(id: string) {
      if (visited.has(id) || !Object.hasOwn(elements, id)) return
      visited.add(id)
      for (const child of elements[id].children ?? []) visit(child.name)
   }

   function addRoot(id: string) {
      if (visited.has(id) || !Object.hasOwn(elements, id)) return
      roots.push(id)
      visit(id)
   }

   addRoot(root)
   for (const id of ids) if (!children.has(id)) addRoot(id)
   for (const id of ids) addRoot(id)
   return roots
}
