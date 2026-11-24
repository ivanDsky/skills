// Claude Code PreToolUse (Bash) entry for ../pre/build-queue.ts; the behaviour and its limits live there.
import hook from "../pre/build-queue";
import { runClaudeHook } from "./adapter";

if (import.meta.main) await runClaudeHook(hook);
