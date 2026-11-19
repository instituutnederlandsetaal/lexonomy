# Entry editor extensions

An extension can replace the editor for one dictionary. Lexonomy still handles saving, entry navigation, the XML source view, and revision history. The extension receives the current entry and dictionary schema as arguments and returns XML when Lexonomy asks for it.

In **Configure → Entry editor**, choose **Customize entry editor**. Set **JavaScript format** to **Editor extension (v1)** and paste a JavaScript object into the JavaScript field. Save the settings and open an entry for editing. The CSS field can hold styles for your editor. Install code you trust. It runs on the Lexonomy page with the permissions of the signed-in user.

## Example

This editor shows the entry XML in a text area and adds buttons to open its linked subentries and parent entries. It works with any entry schema.

```js
({
   mount({ element, entry, schema, readOnly, signal, markDirty, openEntry }) {
      const input = document.createElement('textarea')
      input.setAttribute('aria-label', `Entry XML (${entry.schemaId ?? schema.root})`)
      input.value = entry.content
      input.readOnly = readOnly
      input.rows = 12
      input.addEventListener('input', markDirty, { signal })
      element.append(input)

      for (const related of [...(entry.subentries ?? []), ...(entry.parententries ?? [])]) {
         const button = document.createElement('button')
         button.type = 'button'
         button.textContent = `Open ${related.doctype} ${related.id}`
         button.addEventListener('click', () => openEntry(related), { signal })
         element.append(button)
      }

      return { harvest: () => input.value }
   }
})
```

## Extension API

The object must define synchronous `mount(context)`. An optional `initialXml(context)` returns starting XML for a fresh draft. Its context provides the entry and schema helpers below, before there is an editor element. In `initialXml`, `entry.content` holds the dictionary's usual starting XML. Lexonomy uses that XML when the hook is omitted.

| Context property | Use |
| --- | --- |
| `dictionaryId` | The dictionary's URL identifier. |
| `schema` | The dictionary's Xema schema. `schema.root` is the schema ID for the entry being edited, and `schema.elements[id]` gives the definition. A definition can specify a different XML tag in `elementName`. Treat the schema as read-only. |
| `entry` | The entry being rendered, including its `content` (XML), `schemaId`, and `doctype`. `id` is absent for a new entry. `subentries` and `parententries` are optional. A history preview has a `revisionId`. |
| `headwordElement` | The configured schema ID for the current entry type's headword, when set. |
| `readOnly` | Render without allowing edits when true, for example during a revision preview. |
| `signal` | An `AbortSignal` for this mount. Lexonomy uses it to cancel entry reads and subentry searches on unmount. You can use it to scope your own listeners and requests. |
| `createInitialElement(schemaId)` | Builds starting XML for that schema definition, including required attributes and children. |
| `readEntry(id)` | Reads an entry in this dictionary. Resolves to its current data or `null` if it is missing. |
| `subentries.definitions` | The dictionary's reusable subentry definitions, keyed by schema ID. Use these keys to populate a schema-aware picker. |
| `subentries.search(lemma, schemaId)` | Searches for reusable subentries of the given schema definition. Use a configured subentry schema ID such as `entry_idiom`, which can differ from the XML tag `entry`. A blank lemma returns an empty array. |
| `subentries.referenceXml(related)` | Builds the XML reference to a selected subentry. Insert it at the appropriate location in the XML your editor returns. |

`mount` also receives `element`, the container for your UI, and two callbacks you can use once it returns:

- Call `markDirty()` when the XML changes. This includes changes made by buttons and keyboard shortcuts. Lexonomy uses that signal to indicate unsaved edits and guard navigation.
- Call `openEntry({ id, doctype })` to open another entry in the same dictionary through Lexonomy's navigation.

Each related entry has `id`, `doctype`, and `title`. A title can contain HTML markup. Use `textContent` to display plain labels. The relationships in `entry` describe saved data when available. You can call `readEntry(entry.id)` for up-to-date relationships on an existing entry.

For a subentry picker, call `await subentries.search(lemma, schemaId)` when the user submits a search. Display the results in your own UI. Pass the selected result to `subentries.referenceXml()` and insert the returned XML in the draft. Call `markDirty()` after the insertion. Catch request failures and skip UI updates if `signal.aborted` is true.

Return an object with `harvest()`, which can return XML directly or return a promise that resolves to XML. Lexonomy calls it for Save and when opening the XML source view. Return the complete entry document, including any unedited XML you want to preserve. The editor can mount again when the user opens another entry, comes back from the source view, or previews a revision. Return an optional `dispose()` to release resources such as timers or observers when Lexonomy removes the editor. Use `signal` to scope event listeners to that editor's lifetime.

If the extension fails to mount, Lexonomy displays a warning and opens the configured built-in editor.

The TypeScript contract is in `frontend/js/editor-extension.ts` in the source tree.

## Migrating an older customization

Existing `editor` and `harvester` customizations can use **Legacy editor script**. `adjustDocSpec` remains available for customizing the built-in Xonomy editor. To migrate a replacement editor, move its rendering and XML export into `mount` and `harvest`. The saved `editing` settings use `editorApiVersion: 1` for the extension API and `_js` for the source code.

| Former dependency | Extension API |
| --- | --- |
| `window.xema` and `window.titling` | `schema` and `headwordElement` |
| `Screenful.Editor.entryID` and `Screenful.Editor.readUrl` | `entry.id`, `entry.subentries`, `entry.parententries`, and `readEntry(id)` |
| `Sub.searchSubentries()` and the native results menu | `subentries.search(lemma, schemaId)` and your own result controls |
| `window.store.changeEntryId(id)` | `openEntry({ id, doctype })` |
| Overrides of `Xonomy.render`, `Xonomy.harvest`, and `xema._newXml` | `mount`, `harvest`, and `initialXml` |
