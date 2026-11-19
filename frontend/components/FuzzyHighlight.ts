import { h, type FunctionalComponent } from 'vue'

const FuzzyHighlight: FunctionalComponent<{ match?: Fuzzysort.Result | null; text?: string | null }> =
   ({ match, text }) => match?.highlight((part, index) => h('b', { class: 'red-text', key: index }, part)) ?? text

export default FuzzyHighlight
