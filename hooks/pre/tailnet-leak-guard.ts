// Tailnet leak guard: device addresses never reach a commit or a push (audit F1).
// A public repo once published a test device's Tailscale address, adb port and tailnet name from
// PROFILE.md. Device data lives in the gitignored PROFILE.local.md (skill://deploy-tailscale §2);
// this hook refuses the commit/push that would carry it anyway:
//  - `git commit`: the staged diff (`git diff --cached -U0`; with `-a`/`--all` the diff against HEAD).
//  - `git push`: the outgoing commits (`git diff -U0 <upstream>...HEAD`, falling back to origin/HEAD, origin/main).
// Only ADDED lines are scanned, for a Tailscale CGNAT address (100.64.0.0/10 = 100.64.x.x–100.127.x.x)
// or a `<name>.ts.net` host. Placeholders (`<device>.<tailnet>.ts.net`, `100.x.y.z`) and CIDR notation pass.
// Limits (documented, not guarded): the `eval` tool and scripts that run git are not inspected; `cd`
// into another worktree is followed only for a literal `cd <path>` earlier in the same command; a push
// with no resolvable upstream and no origin/HEAD|origin/main is not scanned; git errors fail open.
import type { ExtensionAPI } from "@oh-my-pi/pi-coding-agent";
import { spawnSync } from "node:child_process";
import { posix } from "node:path";
import { commandsOf } from "./worker-guard";

const CGNAT = /(?<![\d.])100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}(?![\d/])/;
const TS_NET = /(?<![\w-])[A-Za-z0-9][A-Za-z0-9-]*\.ts\.net(?![\w-])/i;
const OPTS_WITH_VALUE = new Set(["-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"]);
const REASON =
	"tailnet-leak-guard: this change adds a Tailscale address (100.64.0.0/10) or a *.ts.net name to a tracked file, " +
	"and committed history is public once pushed. Keep device names, addresses, adb ports and tailnet names in " +
	"the gitignored PROFILE.local.md (`git check-ignore -q PROFILE.local.md`), unstage the line, and keep only " +
	"`- tailscale: <host>` in PROFILE.md. See skill://deploy-tailscale §2.";

/** First offending added line in a `-U0` diff, as `file: line`, or undefined. */
export function findLeak(diff: string): string | undefined {
	let file = "";
	for (const line of diff.split("\n")) {
		if (line.startsWith("+++ ")) file = line.slice(4).replace(/^b\//, "");
		else if (line.startsWith("+") && (CGNAT.test(line) || TS_NET.test(line))) return `${file}: ${line.slice(1).trim().slice(0, 120)}`;
	}
	return undefined;
}

export interface GitAction {
	kind: "commit" | "push";
	dir?: string;
	all: boolean;
}

/** `git commit` / `git push` invocations in the command, with their `-C`/`cd` directory. */
export function gitActions(command: string): GitAction[] {
	const out: GitAction[] = [];
	let cwd: string | undefined;
	for (const argv of commandsOf(command)) {
		const name = argv[0].split("/").pop();
		if (name === "cd" && argv[1] && !argv[1].startsWith("-")) {
			cwd = argv[1].startsWith("/") || !cwd ? argv[1] : posix.join(cwd, argv[1]);
			continue;
		}
		if (name !== "git") continue;
		let dir = cwd;
		let k = 1;
		for (; k < argv.length && argv[k].startsWith("-"); k++) {
			if (argv[k] === "-C") {
				const d = argv[++k] ?? "";
				dir = d.startsWith("/") || !dir ? d : posix.join(dir, d);
			} else if (OPTS_WITH_VALUE.has(argv[k])) k++;
		}
		const sub = argv[k];
		const rest = argv.slice(k + 1);
		if (sub === "push") out.push({ kind: "push", dir, all: false });
		else if (sub === "commit") out.push({ kind: "commit", dir, all: rest.some(a => a === "--all" || /^-[a-zA-Z]*a[a-zA-Z]*$/.test(a)) });
	}
	return out;
}

function git(dir: string | undefined, args: string[]): string | undefined {
	const p = spawnSync("git", args, { cwd: dir, encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
	return p.status === 0 ? p.stdout : undefined;
}

/** The diff a git action would publish; undefined when git cannot say (fail open). */
export function diffFor(action: GitAction): string | undefined {
	if (action.kind === "commit") return git(action.dir, ["diff", action.all ? "HEAD" : "--cached", "-U0", "--no-color"]);
	for (const base of ["@{upstream}", "origin/HEAD", "origin/main"]) {
		const diff = git(action.dir, ["diff", "-U0", "--no-color", `${base}...HEAD`]);
		if (diff !== undefined) return diff;
	}
	return undefined;
}

export default function tailnetLeakGuard(pi: ExtensionAPI): void {
	pi.on("tool_call", async event => {
		if (event.toolName !== "bash") return;
		const input = (event.input ?? {}) as Record<string, unknown>;
		const command = typeof input.command === "string" ? input.command : undefined;
		if (!command || !/\bgit\b/.test(command)) return;
		try {
			for (const action of gitActions(command)) {
				const leak = findLeak(diffFor(action) ?? "");
				if (leak) return { block: true, reason: `${REASON} Found in ${leak}` };
			}
		} catch (error) {
			console.error("tailnet-leak-guard: error, failing open:", error);
		}
	});
}
