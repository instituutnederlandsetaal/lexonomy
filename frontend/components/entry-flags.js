export function flagTextColor(color) {
   const matches = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(color)
   if (!matches) return '#000000'
   const [red, green, blue] = matches.slice(1).map(channel => parseInt(channel, 16))
   return red * 0.299 + green * 0.587 + blue * 0.114 > 186 ? '#000000' : '#ffffff'
}
