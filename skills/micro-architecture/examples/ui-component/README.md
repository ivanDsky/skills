# Sample component: Tag and TagGroup

This is the canonical shape for [../../references/ui-components.md](../../references/ui-components.md),
at the library tier. It was compiled against Compose BOM + Material3 (Kotlin
2.2) and its holder test passed (4/4) inside a scratch Android app on
2026-11-05. Package `com.example.ui.tag` is a placeholder.

| File | Rules it shows |
|---|---|
| `BasicTag.kt` | 2: an unstyled building block, built on `Modifier.toggleable` (10: inherits semantics); 4: `modifier` first optional, applied first |
| `Tag.kt` | 2: a styled layer over `BasicTag`; 5: parameter order, `colors` default from `TagDefaults`; 8: `label` slot, nullable `leadingIcon` slot (no spacing when `null`); 4: intrinsic modifiers appended after `modifier`; previews per state |
| `TagDefaults.kt` | 5: public tokens and `colors()`; theme values read in default expressions |
| `TagColors.kt` | 5: `@Immutable` state-dependent colors with value equality |
| `TagGroupState.kt` | 6: plain `@Stable` holder with private setters, `rememberTagGroupState()`, and a `Saver` that saves only serializable values (7) |
| `TagGroup.kt` | 6: hoisted `state: TagGroupState = rememberTagGroupState()`; no ViewModel; 10: preview renders from parameters |
| `TagGroupStateTest.kt` | 6: holder logic unit-tested headless, with no UI test rule |

Each file declares one public type or composable, plus its
`remember<Type>()` factory (structure-checks S1).
