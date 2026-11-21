// Run: bun test hooks/
// The Claude Code ports (hooks/claude) run the omp hooks unchanged; these tests check the translation
// to PreToolUse output and that each entry runs as a real command hook (stdin JSON in, JSON out, exit 0).
import { afterAll, beforeAll, describe, expect, test } from "bun:test";
import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { homedir, tmpdir } from "node:os";
import { join } from "node:path";
import { decide, type OmpHook, type PreToolUsePayload } from "../claude/adapter";
import apkShipGuard from "../pre/apk-ship-guard";
import buildQueue from "../pre/build-queue";
import tailnetLeakGuard from "../pre/tailnet-leak-guard";
import workerGuard from "../pre/worker-guard";

const SLOT = join(homedir(), ".local/bin/build-slot");
const bash = (command: string, extra: Record<string, unknown> = {}): PreToolUsePayload => ({
	tool_name: "Bash",
	tool_input: { command, description: "test call", ...extra },
});
// Assembled at runtime so this file never trips the guards it tests.
const ip = (...parts: number[]) => parts.join(".");

describe("decide", () => {
	test("a block becomes a deny with the omp reason", async () => {
		const out = await decide(workerGuard, bash("pkill -f build-slot"));
		expect(out?.hookSpecificOutput.permissionDecision).toBe("deny");
		expect(out?.hookSpecificOutput.permissionDecisionReason).toContain("worker-guard");
	});

	test("a rewrite becomes updatedInput that keeps the other fields and does not auto-approve", async () => {
		const rewrite: OmpHook = pi => pi.on("tool_call", async (e: { input: Record<string, unknown> }) => ({ input: { ...e.input, command: "wrapped" } }));
		const out = await decide(rewrite, bash("./gradlew help", { timeout: 1000 }));
		expect(out?.hookSpecificOutput.updatedInput).toEqual({ command: "wrapped", description: "test call", timeout: 1000 });
		expect(out?.hookSpecificOutput.permissionDecision).toBeUndefined();
	});

	test("an allowed command has no opinion", async () => expect(await decide(workerGuard, bash("git status --short"))).toBeUndefined());

	test("other tools are ignored without calling the hook", async () => {
		let called = false;
		const spy: OmpHook = pi => pi.on("tool_call", async () => { called = true; return { block: true }; });
		expect(await decide(spy, { tool_name: "Read", tool_input: { file_path: "/x" } })).toBeUndefined();
		expect(called).toBe(false);
	});

	test("apk-ship-guard refuses Gradle's default APK name", async () => {
		const out = await decide(apkShipGuard, bash("adb install -r app/build/outputs/apk/debug/app-debug.apk"));
		expect(out?.hookSpecificOutput.permissionDecision).toBe("deny");
	});

	test.skipIf(!existsSync(SLOT))("build-queue wraps gradlew in build-slot", async () => {
		const out = await decide(buildQueue, bash("cd /wt && ./gradlew help"));
		expect(out?.hookSpecificOutput.updatedInput?.command).toBe(`cd /wt && ${SLOT} ./gradlew help`);
	});
});

describe("tailnet-leak-guard through the adapter", () => {
	let repo = "";
	const git = (...args: string[]) => spawnSync("git", args, {
		cwd: repo,
		env: { ...process.env, GIT_CONFIG_GLOBAL: "/dev/null", GIT_CONFIG_SYSTEM: "/dev/null" },
	});

	beforeAll(() => {
		repo = mkdtempSync(join(tmpdir(), "claude-leak-"));
		git("init", "-q");
		writeFileSync(join(repo, "PROFILE.md"), `- device: tab @ ${ip(100, 101, 102, 103)}\n`);
		git("add", "PROFILE.md");
	});
	afterAll(() => rmSync(repo, { recursive: true, force: true }));

	test("refuses a commit that adds a tailnet address", async () => {
		const out = await decide(tailnetLeakGuard, bash(`cd ${repo} && git commit -m wip`));
		expect(out?.hookSpecificOutput.permissionDecision).toBe("deny");
	});
});

describe("entries run as Claude Code command hooks", () => {
	const run = (hook: string, stdin: string) =>
		spawnSync(process.execPath, [join(import.meta.dir, "../claude", `${hook}.ts`)], { input: stdin, encoding: "utf8" });
	const HOOKS = ["build-queue", "worker-guard", "apk-ship-guard", "tailnet-leak-guard"];

	for (const hook of HOOKS) {
		test(`${hook}: a harmless command prints nothing and exits 0`, () => {
			const p = run(hook, JSON.stringify(bash("ls -la")));
			expect([p.status, p.stdout]).toEqual([0, ""]);
		});
		test(`${hook}: unreadable stdin fails open`, () => {
			const p = run(hook, "not json");
			expect([p.status, p.stdout]).toEqual([0, ""]);
		});
	}

	test("worker-guard denies pkill of build-slot", () => {
		const p = run("worker-guard", JSON.stringify(bash("pkill -f build-slot")));
		expect(p.status).toBe(0);
		expect(JSON.parse(p.stdout).hookSpecificOutput.permissionDecision).toBe("deny");
	});

	test.skipIf(!existsSync(SLOT))("build-queue rewrites ./gradlew help", () => {
		const p = run("build-queue", JSON.stringify(bash("./gradlew help")));
		expect(p.status).toBe(0);
		expect(JSON.parse(p.stdout).hookSpecificOutput.updatedInput.command).toBe(`${SLOT} ./gradlew help`);
	});
});
