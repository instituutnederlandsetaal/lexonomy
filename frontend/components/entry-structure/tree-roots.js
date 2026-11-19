export function treeRoots(xema) {
   const elements = xema?.elements || {}
   const roots = new Set(Object.keys(elements))
   for (const element of Object.values(elements)) {
      for (const child of element.children || []) roots.delete(child.name)
   }
   if (!roots.size) {
      const root = elements[xema?.root] ? xema.root : Object.keys(elements)[0]
      if (root) roots.add(root)
   }
   return Array.from(roots, id => ({...elements[id], id}))
}
