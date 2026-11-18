// Run: bun test hooks/
import { afterAll, beforeAll, describe, expect, test } from "bun:test";
import { spawnSync } from "node:child_process";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import guard, { findLeak, gitActions } from "../pre/tailnet-leak-guard";

// Addresses are assembled at runtime so this file never trips the guard it tests.
const ip = (...parts: Array<number | string>) => parts.join(".");
const tsnet = (name: string) => `${name}.${["ts", "net"].join(".")}`;
const added = (line: string) => `+++ b/PROFILE.md\n@@ -1,0 +1,1 @@\n+${line}\n`;

const LEAKS = [
	`- device: Pixel @ ${ip(100, 101, 102, 103)}  # verified 2026-11-18`,
	`adb connect ${ip(100, 64, 0, 1)}:5555`,
	`host ${ip(100, 127, 255, 254)}`,
	`- device: tab @ ${ip(100, 100, 1, 2)}`,
	`https://${tsnet("pixel-7.tail1a2b3")}/app.apk`,
	`- tailscale: ${tsnet("box.tail1a2b3")}`,
	`ssh ${tsnet("MyHost").toUpperCase()}`,
];
const CLEAN = [
	"- device: <machine-name> @ <tailscale-ip>  # verified YYYY-MM-DD",
	"https://<device>.<tailnet>.ts.net",
	"- device: tab @ 100.x.y.z",
	`address ${ip(100, 63, 0, 1)} is outside CGNAT`,
	`address ${ip(100, 128, 0, 1)} is outside CGNAT`,
	`version ${ip(1, 100, 64, 12, 3)}`,
	`build ${ip(2100, 64, 1, 1)}`,
	"- tailscale: <host>",
	"a mention of ts.net without a host, or *.ts.net as a pattern",
	`CIDR ${ip(100, 64, 0, 0)}/10 in documentation`,
	"10.0.0.1 and 192.168.1.20",
];

describe("findLeak", () => {
	for (const line of LEAKS) test(`blocks ${line}`, () => expect(findLeak(added(line))).toBeDefined());
	for (const line of CLEAN) test(`allows ${line}`, () => expect(findLeak(added(line))).toBeUndefined());
	test("removed and context lines are not scanned", () => {
		expect(findLeak(`--- a/PROFILE.md\n+++ b/PROFILE.md\n@@ -1 +0,0 @@\n-- device: tab @ ${ip(100, 100, 1, 2)}\n`)).toBeUndefined();
	});
	test("names the file", () => expect(findLeak(added(ip(100, 100, 1, 2)))).toContain("PROFILE.md"));
});

describe("gitActions", () => {
	const kinds = (c: string) => gitActions(c).map(a => a.kind);
	test("finds commit and push", () => {
		expect(kinds("git commit -m x")).toEqual(["commit"]);
		expect(kinds("git add a && git commit -m x && git push origin HEAD")).toEqual(["commit", "push"]);
		expect(kinds("bash -c 'git push'")).toEqual(["push"]);
	});
	test("ignores other git commands and quoted mentions", () => {
		expect(kinds("git status && git diff --cached")).toEqual([]);
		expect(kinds('echo "git push"')).toEqual([]);
		expect(kinds("git log --oneline")).toEqual([]);
	});
	test("-a variants are all-tracked commits", () => {
		expect(gitActions("git commit -am x")[0].all).toBe(true);
		expect(gitActions("git commit --all -m x")[0].all).toBe(true);
		expect(gitActions("git commit -m x")[0].all).toBe(false);
	});
	test("follows -C and cd", () => {
		expect(gitActions("git -C /tmp/wt commit -m x")[0].dir).toBe("/tmp/wt");
		expect(gitActions("cd /tmp/wt && git push")[0].dir).toBe("/tmp/wt");
		expect(gitActions("cd /tmp && cd wt && git push")[0].dir).toBe("/tmp/wt");
	});
});

describe("hook wiring in a real repo", () => {
	type Handler = (event: { toolName: string; input: Record<string, unknown> }) => Promise<unknown>;
	let repo = "";
	let remote = "";
	const run = (cwd: string, ...args: string[]) => {
		const p = spawnSync("git", args, { cwd, encoding: "utf8", env: { ...process.env, GIT_CONFIG_GLOBAL: "/dev/null", GIT_CONFIG_SYSTEM: "/dev/null", GIT_AUTHOR_NAME: "t", GIT_AUTHOR_EMAIL: "t@example.com", GIT_COMMITTER_NAME: "t", GIT_COMMITTER_EMAIL: "t@example.com" } });
		if (p.status !== 0) throw new Error(`git ${args.join(" ")}: ${p.stderr}`);
	};
	const handler = (): Handler => {
		let registered: Handler | undefined;
		guard({ on: (_n: string, fn: Handler) => { registered = fn; } } as never);
		if (!registered) throw new Error("no handler");
		return registered;
	};
	const call = (command: string) => handler()({ toolName: "bash", input: { command } }) as Promise<{ block?: boolean; reason?: string } | undefined>;

	beforeAll(() => {
		const root = mkdtempSync(join(tmpdir(), "leak-guard-"));
		remote = join(root, "remote.git");
		repo = join(root, "repo");
		run(root, "init", "-q", "--bare", "-b", "main", remote);
		run(root, "init", "-q", "-b", "main", repo);
		writeFileSync(join(repo, "PROFILE.md"), "- tailscale: <host>\n");
		run(repo, "add", "PROFILE.md");
		run(repo, "commit", "-q", "-m", "init");
		run(repo, "remote", "add", "origin", remote);
		run(repo, "push", "-q", "-u", "origin", "main");
	});
	afterAll(() => rmSync(join(repo, ".."), { recursive: true, force: true }));

	test("clean staged change passes", async () => {
		writeFileSync(join(repo, "PROFILE.md"), "- tailscale: <host>\n- note: device data lives in PROFILE.local.md\n");
		run(repo, "add", "PROFILE.md");
		expect(await call(`git -C ${repo} commit -m ok`)).toBeUndefined();
	});

	test("staged address blocks commit, naming PROFILE.local.md", async () => {
		writeFileSync(join(repo, "PROFILE.md"), `- tailscale: <host>\n  - device: Pixel @ ${ip(100, 101, 102, 103)}\n`);
		run(repo, "add", "PROFILE.md");
		const r = await call(`git -C ${repo} commit -m leak`);
		expect(r?.block).toBe(true);
		expect(r?.reason).toContain("PROFILE.local.md");
		expect(r?.reason).toContain("PROFILE.md");
	});

	test("unstaged address does not block a plain commit but blocks commit -a", async () => {
		run(repo, "reset", "-q");
		expect(await call(`git -C ${repo} commit -m x`)).toBeUndefined();
		expect((await call(`git -C ${repo} commit -am x`))?.block).toBe(true);
	});

	test("outgoing commit with a *.ts.net name blocks push; local file stays clean", async () => {
		writeFileSync(join(repo, "PROFILE.md"), `- tailscale: ${tsnet("pixel.tail1a2b3")}\n`);
		run(repo, "commit", "-q", "-am", "leak");
		expect((await call(`git -C ${repo} push`))?.block).toBe(true);
		run(repo, "reset", "-q", "--hard", "HEAD~1");
		expect(await call(`git -C ${repo} push`)).toBeUndefined();
	});

	test("other tools and non-git commands pass; git failure fails open", async () => {
		expect(await handler()({ toolName: "read", input: { command: "git push" } })).toBeUndefined();
		expect(await call("ls -la")).toBeUndefined();
		expect(await call("git -C /nonexistent/dir commit -m x")).toBeUndefined();
	});
});
