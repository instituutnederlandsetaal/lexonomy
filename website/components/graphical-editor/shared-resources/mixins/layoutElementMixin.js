import valueDisplayMixin from "./valueDisplayMixin.js"
import {xml2js} from "xml-js"

export default {
   inject: ['editorState', 'editorBus'],
   mixins: [
      valueDisplayMixin
   ],
   computed: {
      configStyles() {
         let output = {}
         for (const [style, value] of Object.entries(this.elementData)) {
            switch (style) {
               case "border":
                  output.border = `1px ${value} #B3D6FF`
                  break
            }
         }
         if (this.showElementsPreview) {
            return
         }
         return output

      },
      readOnly() {
         return this.elementData.readOnly || this.showElementsPreview
      },
      componentData() {
         if (this.valueComponent === "TextInputWithMarkupComponent") {
            return this.calculatedContent.elements
               || []
         }
         if (this.isAttribute) {
            return this.calculatedContent || {type: "attribute", name: this.elementName, text: ""}
         }
         let textElement = this.calculatedContent.elements && this.calculatedContent.elements.find(element => {
            return element.type === "text" && !element.name
         })
         return textElement || {text: "", type: "text"}
      },
      calculatedContent() {
         return this.updatedContent || this.content
      }
   },
   data() {
      return {
         showChildren: true,
         updatedContent: null,
         isHeadword: false,
         newPossibleParents: [],
         showSelectNewParent: false,
         showSelectLinkedElement: false
      }
   },
   created() {
      if (this.showElementsPreview) {
         return
      }
      if (this.children && this.children.length > 0) {
         this.editorBus.addEventListener("is-parent-to-element", this.handleIsParentToElement)
      }
      if (this.editorState.headwordElement === this.elementName) {
         this.isHeadword = true
         this.editorState.headwordData = this.getHeadwordValue(this.content.elements)
      }
   },
   beforeUnmount() {
      this.editorBus.removeEventListener("is-parent-to-element", this.handleIsParentToElement)
      this.editorBus.removeEventListener('add-element-to-self', this.addElementToSelf)
   },
   methods: {
      getHeadwordValue(data) {
         if (!data) {
            return ""
         }
         try {
            return data.find(el => el.type === "text").text
         } catch (e) {
            console.error(e)
            return ""
         }
      },
      hideChildren() {
         this.showChildren = false
      },
      createElementTemplate(elementName) {
         return xml2js(`<${elementName}></${elementName}>`, this.editorState.xml2jsConfig).elements[0]
      },
      handleValueUpdate(data) {
         if (this.isAttribute) {
            this.$emit('input', {elementName: this.elementName, content: data.attributes, isAttribute: true})
            return
         }
         if (this.isHeadword) {
            this.editorState.headwordData = this.getHeadwordValue(data.elements)
         }
         let content = Object.assign({}, this.calculatedContent)
         if (Object.keys(content).length === 0) {
            content = this.createElementTemplate(this.elementName)
         }
         content.elements = data.elements
         this.$emit('input', {
            elementName: this.elementName,
            editorChildNumber: this.editorChildNumber,
            content: content
         })
      },
      handleChildUpdate(data) {
         let content = {...this.calculatedContent, ...data.content}
         if (!content.type) {
            content.type = "element"
         }
         if (!content.name) {
            content.name = this.elementName
         }
         this.$emit('input', {
            elementName: this.elementName,
            editorChildNumber: this.editorChildNumber,
            content: content
         })
      },
      updateContent(newContent) {
         this.updatedContent = newContent
      },
      moveElementDown() {
         this.$emit("move-element", {name: this.elementName, direction: 1, position: this.editorChildNumber})
      },
      moveElementUp() {
         this.$emit("move-element", {name: this.elementName, direction: -1, position: this.editorChildNumber})
      },
      createSibling() {
         this.$emit("create-element", {name: this.elementName})
      },
      deleteElement() {
         this.$emit("delete-element", {name: this.elementName, position: this.editorChildNumber})
      },
      cloneElement() {
         this.$emit("clone-element", {name: this.elementName, content: this.calculatedContent})
      },
      addLink() {
         this.showSelectLinkedElement = true},
      selectNewParent() {
         this.newPossibleParents = []
         this.editorBus.addEventListener('possible-new-parent', this.handlePossibleNewParent)
         this.editorBus.dispatchEvent(new CustomEvent('is-parent-to-element', { detail: this.elementName }))
         this.editorBus.removeEventListener('possible-new-parent', this.handlePossibleNewParent)
         this.showSelectNewParent = true
      },
      //  ------------ MOVE BETWEEN ELEMENTS ----------------
      handleSelectedNewParent(element) {
         this.editorBus.dispatchEvent(new CustomEvent('add-element-to-self', { detail: {
            name: element.props.elementName,
            editorChildNumber: element.props.content.editorChildNumber,
            content: this.calculatedContent
         } }))
         this.deleteElement()
      },
      addElementToSelf({ detail: data }) {
         if (this.elementName === data.name && this.editorChildNumber === data.editorChildNumber) {
            let newContent = Object.assign({}, data.content)
            delete newContent._index
            let content = Object.assign({}, this.calculatedContent)
            if (!content.elements) {
               content.elements = this.createElementTemplate(newContent.name)
            } else if (!content.elements.find(el => {
               return el.name === newContent.name
            })) {
               content.elements.push(newContent)
               this.updatedContent = content
               this.handleChildUpdate({content: content})
               return
            }
            content = this.appendElementAfterSameNameSiblings(newContent.name, content, newContent)
            this.updatedContent = content
            this.handleChildUpdate({content: content})
         }
         this.editorBus.removeEventListener('add-element-to-self', this.addElementToSelf)
      },
      //  ------------ EVENT HANDLERS ----------------
      handlePossibleNewParent({ detail }) {
         this.newPossibleParents.push(detail)
      },
      handleIsParentToElement({ detail: elementName }) {
         if (this.children.some(el => el.name === elementName)) {
            this.editorBus.dispatchEvent(new CustomEvent('possible-new-parent', {
               detail: {
                  ...this.calculatedContent,
                  parentName: this.parentElementName,
                  editorChildNumber: this.editorChildNumber
               }
            }))
            this.editorBus.addEventListener('add-element-to-self', this.addElementToSelf)
         }
      },

      appendElementAfterSameNameSiblings(data, content, newContent) {
         let elements = content.elements || []
         let locationOfLastElement = elements.map(el => el.name).lastIndexOf(data)
         if (locationOfLastElement >= 0) {
            elements.splice(locationOfLastElement + 1, 0, newContent)
         } else {
            elements.push(newContent)
         }
         content.elements = elements
         return content
      }
   }
}
