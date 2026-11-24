# Screen + ViewModel + typed context

This file is the skeleton to copy. If the project has an ADR for layout and import rules, the ADR wins on any conflict.

## Services context (`#lib/app/services.ts`)

```ts
import { createContext } from 'svelte';
import type { AnalyticsSink } from '#lib/ports/analytics.ts';
import type { Clock } from '#lib/ports/clock.ts';

export type Services = { analytics: AnalyticsSink; clock: Clock /* ...one entry per port */ };

export const [getServices, setServices] = createContext<Services>();
```

`createContext` needs Svelte ≥ 5.40; `getServices()` throws when nothing called `setServices`, which is the point. The root `+layout.svelte` is the only caller of `setServices(browserServices())`. Tests call it with `memoryServices()` from `#lib/adapters/memory.ts`.

The layout also renders on the server, so a browser adapter constructor must not touch `window`, `localStorage` or `fetch` until a method is called.

## ViewModel (`#lib/features/<name>/<Name>ViewModel.svelte.ts`)

```ts
import type { Services } from '#lib/app/services.ts';

type Deps = Pick<Services, 'analytics' | 'clock'>;

export class CounterViewModel {
	#deps: Deps;
	count = $state(0);
	doubled = $derived(this.count * 2);

	constructor(deps: Deps) {
		this.#deps = deps;
	}

	increment = () => {
		this.count += 1;
		this.#deps.analytics.track('counter_increment', { count: this.count });
	};
}
```

- Arrow-function fields, so `onclick={vm.increment}` keeps `this`.
- Take only the port slices you use, never the whole `Services`.
- No `$effect` in a ViewModel unless it wraps a DOM or timer resource, and then dispose it from a `destroy()` the Screen calls.
- Never import another feature, an adapter, `window` or `document`.
- Explicit `.svelte.ts` extension in the import (`allowImportingTsExtensions` is on in `$app/tsconfig`). Extensionless `./x.svelte` also resolves; do not mix the two in one project.

## Screen (`<Name>Screen.svelte`)

```svelte
<script lang="ts">
	import { getServices } from '#lib/app/services.ts';
	import { CounterViewModel } from './CounterViewModel.svelte.ts';

	const vm = new CounterViewModel(getServices());
</script>

<button onclick={vm.increment}>{vm.count} / {vm.doubled}</button>
```

The Screen binds and lays out. No branching on domain or session state beyond `{#if}` over ViewModel fields; no port access. A route's `+page.svelte` renders one Screen and nothing else.

## Test (`CounterViewModel.svelte.test.ts`, no DOM)

```ts
import { expect, test } from 'vitest';
import { memoryServices } from '#lib/adapters/memory.ts';
import { CounterViewModel } from './CounterViewModel.svelte.ts';

test('increment tracks and counts', () => {
	const services = memoryServices();
	const vm = new CounterViewModel(services);
	vm.increment();
	expect(vm.count).toBe(1);
	expect(services.analytics.events).toEqual([{ name: 'counter_increment', props: { count: 1 } }]);
});
```

The `.svelte.test.ts` name lets the file use runes. `$derived` reads are lazy, so assert on `vm.doubled` directly; use `flushSync()` from `'svelte'` or `$effect.root` only when testing an effect. Component and browser levels: `skill://tdd` `references/web-testing.md`.
