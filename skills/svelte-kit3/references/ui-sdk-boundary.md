# UI SDK boundary

The UI SDK (`@ui-sdk/core` + `@ui-sdk/svelte`, exact pin, no `^`) handles interaction. Domain state, rules and undo are never its. Read `skill://ui-sdk` for the API; its docs also ship at `node_modules/@ui-sdk/<framework>/docs/llms.txt`. Its "don't hand-roll what we ship" rule covers chrome and input, not domain state.

## Chrome

Use UI SDK components (Tabs, Select, Menu, Drawer, Listbox, Field, toaster), styled to the project's design rules. Do not write a tab list, menu or sheet by hand.

## Board primitive

A board input is a `definePrimitive` kept next to the feature that uses it (shared ones in `#lib/ui/`).

- It owns focus, the drag or press session, the preview highlight, hit-testing, snapping and announcements.
- It emits intents through `"callback"` options: `onPaint(cells, mode)`, `onToggle(cell)`, `onMark(cell)`, `onConnect(a, b)`.
- It receives the board as an option (kind `"value"`, any non-primitive value) and copies it into state through `sync`, or its parts never see a change:

```ts
export const board = definePrimitive({
	name: 'paint-board',
	options: { cells: 'value', onPaint: 'callback' },
	state: (o: BoardOptions) => ({ cells: o.cells, drag: null as Drag | null }),
	sync: (o) => ({ cells: o.cells }),
	api: (context) => ({
		commit: (cells: number[], mode: Mode) => context.options().onPaint?.(cells, mode)
	}),
	slots: (slot) => ({ /* root, cell with press/pointer handlers */ })
});
```

- It imports no rules, ports, stores or ViewModel. No counts, solved flag or undo inside it.
- `createConnect` and `createParts` (`@ui-sdk/svelte/primitive`) are fine for hit-testing and markup.

The ViewModel turns each intent into exactly one `Command<S>` and pushes it into the project's command history. It then passes the new state back down as the option. Undo/Redo buttons and shortcuts call the ViewModel. Never use `createUndoStack` or `createChange` for domain state.

## Touch

Every board sets `touch-action: none`. A pointer moving faster than one cell per frame must not lose cells: the primitive fills the gap between the previous and current cell. A Playwright fast-sweep test runs in Chromium and WebKit.

## Tests

- Rules, commands and ViewModels: Vitest, no DOM.
- Your own primitives: `mount`, `checkPattern`, `checkServer`, `checkDirection` from `@ui-sdk/core/testing` in jsdom (see `skill://ui-sdk` `references/testing.md`). Always `unmount()` in `finally`.
- Touch, sheets, focus: Playwright.
- Never run `checkPattern` on UI SDK's own components.

## Beta gotchas

- Published beta.16: `import '@ui-sdk/svelte/primitive'` fails in plain Node (`ERR_UNSUPPORTED_DIR_IMPORT`). Vite and Vitest are unaffected; no build script may import it.
- Each upgrade is its own ticket with the gate and a device check.
