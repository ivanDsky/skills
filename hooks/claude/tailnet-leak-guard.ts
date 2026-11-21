// Claude Code PreToolUse (Bash) entry for ../pre/tailnet-leak-guard.ts; the behaviour and its limits live there.
import hook from "../pre/tailnet-leak-guard";
import { runClaudeHook } from "./adapter";

if (import.meta.main) await runClaudeHook(hook);
