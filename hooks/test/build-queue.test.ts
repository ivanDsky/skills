// Run: bun test hooks/
import { describe, expect, test } from "bun:test";
import { queueBuilds } from "../pre/build-queue";

const SLOT = "/q/build-slot";
const SCRIPTS: Record<string, string> = {
	"/tmp/gate.sh": "cd /wt && ./gradlew :app:testDebugUnitTest :konsist:test 2>&1 | tail -30\n",
	"~/scratch/run-1890-gates.sh": "#!/bin/bash\ncd /wt || exit 1\n./gradlew :app:testDebugUnitTest > /tmp/g.log 2>&1\n",
	"/tmp/self-queued.sh": "~/.local/bin/build-slot ./gradlew :app:testDebugUnitTest\n",
	"/tmp/no-gradle.sh": "git status --short\n",
};
const queue = (command: string) => queueBuilds(command, SLOT, path => SCRIPTS[path]);

const WRAPPED: Array<[string, string]> = [
	["./gradlew :app:testDebugUnitTest", `${SLOT} ./gradlew :app:testDebugUnitTest`],
	["cd /wt && ./gradlew test", `cd /wt && ${SLOT} ./gradlew test`],
	["python3 ~/.agents/skills/deliver/scripts/ship_apk.py --slug x", `${SLOT} python3 ~/.agents/skills/deliver/scripts/ship_apk.py --slug x`],
	["bash /tmp/gate.sh", `${SLOT} bash /tmp/gate.sh`],
	["bash ~/scratch/run-1890-gates.sh", `${SLOT} bash ~/scratch/run-1890-gates.sh`],
	["cd /wt; bash -x /tmp/gate.sh | tail -5", `cd /wt; ${SLOT} bash -x /tmp/gate.sh | tail -5`],
];

const UNCHANGED = [
	"./gradlew --stop",
	"./gradlew --status",
	"~/.local/bin/build-slot ./gradlew :app:testDebugUnitTest",
	"bash /tmp/self-queued.sh",
	"bash /tmp/no-gradle.sh",
	"bash /tmp/missing.sh",
	"bash scripts/relative.sh",
	"cat /tmp/gate.sh",
	"echo bash /tmp/gate.sh",
];

describe("build-queue wraps", () => {
	for (const [command, expected] of WRAPPED) test(command, () => expect(queue(command)).toBe(expected));
});

describe("build-queue leaves alone", () => {
	for (const command of UNCHANGED) test(command, () => expect(queue(command)).toBeUndefined());
});
