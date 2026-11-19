import Materialize from '../libs/materialize/materialize.min.js'
// Materialize wraps the native select. Restore the DOM before Vue patches it.
export const materializeSelects = {
   mounted() {
      Materialize.FormSelect.init(this.$el.querySelectorAll('select'))
   },
   beforeUpdate() {
      this.destroyFormSelects()
   },
   updated() {
      Materialize.FormSelect.init(this.$el.querySelectorAll('select'))
   },
   beforeUnmount() {
      this.destroyFormSelects()
   },
   methods: {
      destroyFormSelects() {
         for (const element of this.$el.querySelectorAll('select')) {
            Materialize.FormSelect.getInstance(element)?.destroy()
         }
      }
   }
}
