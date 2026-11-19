import type { CSSProperties } from 'vue'

export type FormattingFields = {
   shown?: boolean | 'true' | 'false'
   layout?: 'inline' | 'block'
   label?: string
   order?: 'before' | 'after'
   captioning?: string
   interactivity?: string | boolean
   innerPunc?: string
   textsize?: string
   weight?: CSSProperties['fontWeight']
   slant?: CSSProperties['fontStyle']
   colour?: string
   outerPunc?: string
   background?: string
   border?: string
   gutter?: string
   separation?: string
   displayType?: 'inline' | 'popup' | ''
   editorInputType?: 'number' | 'text' | 'textarea' | ''
   readOnly?: boolean
   hideElementName?: boolean
   enableCopying?: boolean
   enableParentChange?: boolean
   enablePositionChange?: boolean
   attributes?: Record<string, FormattingFields>
}

export type Xemplate = Record<string, FormattingFields | string | undefined> & { _css?: string; _xsl?: string }

function formattingFields(value: Xemplate[string]): FormattingFields {
   return value && typeof value === 'object' && !Array.isArray(value) ? value : {}
}

export function readFormattingFields(
   template: Xemplate, definitionId: string, xmlTag: string, attributeName?: string
) {
   if (attributeName === undefined) return formattingFields(template[definitionId] ?? template[xmlTag])
   const configured = formattingFields(template[definitionId]).attributes
   const legacy = formattingFields(template[xmlTag]).attributes
   return formattingFields(configured?.[attributeName] ?? legacy?.[attributeName])
}

export function previewFormatting(
   template: Xemplate, definitionId: string, xmlTag: string, attributeName?: string
) {
   const fields = readFormattingFields(template, definitionId, xmlTag, attributeName)
   const element = attributeName === undefined
   return {
      ...fields,
      shown: fields.shown === undefined ? element : fields.shown === true || fields.shown === 'true',
      layout: fields.layout ?? (element ? 'block' : 'inline'),
      order: fields.order ?? 'after',
      gutter: fields.gutter === 'handing' ? 'hanging' : fields.gutter
   }
}
