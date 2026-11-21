// Claude Code adapter for the omp pre-hooks in ../pre (Orca bots trial, 2026-11-21).
// Each hooks/claude/<name>.ts entry runs one omp hook unchanged as a Claude Code `PreToolUse`
// command hook (matcher `Bash`), so the rules live in one place and omp keeps loading ../pre as before.
// Translation:
//  - stdin `{tool_name: "Bash", tool_input, cwd}` → the omp event `{toolName: "bash", input: tool_input}`.
//  - omp `{block: true, reason}` → `permissionDecision: "deny"` with the reason (Claude sees it).
//  - omp `{input}` (build-queue rewrite) → `updatedInput` with no `permissionDecision`, so the rewritten
//    command still goes through the session's normal permission flow instead of being auto-approved.
//  - anything else → no output, exit 0 (no opinion).
// Fails open like the omp hooks: unreadable stdin or a hook error never blocks the Bash call.
import type { ExtensionAPI } from "@oh-my-pi/pi-coding-agent";

type OmpEvent = { toolName: string; input: Record<string, unknown> };
type OmpResult = { block?: boolean; reason?: string; input?: Record<string, unknown> } | undefined;
type OmpHandler = (event: OmpEvent) => unknown;
export type OmpHook = (pi: ExtensionAPI) => void;

export interface PreToolUsePayload {
	tool_name?: string;
	tool_input?: Record<string, unknown>;
	cwd?: string;
}

export interface PreToolUseOutput {
	hookSpecificOutput: {
		hookEventName: "PreToolUse";
		permissionDecision?: "deny";
		permissionDecisionReason?: string;
		updatedInput?: Record<string, unknown>;
	};
}

/** Runs `hook`'s tool_call handlers on a Claude Code PreToolUse payload; undefined = no opinion. */
export async function decide(hook: OmpHook, payload: PreToolUsePayload): Promise<PreToolUseOutput | undefined> {
	if (payload.tool_name !== "Bash") return undefined;
	const handlers: OmpHandler[] = [];
	hook({ on: (name: string, fn: OmpHandler) => { if (name === "tool_call") handlers.push(fn); } } as unknown as ExtensionAPI);
	const input = payload.tool_input ?? {};
	for (const handler of handlers) {
		const result = (await handler({ toolName: "bash", input })) as OmpResult;
		if (result?.block) {
			return { hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "deny", permissionDecisionReason: result.reason ?? "blocked" } };
		}
		if (result?.input) return { hookSpecificOutput: { hookEventName: "PreToolUse", updatedInput: result.input } };
	}
	return undefined;
}

/** Entry point for hooks/claude/<name>.ts: stdin payload in, decision JSON out, always exit 0. */
export async function runClaudeHook(hook: OmpHook): Promise<void> {
	try {
		const payload = JSON.parse(await Bun.stdin.text()) as PreToolUsePayload;
		// Claude Code runs hooks in its own cwd; follow the session's shell so git-based guards see the right repo.
		if (typeof payload.cwd === "string") {
			try { process.chdir(payload.cwd); } catch { /* keep the hook's cwd */ }
		}
		const output = await decide(hook, payload);
		if (output) process.stdout.write(`${JSON.stringify(output)}\n`);
	} catch (error) {
		console.error("claude hook adapter: error, failing open:", error);
	}
}
