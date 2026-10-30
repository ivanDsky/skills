# Playground & prototype links

## Showkase (in-app component catalog)

Airbnb's Showkase (MIT) generates a browser from annotations - zero manual
indexing:

1. `showkase` + `showkase-processor` as debugImplementation / kspDebug.
2. Annotate: `@ShowkaseComposable("name", "group")` on previews or composables
   (it also picks up @Preview composables), `@ShowkaseColor`,
   `@ShowkaseTypography`.
3. `ShowkaseBrowserActivity` renders them all with dark mode / RTL / font-scale
   variants - the playground the dev settings screen links to.
   https://github.com/airbnb/Showkase

## Prototype screens

- Prototype routes live in the nav graph behind a debug gate (or the prototype
  flag) - reachable in debug builds only.
- Register each as a row in dev settings; the row resolves via deep link.
- Jump straight from the terminal: `adb shell am start -W -d <deep-link-uri>`
  (works over wireless adb from diagnose-bug's setup).
