// Claude Code PreToolUse (Bash) entry for ../pre/worker-guard.ts; the behaviour and its limits live there.
import hook from "../pre/worker-guard";
import { runClaudeHook } from "./adapter";

if (import.meta.main) await runClaudeHook(hook);
