export function parseXml(source) {
   const xml = new DOMParser().parseFromString(source, 'application/xml')
   return xml.getElementsByTagNameNS('http://www.mozilla.org/newlayout/xml/parsererror.xml', 'parsererror').length
      ? null : xml
}

export function isValidXmlName(name) {
   return Boolean(name && parseXml('<' + name + '/>')?.documentElement.nodeName === name)
}
