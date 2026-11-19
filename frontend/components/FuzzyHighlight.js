import { h } from 'vue'
import FuzzySort from '../libs/fuzzysort/fuzzysort.js'

export default function FuzzyHighlight({ match, text }) {
   return match
      ? FuzzySort.highlight(match, part => h('b', { class: 'red-text' }, part))
      : text
}
