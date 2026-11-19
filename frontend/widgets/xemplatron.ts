import linkIcon from '../assets/furniture/link.png'
import './xemplatron.css'
import type { WorkspaceConfig } from '../js/dictionary-workspace.ts'
import type { EntryRendering } from '../js/entry-editor-api.ts'
import { parseXml } from '../js/xml.ts'
import { xemaElementId, xmlElementName, type Xema } from '../js/xema.ts'
import { previewFormatting, type FormattingFields, type Xemplate } from '../js/xemplate.ts'

type PreviewStyle = ReturnType<typeof previewFormatting>
export type CrossReferenceHref = (text: string) => string

export function entryHtml(entry: EntryRendering & { content: string }, { xemplate, xema }: Pick<WorkspaceConfig, 'xemplate' | 'xema'>,
   crossReferenceHref: CrossReferenceHref) {
   const html = entry.contentHtml
   // Older backends embed the resolved XML in a script. Read the XML without running it.
   const legacy = html?.match(/^\s*<script type='text\/javascript'>\s*\$\('#viewer'\)\.html\(Xemplatron\.xml2html\(\s*'([\s\S]*)',\n\s*\{/)
   if (html && !legacy) return html
   const xml = entry.resolvedXml ?? legacy?.[1].replaceAll("\\'", "'") ?? entry.content
   return xml ? renderXml(xml, xemplate, xema, crossReferenceHref) : ''
}

function isText(node: ChildNode): node is Text {
   return node.nodeType === Node.TEXT_NODE || node.nodeType === Node.CDATA_SECTION_NODE
}

function isElement(node: ChildNode): node is Element {
   return node.nodeType === Node.ELEMENT_NODE
}

export function renderXml(xml: string | Document, xemplate: Xemplate, xema: Xema, crossReferenceHref?: CrossReferenceHref) {
   const document = typeof xml === 'string' ? parseXml(xml) : xml
   if (!document) return ''
   const escape = xmlEscape

   function elementStyle(node: Element, id: string) {
      return previewFormatting(xemplate, id, node.nodeName)
   }

   function attributeStyle(node: Attr, parentId: string) {
      return previewFormatting(xemplate, parentId, node.ownerElement?.nodeName ?? '', node.name)
   }

   function decorate(node: Element | Attr, style: PreviewStyle, content: string, first: boolean, last: boolean, caption = '') {
      if (style.label) content = `<span class="label">${escape(style.label)}</span>&nbsp;${content}`
      for (const dimension of styleDimensions) {
         const choice = style[dimension]
         if (typeof choice === 'string' && choice) {
            content = getStyle(dimension, choice).toHtml(style.layout, content, node, first, last, caption, crossReferenceHref)
         }
      }
      return content
   }

   function renderAttribute(node: Attr, parentId: string, style: PreviewStyle, first: boolean, last: boolean) {
      const definition = xema.elements[parentId]?.attributes?.[node.name]
      const caption = definition?.values?.find(option => option.value === node.value)?.caption
      const tag = style.layout === 'block' ? 'div' : 'span'
      return `<${tag} class="clearFont">${decorate(node, style, escape(node.value), first, last, caption)}</${tag}>`
   }

   function renderElement(node: Element, id: string, parentId: string | undefined, style: PreviewStyle, first: boolean, last: boolean) {
      if (!style.shown) return ''
      const definition = xema.elements[id]
      const label = node.getAttribute('lxnm:linkable')
      let html = label === null ? '' :
         `<span style="display:none" name="${escape(label)}" class="linkable"><img src="${linkIcon}"/>${escape(label)}</span>`
      const text = node.textContent ?? ''
      let caption: string | undefined
      if (definition?.filling === 'lst') {
         html += escape(text)
         caption = definition.values?.find(option => option.value === text)?.caption
      } else if (definition?.filling === 'med') {
         const url = escape(text)
         const filetype = detectFileType(text)
         if (filetype === 'image') html += `<img src="${url}" class="media_image"/>`
         else if (filetype === 'video') html += `<video controls class="media_video"><source src="${url}"/></video>`
         else if (filetype === 'audio') html += `<audio controls class="media_audio" src="${url}"></audio>`
         else html += url
      } else {
         const attributes = Array.from(node.attributes)
            .filter(attribute => !attribute.name.startsWith('xml:') && !attribute.name.startsWith('lxnm:') &&
               !attribute.name.startsWith('xmlns:') && attribute.name !== 'xmlns')
            .map(attribute => ({ kind: 'attribute' as const, node: attribute, style: attributeStyle(attribute, id) }))
            .filter(attribute => attribute.style.shown)
         type Child = { kind: 'text'; node: Text; style?: undefined } |
            { kind: 'element'; node: Element; id: string; style: PreviewStyle }
         const children = Array.from(node.childNodes).flatMap((child): Child[] => {
            if (isText(child)) return [{ kind: 'text', node: child }]
            if (!isElement(child) || child.nodeName.startsWith('lxnm:')) return []
            const childId = xemaElementId(xema, child.nodeName, id)
            const style = elementStyle(child, childId)
            return style.shown ? [{ kind: 'element', node: child, id: childId, style }] : []
         })
         const visible = [...attributes.filter(attribute => attribute.style.order === 'before'),
            ...children, ...attributes.filter(attribute => attribute.style.order !== 'before')]
         for (const [index, child] of visible.entries()) {
            const last = index === visible.length - 1 || visible[index + 1].style?.layout === 'block'
            if (child.kind === 'element') html += renderElement(child.node, child.id, id, child.style, index === 0, last)
            else if (child.kind === 'attribute') html += renderAttribute(child.node, id, child.style, index === 0, last)
            else html += escape(child.node.data)
         }
      }

      const tag = style.layout === 'block' ? 'div' : 'span'
      const clearFont = (parentId ? xema.elements[parentId]?.filling : undefined) === 'inl' ? '' : ' class="clearFont"'
      return `<${tag}${clearFont}>${decorate(node, style, html, first, last, caption)}</${tag}>`
   }

   const root = document.documentElement
   const definition = root.getAttribute('lxnm:definition')
   const id = definition && xema.elements[definition] && xmlElementName(xema, definition) === root.nodeName
      ? definition : xemaElementId(xema, root.nodeName)
   return renderElement(root, id, undefined, elementStyle(root, id), true, true)
}

function xmlEscape(str: unknown) {
  return String(str)
		.replace(/&/g, '&amp;')
		.replace(/"/g, '&quot;')
		.replace(/'/g, '&apos;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;');
};

type StyleDimension = keyof Pick<FormattingFields, 'captioning' | 'interactivity' | 'innerPunc' | 'textsize' |
   'weight' | 'slant' | 'colour' | 'outerPunc' | 'background' | 'border' | 'gutter' | 'separation'>
type Layout = PreviewStyle['layout']
type StyleRule = {
   title: string
   toHtml(layout: Layout, html: string, node: Element | Attr, first: boolean, last: boolean,
      caption: string, crossReferenceHref?: CrossReferenceHref): string
}

function getStyle(dimension: StyleDimension, name: string) {
   const style = styles[dimension]?.[name]
   return typeof style === 'object' ? style : defaultStyle
}

const defaultStyle = { toHtml: (_layout: Layout, html: string) => html }
const styles: Record<StyleDimension, { title: string } & Record<string, StyleRule | string>> = {
  // The dimensions are ordered from innermost to outermost.
  captioning: {
    "title": "Caption display",
    "replace": {toHtml: function(ly, html, n, isF, isL, cap){return "<span>"+(cap ? xmlEscape(cap) : html)+"</span>"}, title: "Show caption instead of value"},
    "mouseover": {toHtml: function(ly, html, n, isF, isL, cap){return "<span class='caption' title='"+xmlEscape(cap)+"'>"+html+"</span>"}, title: "Show caption on mouse-over"},
  },
  interactivity: {
    "title": "Interactivity",
    "xref": {toHtml: function(ly, html, n, isF, isL, cap, crossReferenceHref) {
      const text = n.textContent ?? ''
      const href = crossReferenceHref?.(text) ?? '#'
      return '<a class="xref" data-text="' + xmlEscape(text) + '" href="' + xmlEscape(href) + '">' + html + '</a>'
    }, title: "Clickable cross-reference"},
    "xlink": {toHtml: function(ly, html, n) {
      const text = xmlEscape(n.textContent);
      if (!n.textContent || !URL.canParse(n.textContent, document.baseURI)) return text;
      const url = new URL(n.textContent, document.baseURI);
      if (!['https:', 'http:', 'mailto:', 'tel:', 'ftp:'].includes(url.protocol)) return text;
      return '<a class="xlink" target="_blank" rel="noopener" href="' + xmlEscape(url.href) + '">' + text + '</a>';
    }, title: "External URL link"},
  },
  innerPunc: {
    "title": "Inner punctuation",
    "roundBrackets": {toHtml: function(ly, html, n, isF, isL){return "("+html+")"}, title: "Round brackets"},
    "squareBrackets": {toHtml: function(ly, html, n, isF, isL){return "["+html+"]"}, title: "Square brackets"},
    "curlyBrackets": {toHtml: function(ly, html, n, isF, isL){return "{"+html+"}"}, title: "Curly brackets"},
    "comma": {toHtml: function(ly, html, n, isF, isL){return html+(isL?"":", ")}, title: "Comma"},
    "semicolon": {toHtml: function(ly, html, n, isF, isL){return html+(isL?"":"; ")}, title: "Semicolon"},
    "colon": {toHtml: function(ly, html, n, isF, isL){return html+(isL?"":": ")}, title: "Colon"},
  },
  textsize: {
    "title": "Text size",
    "smaller": {toHtml: function(ly, html, n, isF, isL){return "<span class='smaller'>"+html+"</span>"}, title: "Smaller"},
    "bigger": {toHtml: function(ly, html, n, isF, isL){return "<span class='bigger'>"+html+"</span>"}, title: "Bigger"},
  },
  weight: {
    "title": "Text weight",
    "bold": {toHtml: function(ly, html, n, isF, isL){return "<span class='bold'>"+html+"</span>"}, title: "Bold"},
  },
  slant: {
    "title": "Text slant",
    "italic": {toHtml: function(ly, html, n, isF, isL){return "<span class='italic'>"+html+"</span>"}, title: "Italic"},
  },
  colour: {
    "title": "Text colour",
    "red": {toHtml: function(ly, html, n, isF, isL){return "<span class='xema_red'>"+html+"</span>"}, title: "Red"},
    "blue": {toHtml: function(ly, html, n, isF, isL){return "<span class='xema_blue'>"+html+"</span>"}, title: "Blue"},
    "green": {toHtml: function(ly, html, n, isF, isL){return "<span class='xema_green'>"+html+"</span>"}, title: "Green"},
    "grey": {toHtml: function(ly, html, n, isF, isL){return "<span class='xema_grey'>"+html+"</span>"}, title: "Grey"},
  },
  outerPunc: {
    "title": "Outer punctuation",
    "roundBrackets": {toHtml: function(ly, html, n, isF, isL){return "("+html+")"}, title: "Round brackets"},
    "squareBrackets": {toHtml: function(ly, html, n, isF, isL){return "["+html+"]"}, title: "Square brackets"},
    "curlyBrackets": {toHtml: function(ly, html, n, isF, isL){return "{"+html+"}"}, title: "Curly brackets"},
    "comma": {toHtml: function(ly, html, n, isF, isL){return html+(isL?"":", ")}, title: "Comma"},
    "semicolon": {toHtml: function(ly, html, n, isF, isL){return html+(isL?"":"; ")}, title: "Semicolon"},
    "colon": {toHtml: function(ly, html, n, isF, isL){return html+(isL?"":": ")}, title: "Colon"},
  },
  background: {
    "title": "Background colour",
    "yellow": {toHtml: function(ly, html, n, isF, isL){return "<"+(ly=="block"?"div":"span")+" class='background xema_yellow'>"+html+"</"+(ly=="block"?"div":"span")+">"}, title: "Yellow"},
    "blue": {toHtml: function(ly, html, n, isF, isL){return "<"+(ly=="block"?"div":"span")+" class='background xema_blue'>"+html+"</"+(ly=="block"?"div":"span")+">"}, title: "Blue"},
    "grey": {toHtml: function(ly, html, n, isF, isL){return "<"+(ly=="block"?"div":"span")+" class='background xema_grey'>"+html+"</"+(ly=="block"?"div":"span")+">"}, title: "Grey"},
  },
  border: {
    "title": "Box border",
    "dotted": {toHtml: function(ly, html, n, isF, isL){return "<"+(ly=="block"?"div":"span")+" class='border dotted'>"+html+"</"+(ly=="block"?"div":"span")+">"}, title: "Dotted"},
    "solid": {toHtml: function(ly, html, n, isF, isL){return "<"+(ly=="block"?"div":"span")+" class='border solid'>"+html+"</"+(ly=="block"?"div":"span")+">"}, title: "Thin"},
    "thick": {toHtml: function(ly, html, n, isF, isL){return "<"+(ly=="block"?"div":"span")+" class='border thick'>"+html+"</"+(ly=="block"?"div":"span")+">"}, title: "Thick"},
  },
  gutter: {
    "title": "Indentation and bulleting",
    "disk": {toHtml: function(ly, html, n, isF, isL){ return _bullet(ly, "disk", html) }, title: "Round bullet"},
    "square": {toHtml: function(ly, html, n, isF, isL){ return _bullet(ly, "square", html) }, title: "Square bullet"},
    "diamond": {toHtml: function(ly, html, n, isF, isL){ return _bullet(ly, "diamond", html) }, title: "Diamond bullet"},
    "arrow": {toHtml: function(ly, html, n, isF, isL){ return _bullet(ly, "arrow", html) }, title: "Arrow bullet"},
    "indent": {toHtml: function(ly, html, n, isF, isL){ return "<"+(ly=="block"?"div":"span")+" class='indented'>"+html+"</"+(ly=="block"?"div":"span")+">" }, title: "Indent"},
    "hanging": {toHtml: function(ly, html, n, isF, isL){ return "<"+(ly=="block"?"div":"span")+" class='hanging'>"+html+"</"+(ly=="block"?"div":"span")+">" }, title: "Hanging indent"},
    "sensenum0": {title: "Sense number I, II, III...", toHtml: function(ly, html, n, isF, isL){ return _senseNum(ly, html, n, 0); }},
    "sensenum1": {title: "Sense number 1, 2, 3...", toHtml: function(ly, html, n, isF, isL){ return _senseNum(ly, html, n, 1); }},
    "sensenum2": {title: "Sense number a, b, c...", toHtml: function(ly, html, n, isF, isL){ return _senseNum(ly, html, n, 2); }},
    "sensenum3": {title: "Sense number i, ii, iii...", toHtml: function(ly, html, n, isF, isL){ return _senseNum(ly, html, n, 3); }},
  },
  separation: {
    "title": "Separation from other content",
    "space": {toHtml: function(ly, html, n, isF, isL){ if(ly=="block") return "<div class='space'>"+html+"</div>"; return (isF?"":" ")+html+(isL?"":" ");}, title: "Whitespace"},
  },
}
const styleDimensions = Object.keys(styles) as StyleDimension[]

function _getNumberingSymbol(num: number, level: number){
  var ret="&nbsp;";
  if(level==0) ret=_getRoman(num);
  if(level==1) ret=num.toString();
  if(level==2) ret=_getAbc(num);
  if(level>=3) ret=_getRoman(num).toLowerCase();
  return "<span class='numberingSymbol'>"+ret+"</span>";
}
function _getAbc(num: number){
  num=num-1;
  var list="abcdefghijklmnopqrstuvwxyz";
  var ret=list[list.length-1]; if(num<list.length) ret=list[num];
  return ret.toString();
};
function _getRoman(num: number){
  num=num-1;
  var list=["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"];
  var ret=list[list.length-1]; if(num<list.length) ret=list[num];
  return ret;
};
function _hasEponymousSiblings(n: Node){
  var num=0;
  let sibling = n.previousSibling; while(sibling){ if(sibling.nodeName==n.nodeName) num++; sibling=sibling.previousSibling; }
  sibling = n.nextSibling; while(sibling){ if(sibling.nodeName==n.nodeName) num++; sibling=sibling.nextSibling; }
  return num;
};
function _senseNum(ly: Layout, html: string, n: Node, startLevel: number) {
  var symbol="&mdash;";
  if(_hasEponymousSiblings(n)) {
    var num=0;
    let sibling: Node | null = n; while(sibling){ if(sibling.nodeName==n.nodeName) num++; sibling=sibling.previousSibling; }
    if(num) {
      var level=startLevel-1;
      let parent: Node | null = n; while(parent){ if(parent.nodeName==n.nodeName) level++; parent=parent.parentNode; }
      symbol=_getNumberingSymbol(num, level);
    }
  }
  return _bullet(ly, symbol, html);

}
function _bullet(ly: Layout, name: string, html: string){
  var symbol=""; var className="";
  if(name=="square") { symbol="⯀"; className=name; }
  else if(name=="diamond") { symbol="⯁"; className=name; }
  else if(name=="arrow") { symbol="⯈"; className=name; }
  else if(name=="disk") { symbol="⏺"; className=name; }
  else symbol=name;
  if(ly=="inline") return "<span class='bulleted "+className+"'>"+symbol+"</span>&nbsp;"+html;
  return "<div class='bulleted "+className+"'><div class='bullet'>"+symbol+"</div> <div class='inside'>"+html+"</div><div class='clear'></div></div>";
}
function detectFileType(url: string) {
  var fileExtension = (url.split('.').pop() ?? '').split(/\#|\?/)[0].toLowerCase();
  if (['jpg','jpeg','png','gif','svg'].includes(fileExtension)) return 'image';
  if (['avi','mp4','webm'].includes(fileExtension)) return 'video';
  if (['wav','ogg','weba'].includes(fileExtension)) return 'audio';
  return '';
}

// Stored custom editors can still use the Xemplatron interface.
export const Xemplatron = {
   xml2html: renderXml, xmlEscape, getStyle, defaultStyle, styles, detectFileType,
   _getNumberingSymbol, _getAbc, _getRoman, _hasEponymousSiblings, _senseNum, _bullet
}
