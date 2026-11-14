// Run: bun test hooks/
// The hard-rules block is pasted verbatim into every spawn-prompt template; fail when a copy drifts.
import { expect, test } from "bun:test";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const ROOT = join(import.meta.dir, "../..");
const read = (path: string) => readFileSync(join(ROOT, path), "utf8");

const canonical = read("skills/implement/references/hard-rules.md").split("```\n")[1];

const PASTED_IN = [
	"skills/implement/references/dispatch.md",
	"skills/prototype/references/page-brief.md",
	"skills/fan-out-research/references/finding-format.md",
];
const POINTER = "skill://implement/references/hard-rules.md";
const POINTED_FROM = [
	"skills/assess-teardown/references/architect-brief.md",
	"skills/goldfish-review/references/lenses.md",
];

test("canonical block is at most 10 lines", () => {
	expect(canonical.startsWith("Hard rules")).toBe(true);
	expect(canonical.trimEnd().split("\n").length).toBeLessThanOrEqual(10);
});

for (const path of PASTED_IN) {
	test(`${path} carries the block verbatim`, () => expect(read(path)).toContain(canonical));
}

for (const path of POINTED_FROM) {
	test(`${path} points to the canonical block`, () => expect(read(path)).toContain(POINTER));
}
