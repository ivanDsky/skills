// Worker guard: the mechanically detectable rules of skills/implement/references/hard-rules.md.
// Agents broke these in prose more than once (audit F6), so the bash tool refuses them:
//  1. pkill / killall of gradle, java, kotlin or build-slot, `kill` of a pgrep'd gradle/java, `gradlew --stop`
//     (kills the daemons and queued builds of every other lane on the machine).
//  2. `git add -A`, `git add --all`, `git add .` (blind staging reverts other work).
//  3. `rm` (or `find -delete`) of ~/.gradle, ~/Library, ~/.android or an ancestor such as ~
//     (shared caches; a full disk is reported BLOCKED, never cleaned by a worker).
//  4. `yes` as a command (`yes | sdkmanager --licenses`): it never ends by itself, and when its reader hangs or
//     the worker's shell is cut off it is left running at full CPU (24 orphans slowed the merge lane for 56 min).
//     Use the command's non-interactive flag instead (`--yes`, `-y`, `--assume-yes`, `--non-interactive`).
// The command is parsed into shell words, so a quoted commit message, an `echo`, a heredoc body or
// a comment that merely mentions a forbidden command is allowed; `bash -c "…"`, `eval`, `$(…)`,
// backticks, `sudo`, `env`, `xargs` and VAR=value prefixes are looked through.
// Limits (documented, not guarded): the `eval` tool and scripts written to disk and then run are
// not inspected; a `cd ~/.gradle && rm -rf caches` is invisible because relative paths are never
// resolved; `git commit -a` (tracked files only) is allowed; a heredoc piped into a shell is not parsed.
import type { ExtensionAPI } from "@oh-my-pi/pi-coding-agent";
import { homedir } from "node:os";
import { posix } from "node:path";

const MAX_DEPTH = 5;
const TARGET = /gradle|java|kotlin|build-slot/i;
const WRAPPERS = new Set([
	"sudo", "command", "builtin", "exec", "nohup", "time", "nice", "env", "xargs", "stdbuf", "timeout",
	"then", "do", "else", "if", "while", "until", "elif", "!", "{",
]);
const SHELLS = new Set(["bash", "sh", "zsh", "dash", "ksh"]);
const PROCESS_LISTERS = new Set(["pgrep", "pidof", "ps", "jps", "lsof", "grep", "egrep", "awk", "pkill"]);
const GLOBAL_GIT_OPTS_WITH_VALUE = new Set(["-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"]);

/** Reads `$( … )` starting just after the opening paren; returns the inner text and the index after `)`. */
function readSubstitution(src: string, start: number): { inner: string; next: number } {
	let depth = 1;
	let i = start;
	while (i < src.length) {
		const c = src[i];
		if (c === "\\") i += 2;
		else if (c === "'") i = (src.indexOf("'", i + 1) + 1 || src.length);
		else if (c === '"') {
			i++;
			while (i < src.length && src[i] !== '"') i += src[i] === "\\" ? 2 : 1;
			i++;
		} else if (c === "(") { depth++; i++; }
		else if (c === ")") {
			if (--depth === 0) return { inner: src.slice(start, i), next: i + 1 };
			i++;
		} else i++;
	}
	return { inner: src.slice(start), next: src.length };
}

function readBackticks(src: string, start: number): { inner: string; next: number } {
	let i = start;
	while (i < src.length && src[i] !== "`") i += src[i] === "\\" ? 2 : 1;
	return { inner: src.slice(start, i), next: i + 1 };
}

/** Splits `src` into simple commands (argv word lists), descending into `$( )` and backticks. */
export function simpleCommands(src: string, depth = 0): string[][] {
	const out: string[][] = [];
	if (depth > MAX_DEPTH) return out;
	let words: string[] = [];
	let cur = "";
	let has = false;
	let pending: Array<{ delim: string; dash: boolean }> = [];
	const endWord = () => {
		if (has) words.push(cur);
		cur = "";
		has = false;
	};
	const endCommand = () => {
		endWord();
		if (words.length) out.push(words);
		words = [];
	};
	const substitution = (read: { inner: string; next: number }) => {
		out.push(...simpleCommands(read.inner, depth + 1));
		cur += "$(…)";
		has = true;
		return read.next;
	};
	let i = 0;
	const n = src.length;
	while (i < n) {
		const c = src[i];
		if (c === "\\") {
			if (src[i + 1] === "\n") { i += 2; continue; }
			cur += src[i + 1] ?? "";
			has = true;
			i += 2;
		} else if (c === "'") {
			const close = src.indexOf("'", i + 1);
			const end = close < 0 ? n : close;
			cur += src.slice(i + 1, end);
			has = true;
			i = end + 1;
		} else if (c === '"') {
			has = true;
			i++;
			while (i < n && src[i] !== '"') {
				if (src[i] === "\\" && i + 1 < n) {
					const next = src[i + 1];
					cur += '"\\$`'.includes(next) ? next : src[i] + next;
					i += 2;
				} else if (src[i] === "$" && src[i + 1] === "(") i = substitution(readSubstitution(src, i + 2));
				else if (src[i] === "`") i = substitution(readBackticks(src, i + 1));
				else cur += src[i++];
			}
			i++;
		} else if (c === "$" && src[i + 1] === "(") i = substitution(readSubstitution(src, i + 2));
		else if (c === "`") i = substitution(readBackticks(src, i + 1));
		else if (c === "#" && !has) {
			while (i < n && src[i] !== "\n") i++;
		} else if (c === "<" && src[i + 1] === "<" && src[i + 2] !== "<") {
			endWord();
			i += 2;
			const dash = src[i] === "-";
			if (dash) i++;
			while (src[i] === " " || src[i] === "\t") i++;
			let delim = "";
			while (i < n && !/[\s;&|()<>]/.test(src[i])) {
				if (src[i] !== "'" && src[i] !== '"' && src[i] !== "\\") delim += src[i];
				i++;
			}
			pending.push({ delim, dash });
		} else if (c === "\n") {
			endCommand();
			i++;
			for (const { delim, dash } of pending) {
				while (i < n) {
					const eol = src.indexOf("\n", i);
					const line = src.slice(i, eol < 0 ? n : eol);
					i = eol < 0 ? n : eol + 1;
					if ((dash ? line.replace(/^\t+/, "") : line) === delim) break;
				}
			}
			pending = [];
		} else if (c === ";" || c === "&" || c === "|" || c === "(" || c === ")") {
			endCommand();
			i++;
		} else if (c === " " || c === "\t") {
			endWord();
			i++;
		} else {
			cur += c;
			has = true;
			i++;
		}
	}
	endCommand();
	return out;
}

const base = (word: string) => word.split("/").pop() ?? word;

/** Drops assignments and wrapper commands (sudo, env, xargs, …) so argv[0] is the command that runs. */
function stripWrappers(argv: string[]): string[] {
	let rest = argv;
	for (;;) {
		const head = rest[0];
		if (head === undefined) return rest;
		if (/^[A-Za-z_][A-Za-z0-9_]*=/.test(head)) {
			rest = rest.slice(1);
		} else if (WRAPPERS.has(base(head))) {
			rest = rest.slice(1);
			while (rest[0] !== undefined && (rest[0].startsWith("-") || /^\d+[smhd]?$/.test(rest[0]) || /^[A-Za-z_][A-Za-z0-9_]*=/.test(rest[0]))) {
				rest = rest.slice(1);
			}
		} else return rest;
	}
}

/** Every command that would run, with `bash -c "…"` and `eval …` bodies expanded. */
export function commandsOf(src: string, depth = 0): string[][] {
	const result: string[][] = [];
	if (depth > MAX_DEPTH) return result;
	for (const raw of simpleCommands(src)) {
		const argv = stripWrappers(raw);
		if (argv.length === 0) continue;
		result.push(argv);
		const name = base(argv[0]);
		if (name === "eval") result.push(...commandsOf(argv.slice(1).join(" "), depth + 1));
		else if (SHELLS.has(name)) {
			const flag = argv.findIndex((w, k) => k > 0 && /^-[a-zA-Z]*c[a-zA-Z]*$/.test(w));
			if (flag > 0 && argv[flag + 1] !== undefined) result.push(...commandsOf(argv[flag + 1], depth + 1));
		}
	}
	return result;
}

const HOME = homedir();
const PROTECTED = [".gradle", "Library", ".android"].map(dir => posix.join(HOME, dir));

function globToRegExp(glob: string): RegExp {
	const body = glob.replace(/[.+^${}()|\\]/g, "\\$&").replace(/\*/g, ".*").replace(/\?/g, ".");
	return new RegExp(`^${body}$`);
}

/** True when `raw` names (or contains, or is an ancestor of) a protected cache directory. */
export function isProtectedPath(raw: string, home = HOME, protectedDirs = PROTECTED): boolean {
	let p = raw
		.replace(/^(?:\$\{?HOME\}?|~)(?=\/|$)/, home)
		.replace(/^\$\{?GRADLE_USER_HOME\}?(?=\/|$)/, posix.join(home, ".gradle"))
		.replace(/^\$\{?ANDROID_(?:USER_)?HOME\}?(?=\/|$)/, posix.join(home, ".android"));
	if (!p.startsWith("/")) return false;
	p = posix.normalize(p).replace(/\/+$/, "") || "/";
	const parts = p.split("/");
	const glob = parts.findIndex(part => /[*?[]/.test(part));
	if (glob >= 0) {
		const prefix = parts.slice(0, glob).join("/") || "/";
		const pattern = globToRegExp(parts[glob]);
		if (protectedDirs.some(dir => posix.dirname(dir) === prefix && pattern.test(posix.basename(dir)))) return true;
		p = prefix;
	}
	return protectedDirs.some(dir => p === dir || p.startsWith(`${dir}/`) || dir.startsWith(p === "/" ? "/" : `${p}/`));
}

function operands(args: string[]): string[] {
	const dashdash = args.indexOf("--");
	return args.filter((a, k) => (dashdash >= 0 && k > dashdash) || (!a.startsWith("-") && k !== dashdash));
}

function gitSubcommand(args: string[]): { sub: string; rest: string[] } | undefined {
	for (let k = 0; k < args.length; k++) {
		const a = args[k];
		if (GLOBAL_GIT_OPTS_WITH_VALUE.has(a)) k++;
		else if (!a.startsWith("-")) return { sub: a, rest: args.slice(k + 1) };
	}
	return undefined;
}

export interface Violation {
	rule: "kill" | "gradle-stop" | "git-add" | "rm-cache" | "yes-pipe";
	reason: string;
}

const REASONS: Record<Violation["rule"], string> = {
	kill:
		"worker-guard: killing Gradle, Java or build-slot processes by name also kills every other lane's builds on this machine. " +
		"Wait for your own build (the build-slot queue runs them in turn; a hook adds the build-slot prefix, so seeing it in " +
		"your command is expected); if one hangs, report BLOCKED with the log path instead of killing it. " +
		"See skill://implement/references/hard-rules.md.",
	"gradle-stop":
		"worker-guard: `gradlew --stop` stops the Gradle daemons of every lane, not only yours. Let your build " +
		"finish (daemons are reused on purpose); if it hangs, report BLOCKED with the log path. " +
		"See skill://implement/references/hard-rules.md.",
	"git-add":
		"worker-guard: blind staging (`git add -A`, `--all`, `.`) swept in other work and once reverted another PR's " +
		"change. Stage explicit paths: `git status --short`, then `git add path/a path/b` (use `git add -u` only " +
		"for already-tracked edits). See skill://implement/references/hard-rules.md.",
	"rm-cache":
		"worker-guard: ~/.gradle, ~/Library and ~/.android are shared by every lane; deleting them breaks other " +
		"builds. Delete only inside your own worktree (`rm -rf build .gradle` with relative paths). Disk full or " +
		"short on space: report BLOCKED, never free space yourself. See skill://implement/references/hard-rules.md.",
	"yes-pipe":
		"worker-guard: `yes | cmd` never ends on its own and is left spinning at full CPU when its reader hangs or the shell " +
		"is cut off (orphaned `yes` processes slowed the merge lane). Use the command's non-interactive flag instead " +
		"(`--yes`, `-y`, `--assume-yes`, `--non-interactive`, `sdkmanager --licenses` with licenses pre-accepted); " +
		"if it has none, feed a finite input (`printf 'y\\n' | cmd`) or report BLOCKED. Never clean up with pkill/killall: " +
		"stop only processes you started, by pid. See skill://implement/references/hard-rules.md.",
};

export function findViolations(command: string): Violation[] {
	const found = new Set<Violation["rule"]>();
	const cmds = commandsOf(command);
	const killsByPid = cmds.some(c => base(c[0]) === "kill");
	for (const argv of cmds) {
		const name = base(argv[0]);
		const args = argv.slice(1);
		if ((name === "pkill" || name === "killall") && args.some(a => TARGET.test(a))) found.add("kill");
		if (killsByPid && (name === "jps" || (PROCESS_LISTERS.has(name) && args.some(a => TARGET.test(a))))) found.add("kill");
		if (name === "yes") found.add("yes-pipe");
		if (/^gradlew?(?:\.bat)?$/.test(name) && args.includes("--stop")) found.add("gradle-stop");
		if (name === "git") {
			const git = gitSubcommand(args);
			if (git && (git.sub === "add" || git.sub === "stage")) {
				const afterDashes = git.rest.indexOf("--");
				const blind = git.rest.some((a, k) =>
					(afterDashes < 0 || k < afterDashes) && (a === "--all" || /^-[a-zA-Z]*A[a-zA-Z]*$/.test(a)),
				) || operands(git.rest).some(a => a === "." || a === "./" || a === ":/");
				if (blind) found.add("git-add");
			}
		}
		if (name === "rm" || name === "unlink" || name === "trash") {
			if (operands(args).some(a => isProtectedPath(a))) found.add("rm-cache");
		} else if (name === "find") {
			const roots: string[] = [];
			for (const a of args) {
				if (a.startsWith("-") || a === "(" || a === "!") break;
				roots.push(a);
			}
			if (args.some(a => a === "-delete" || a === "-exec" || a === "-execdir" || a === "-ok") && roots.some(a => isProtectedPath(a))) {
				found.add("rm-cache");
			}
		}
	}
	return [...found].map(rule => ({ rule, reason: REASONS[rule] }));
}

export default function workerGuard(pi: ExtensionAPI): void {
	let warned = false;
	pi.on("tool_call", async event => {
		if (event.toolName !== "bash") return;
		const input = (event.input ?? {}) as Record<string, unknown>;
		const command = typeof input.command === "string" ? input.command : undefined;
		if (!command) return;
		// Fail open: a parser bug must never block every bash call.
		let violations: Violation[];
		try {
			violations = findViolations(command);
		} catch (error) {
			if (!warned) {
				warned = true;
				console.error("worker-guard: parser error, failing open:", error);
			}
			return;
		}
		if (violations.length > 0) return { block: true, reason: violations.map(v => v.reason).join(" ") };
	});
}
