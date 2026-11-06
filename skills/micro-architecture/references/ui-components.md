# UI component rules — payload

Read when a ticket or diff adds or changes a public `@Composable`, an
`XxxState` holder, an `XxxDefaults`/`XxxColors` type, or a `Modifier`
factory. A reusable component has no business rules, only UI logic and UI
element state. It does not get Clean Architecture's layers. It gets
building-block layers, hoisted state, plain state holders, slots and
`XxxDefaults`. App-level layering (screen → ViewModel → domain → data) stays
with `design-architecture`/references/rules-architecture.md. Canonical shape:
[../examples/ui-component/](../examples/ui-component/).

## Tier first

The androidx guidelines set requirement levels per audience. Pick the tier
per module before applying any rule, and state it on every finding.

| Tier | Code | How to tell | Strength |
|---|---|---|---|
| library | design-system or shared UI module, or any published artifact | module named `designsystem`, `core:ui`, `ui-kit`, `components`; consumed by ≥2 feature modules; `maven-publish` or `explicitApi()` | rules at their MUST; rule 11 only when published |
| app | feature screens and components used inside one feature | everything else | MUST rules drop to SHOULD (rule 7 stays MUST); rule 11 off |

`start` infers the tier. When it is ambiguous (one module, a shared
`ui/components` package), `start` asks once and the answer is ledgered as
`Ruling: ui-tier <module> = library|app — <why>`.

## Primary bias to correct

- Clean Architecture inside a component: a use case, mapper, domain model or
  ViewModel for UI-only state.
- Component by reflex: a wrapper over `Row` + `Text` the caller writes in
  three lines.
- Knob soup: `XxxStyle`/`XxxConfig` grab-bags, Boolean shape flags, a second
  `Modifier` parameter.
- Wrong state owner: everything hoisted into the ViewModel, or internal
  `remember` state the caller cannot read or reset.
- Wrong API looseness: `title: String, icon: ImageVector?` where callers need
  arbitrary content, or slots everywhere for flexibility no caller asked for.

## Decision rules

1. **Need.** Before adding a component, build the use from public blocks
   (`Row`, `Text`, `Modifier.selectable`). If the result is simple and readable
   and needs no hidden knowledge, callers can write it, so there is no
   component. Shipping one has a long-term cost. SHOULD.
2. **One problem, layered.** Each component solves one problem, and each
   problem is solved in one place. A component with two jobs is split
   (`Button` + `checked` → `Button`, `ToggleButton`). Layer from
   single-purpose blocks: a `Basic*` block (no design opinion, made to be
   wrapped) first, then the styled component built from public blocks. MUST.
3. **Component or Modifier.** Decorating any single element (padding, click,
   clip, semantics) is a `Modifier.x()` factory extension. Adding or removing
   structure, or distinct UI, is a component. No optional parameter may
   duplicate a Modifier (`onClick` or `clipToCircle` on a leaf). SHOULD.
4. **`modifier`.** Every UI-emitting component takes exactly one
   `modifier: Modifier = Modifier`. It is the first optional parameter and is
   applied once to the root, first in the chain. Intrinsic modifiers are
   appended after it, never prepended. A conditional root gets it on each
   branch root. Child-specific modifiers become slots or a split, never
   `iconModifier`. MUST.
5. **Parameters.** Order: required, then `modifier`, then optional, then a
   trailing `content` slot. Within each group, data comes before metadata,
   which comes before customization.
   - Defaults are public and meaningful: inline for one or two, otherwise an
     `XxxDefaults` object. State-dependent colors or elevations go in an
     `@Immutable class XxxColors` built by `XxxDefaults.colors()`.
   - `null` means absent, never "use the default".
   - No grab-bag `XxxStyle`; variants are separate components
     (`PrimaryButton`).
   - A CompositionLocal is read in a default expression, never in the body.

   MUST.
6. **State owner: the lowest that works** (table A). Ladder:
   - local `remember`/`rememberSaveable`;
   - the lowest common ancestor of the readers and writers;
   - a plain `@Stable class XxxState` with `rememberXxxState()`, when UI
     logic is complex or reused;
   - a ViewModel, only for business logic or screen UI state.

   A component is controlled (`value` + `onValueChange`) or takes a hoisted
   `state: XxxState = rememberXxxState()`. Never `MutableState<T>`/`State<T>`
   parameters (use `T` or `() -> T`), and never a nullable state sentinel.
   The holder carries the interaction logic and is unit-tested without
   composing UI. That fulfils rules-architecture 15 for components. MUST.
7. **State boundaries.** No ViewModel or screen-level holder passes below the
   route composable; pass the state slice and event lambdas. A plain holder
   never depends on a longer-lived holder. Frame-clock work
   (`animateScrollToItem`, `DrawerState.close()`) runs in
   `rememberCoroutineScope()`, never `viewModelScope`, which throws "a
   MonotonicFrameClock is not available". `rememberSaveable`/`Saver` saves
   serializable values only, never runtime objects or callbacks. MUST at both
   tiers.
8. **API shape** (table B). A caller-varying visual region is a slot
   (`@Composable () -> Unit`); an optional one is nullable with a `null`
   default, so its spacing disappears. A region the design system constrains
   stays a primitive, enum or restrictive parameter. Children that need parent
   config or must stay scoped to the parent get a scope receiver. Anything
   else is an inline conditional.
   - No slot or scope for hypothetical flexibility.
   - Slot content keeps its lifecycle when the parent's layout changes. Use
     one `Layout` or `movableContentOf`, never
     `if (x) Row { content() } else Column { content() }`.

   SHOULD.
9. **Names and returns.** A Unit composable is a PascalCase noun that emits
   its root. A composable that returns a value is camelCase and emits nothing
   (emit XOR return). Factories that remember are `rememberXxx`;
   CompositionLocals are `LocalXxx`. No company or module prefix
   (`AppButton`); the default variant takes the plain name. MUST.
10. **Accessibility and tooling.** Build on foundation blocks
    (`Modifier.clickable`, `Image`) to inherit semantics; `Layout` and
    `pointerInput` code adds semantics by hand. Initial state comes from
    parameters, not a `LaunchedEffect`, so previews and screenshot tests render
    frame one. A component creates its runtime objects (`LazyListState`,
    `FocusRequester`) itself or as remembered defaults, so sample data alone
    previews it (`preview-compose`). SHOULD.
11. **Evolution (published library only).**
    - Never remove or reorder parameters.
    - New parameters get defaults and go last, or before a trailing lambda.
    - A changed signature is a new overload, with the old one
      `@Deprecated(level = DeprecationLevel.HIDDEN)` delegating to it.
    - Never add or remove `@Stable`/`@Immutable` on a released type.

    MUST.

## A. Where state lives

| State / logic | Owner |
|---|---|
| Element-only UI state (expanded, pressed, animation) | local `remember` / `rememberSaveable` |
| UI state siblings share | lowest common ancestor composable |
| UI state + UI logic, complex or reused | plain `@Stable` holder via `rememberXxxState()`; `Saver` if it must survive recreation |
| Runtime UI objects (`LazyListState`, `FocusRequester`, `DrawerState`) | composition (remembered), never a ViewModel |
| UI-derived logic (show FAB from scroll position) | composable or plain holder (`derivedStateOf`) |
| UI state that business logic reads or writes (query driving suggestions) | ViewModel (documented exception) |
| Business output → screen UI state | ViewModel (`rules-architecture` 19) |
| Events that change state | lambdas passed up to the owner |

## B. API shape

| Choice | Pick when | Avoid when |
|---|---|---|
| Restrictive (typed params, closed variants) | the design system must forbid variants; the case set is small and closed | callers need arbitrary content; variants keep growing |
| Slot (nullable when optional) | the region varies per caller with no design constraint; the component owns order and spacing | slots multiply per distinction; children need parent state |
| Slot + `@Stable` `XxxDefaults` sub-parts | styled sub-parts must be discoverable without top-level `XxxTitle()` functions | a single variant with no shared tokens |
| Scope receiver (`RowScope`-like, per-slot scopes) | children need parent config (size, toggle) or child-layout control is a public contract | a simple conditional; the scope starts holding business logic |
| Inline conditional | two or three cases, no reusable contract | branches that change for unrelated reasons |

## File map for one component

One public type per file (rules-architecture 20). Create only the files the
component needs: a stateless component with two defaults is one file.

| File | Holds |
|---|---|
| `BasicTag.kt` | the unstyled building block, when layering is real |
| `Tag.kt` | the styled composable, its `content` overloads, its previews |
| `TagDefaults.kt` | `object TagDefaults`: tokens and `colors()` |
| `TagColors.kt` | `@Immutable class TagColors` |
| `TagGroupState.kt` | `@Stable class TagGroupState` + `rememberTagGroupState()` + its `Saver` |

## Trigger rules

- Adding a public composable → rule 1 first; write the reason in the ticket.
- A Boolean or enum parameter that changes structure → rule 2 (split) or
  rule 8 (slot).
- A `String`/`ImageVector` content parameter on a reusable component →
  rule 8.
- A `ViewModel`, `MutableState` or `State` parameter below the route →
  rules 6–7.
- `remember { mutableStateOf(…) }` the caller needs to read or reset →
  rule 6: hoist.
- A use case, mapper or domain model added for UI-only state → delete it;
  the app layering rules do not apply.
- Changing a public signature in a published module → rule 11.

## Final checklist

- The tier is named; every finding states it.
- Every new component passed rule 1 and solves one problem.
- One `modifier`: first optional, applied first, at the root.
- Parameter order holds; defaults are public; no null-as-default, no style
  bag.
- Each piece of state has one owner from table A; no ViewModel below the
  route; holder logic is tested headless.
- Slots, restrictive params and scopes each match table B.
- Previews render from parameters alone.
- Published module: no removed parameter; new ones are defaulted.

## Sources

Paraphrased; requirement levels kept. Licenses and notices are in
`ATTRIBUTION.md`.

- [Compose Component API Guidelines](https://github.com/androidx/androidx/blob/androidx-main/compose/docs/compose-component-api-guidelines.md)
  and [Compose API Guidelines](https://github.com/androidx/androidx/blob/androidx-main/compose/docs/compose-api-guidelines.md)
  (androidx, Apache-2.0).
- [Where to hoist state](https://developer.android.com/develop/ui/compose/state-hoisting)
  and [State holders and UI state](https://developer.android.com/topic/architecture/ui-layer/stateholders).
- [chrisbanes/skills](https://github.com/chrisbanes/skills)
  `compose-component-design`, `compose-state-and-effects` (Apache-2.0).
- Bumble Tech, [Refining Compose API for design systems](https://medium.com/bumble-tech/refining-compose-api-for-design-systems-d652e2c2eac3)
  (table B).
- Stream, [Composition patterns in Jetpack Compose](https://getstream.io/blog/composition-pattern-compose/)
  (scope caveats).
