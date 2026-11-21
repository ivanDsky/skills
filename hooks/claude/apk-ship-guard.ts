// Claude Code PreToolUse (Bash) entry for ../pre/apk-ship-guard.ts; the behaviour and its limits live there.
// Claude Code has no eval tool, so only the Bash half of the omp hook applies.
import hook from "../pre/apk-ship-guard";
import { runClaudeHook } from "./adapter";

if (import.meta.main) await runClaudeHook(hook);
