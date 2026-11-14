// Run: bun test hooks/
import { describe, expect, test } from "bun:test";
import { homedir } from "node:os";
import workerGuard, { findViolations, isProtectedPath } from "../pre/worker-guard";

const HOME = homedir();
const rules = (command: string) => findViolations(command).map(v => v.rule);

const BLOCKED: Array<[string, string]> = [
	["pkill -f gradlew", "kill"],
	["pkill -9 java", "kill"],
	["pkill -f 'GradleDaemon'", "kill"],
	["killall java", "kill"],
	["sudo killall -9 java", "kill"],
	["echo done; pkill -f kotlin-compiler", "kill"],
	["kill -9 $(pgrep -f gradle)", "kill"],
	["jps | awk '{print $1}' | xargs kill", "kill"],
	["ps aux | grep -i gradle | awk '{print $2}' | xargs kill -9", "kill"],
	["./gradlew --stop", "gradle-stop"],
	["gradle --stop", "gradle-stop"],
	["cd app && ../gradlew --stop", "gradle-stop"],
	["JAVA_HOME=/x ./gradlew --stop", "gradle-stop"],
	["git add -A", "git-add"],
	["git add --all", "git-add"],
	["git add .", "git-add"],
	["git add ./", "git-add"],
	["git add -- .", "git-add"],
	["git add -Av", "git-add"],
	["git -C /tmp/wt add -A", "git-add"],
	["git add -A && git commit -m wip", "git-add"],
	["git add src/a.kt . ", "git-add"],
	["git stage -A", "git-add"],
	["cd x && git add .", "git-add"],
	["bash -c 'git add -A'", "git-add"],
	['sh -c "cd x && git add ."', "git-add"],
	["eval 'git add -A'", "git-add"],
	["echo $(git add -A)", "git-add"],
	["`git add -A`", "git-add"],
	["rm -rf ~/.gradle", "rm-cache"],
	["rm -rf ~/.gradle/caches", "rm-cache"],
	["rm -rf $HOME/.gradle/caches/modules-2", "rm-cache"],
	['rm -rf "${HOME}/.gradle"', "rm-cache"],
	["rm -rf ~/Library/Caches/Google", "rm-cache"],
	["rm -rf ~/Library/Caches/*", "rm-cache"],
	["rm -rf ~/Library", "rm-cache"],
	["rm -rf ~/.android/avd", "rm-cache"],
	[`rm -rf ${HOME}/.gradle`, "rm-cache"],
	["rm -rf $GRADLE_USER_HOME/caches", "rm-cache"],
	["rm -rf ~/.gra*", "rm-cache"],
	["rm -rf ~/.gradle/../.gradle/caches", "rm-cache"],
	["rm -rf ~", "rm-cache"],
	["rm -rf ~/*", "rm-cache"],
	["sudo rm -rf ~/Library/Caches", "rm-cache"],
	["rm -rf build ~/.gradle/daemon", "rm-cache"],
	["find ~/.gradle -mtime +7 -delete", "rm-cache"],
	["find ~/Library/Caches -name '*.tmp' -exec rm {} +", "rm-cache"],
];

const ALLOWED: string[] = [
	// ordinary build and git work
	"./gradlew :app:testDebugUnitTest",
	"./gradlew --status",
	"git add app/src/Main.kt app/src/Other.kt",
	"git add .gitignore",
	"git add ./app/src",
	"git add -u",
	"git add -p app/src/Main.kt",
	"git status --short && git diff --stat",
	"git commit -a -m 'fix'",
	"git -C /tmp/wt add src/a.kt",
	// forbidden text only quoted, echoed, in a message, comment or heredoc
	`git commit -m "never run git add -A; pkill gradle is banned"`,
	"git commit -m 'document gradlew --stop and rm -rf ~/.gradle rules'",
	'echo "git add -A"',
	"echo pkill java > /tmp/note.txt",
	"grep -n 'git add -A' docs/rules.md",
	"# git add -A\ngit add a.kt",
	"git commit -F - <<'EOF'\nfix(x): do not git add -A\nrm -rf ~/.gradle\nEOF\ngit status",
	"cat <<EOF\npkill java\nEOF",
	// kill by pid, unrelated pkill
	"kill 12345",
	"pkill -f my-dev-server",
	"killall Finder",
	"pgrep -f gradle",
	"ps aux | grep gradle",
	"echo java; kill 4242",
	// deleting inside the worktree or non-protected home paths
	"rm -rf build .gradle",
	"rm -rf ./.gradle/caches",
	"rm -rf .android",
	"rm -rf ~/Projects/app/.gradle",
	"rm -rf ~/Projects/app/build",
	"rm -rf ~/.gradle-wrapper-scratch",
	"rm -rf ~/.gradlew-notes",
	"rm -rf /tmp/scratch",
	"rm -rf $TMPDIR/x",
	"rm -f ~/Library.txt",
	"ls ~/.gradle ~/Library/Caches",
	"find . -name '*.orig' -delete",
	"find ~/Projects -name build -type d -exec rm -rf {} +",
	"du -sh ~/.gradle ~/.android",
];

describe("worker-guard blocks", () => {
	for (const [command, rule] of BLOCKED) {
		test(command, () => expect(rules(command)).toContain(rule as never));
	}
});

describe("worker-guard allows", () => {
	for (const command of ALLOWED) {
		test(command, () => expect(rules(command)).toEqual([]));
	}
});

test("a message names the allowed alternative", () => {
	const reasons = findViolations("git add -A && ./gradlew --stop").map(v => v.reason).join(" ");
	expect(reasons).toContain("git add path/a path/b");
	expect(reasons).toContain("report BLOCKED");
	expect(reasons).toContain("hard-rules.md");
});

test("isProtectedPath treats relative paths as the worktree", () => {
	expect(isProtectedPath(".gradle", "/home/u", ["/home/u/.gradle"])).toBe(false);
	expect(isProtectedPath("~/.gradle/x", "/home/u", ["/home/u/.gradle"])).toBe(true);
	expect(isProtectedPath("/home/u/work/.gradle", "/home/u", ["/home/u/.gradle"])).toBe(false);
});

describe("hook wiring", () => {
	type Handler = (event: { toolName: string; input: Record<string, unknown> }) => Promise<unknown>;
	const handler = (): Handler => {
		let registered: Handler | undefined;
		workerGuard({ on: (_name: string, fn: Handler) => { registered = fn; } } as never);
		if (!registered) throw new Error("no tool_call handler registered");
		return registered;
	};

	test("blocks a forbidden bash command with a reason", async () => {
		const result = (await handler()({ toolName: "bash", input: { command: "git add -A" } })) as { block: boolean; reason: string };
		expect(result.block).toBe(true);
		expect(result.reason).toContain("worker-guard");
	});

	test("passes allowed bash commands and other tools", async () => {
		expect(await handler()({ toolName: "bash", input: { command: "git add a.kt" } })).toBeUndefined();
		expect(await handler()({ toolName: "read", input: { command: "git add -A" } })).toBeUndefined();
	});

	test("pathological input never throws out of the handler", async () => {
		const nested = `${"$(".repeat(50)}git add -A${")".repeat(50)}`;
		for (const command of ['echo "unbalanced', "echo 'unbalanced", "git add -A \\", "$(((", "`", nested, "<<", "cat <<EOF\nno end"]) {
			let result: unknown;
			await expect((async () => { result = await handler()({ toolName: "bash", input: { command } }); })()).resolves.toBeUndefined();
			expect(result === undefined || typeof (result as { block?: boolean }).block === "boolean").toBe(true);
		}
	});

	test("fails open when the parser throws", async () => {
		const original = String.prototype.split;
		const errors: unknown[][] = [];
		const logged = console.error;
		console.error = (...args: unknown[]) => { errors.push(args); };
		String.prototype.split = () => { throw new Error("boom"); };
		let result: unknown = "unset";
		try {
			result = await handler()({ toolName: "bash", input: { command: "git add -A" } });
		} finally {
			String.prototype.split = original;
			console.error = logged;
		}
		expect(result).toBeUndefined();
		expect(errors.length).toBe(1);
	});
});
