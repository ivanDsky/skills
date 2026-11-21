// Build queue (user ruling 2026-11-11): parallel agent worktrees each ran
// `./gradlew assembleDebug test` at once (10 builds, load 80–99 on 8 cores, swap full).
// This hook prefixes every agent bash `gradlew` call and `python3 … ship_apk.py` call with
// ~/.local/bin/build-slot, which lets at most $BUILD_SLOTS (default 3) builds run machine-wide
// and queues the rest. Only the gradlew/ship_apk token is wrapped, so cd/export/eval in the
// persistent shell keep their meaning. Quick queries (--stop, --status, --version) skip the queue.
// `bash|sh|zsh <absolute path>.sh` is wrapped as a whole when that script runs gradlew and does not
// call build-slot itself (audit 2026-11-21: 35 script runs escaped the queue).
// The agent sees the rewritten command in its own tool call and job label; that prefix is expected
// (skill://implement/references/hard-rules.md), and a command that already names build-slot is left
// alone, so nothing nests.
// Limits: relative script paths, scripts started without a shell word, and scripts written later in
// the same command are not inspected; a wrapped script is queued as a light run because build-slot
// cannot see its Gradle tasks.
import type { ExtensionAPI } from "@oh-my-pi/pi-coding-agent";
import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const SLOT = join(homedir(), ".local/bin/build-slot");
// Command position: start, after a separator, subshell/substitution opener, or then/do/else;
// followed by optional VAR=value assignments.
const HEAD = String.raw`((?:^|[\n;&|(]|\$\(|\b(?:then|do|else)\s)\s*(?:[A-Za-z_][A-Za-z0-9_]*=(?:"[^"]*"|'[^']*'|[^\s;&|]*)\s+)*)`;
const GRADLEW = new RegExp(HEAD + String.raw`((?:[\w.~/$-]*/)?gradlew)(?=[\s;&|)]|$)([^\n;&|)]*)`, "g");
const SHIP_APK = new RegExp(HEAD + String.raw`(python3?\s+[^\s;&|)]*ship_apk\.py)`, "g");
const SCRIPT = new RegExp(HEAD + String.raw`((?:bash|sh|zsh)\s+(?:-[a-z]+\s+)*)((?:~|\$HOME|\$\{HOME\}|/)[^\s;&|)]*\.sh)(?=[\s;&|)]|$)`, "g");
const QUICK = /^\s*(?:--stop|--status|--version|-v)\b/;

/** Reads a script the command is about to run; undefined when it cannot be read. */
export type ScriptReader = (path: string) => string | undefined;

function readScriptFile(path: string): string | undefined {
	const abs = path.replace(/^(?:~|\$HOME|\$\{HOME\})(?=\/)/, homedir());
	try {
		return readFileSync(abs, "utf8");
	} catch {
		return undefined;
	}
}

/** Returns `command` with heavy build invocations prefixed by `slot`, or undefined if unchanged. */
export function queueBuilds(command: string, slot: string = SLOT, readScript: ScriptReader = readScriptFile): string | undefined {
	if (command.includes("build-slot")) return undefined;
	const next = command
		.replace(GRADLEW, (whole, head: string, gradlew: string, args: string) =>
			QUICK.test(args) ? whole : `${head}${slot} ${gradlew}${args}`,
		)
		.replace(SHIP_APK, (_whole, head: string, call: string) => `${head}${slot} ${call}`)
		.replace(SCRIPT, (whole, head: string, shell: string, path: string) => {
			// A script that calls build-slot itself is left alone: wrapping it would nest the queue.
			const body = readScript(path);
			return body !== undefined && /\bgradlew\b/.test(body) && !body.includes("build-slot") ? `${head}${slot} ${shell}${path}` : whole;
		});
	return next === command ? undefined : next;
}

export default function buildQueue(pi: ExtensionAPI): void {
	pi.on("tool_call", async event => {
		if (event.toolName !== "bash") return;
		const input = (event.input ?? {}) as Record<string, unknown>;
		const command = typeof input.command === "string" ? input.command : undefined;
		if (!command || !existsSync(SLOT)) return;
		const queued = queueBuilds(command);
		if (queued) return { input: { ...input, command: queued } };
	});
}
