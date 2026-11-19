import DOMPurify from 'dompurify'

DOMPurify.addHook('afterSanitizeAttributes', node => {
   if (!node.hasAttribute('target')) return
   if (node instanceof HTMLAnchorElement && node.target === '_blank') node.relList.add('noopener')
   else node.removeAttribute('target')
})

export function sanitizeHtml(html: string | null | undefined) {
   return DOMPurify.sanitize(html ?? '', { ADD_ATTR: ['target'], FORBID_TAGS: ['style'] })
}
