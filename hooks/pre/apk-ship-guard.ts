// APK ship guard (user ruling 2026-11-11).
// Every APK that reaches a device must carry its build identity: allocated by
// deliver's build_identity.py, built with $GRADLE_ARGS, named
// <AppName>-<versionName>-<code>-<debug|release>.apk.
//  1. Raw `tailscale file cp` from agent bash/eval is refused once
//     deliver/scripts/ship_apk.py exists; that script is the only Taildrop path
//     (it calls tailscale itself, so it never passes through this hook).
//  2. `adb install` of an APK whose file name is not canonical is refused.
import type { ExtensionAPI } from "@oh-my-pi/pi-coding-agent";
import { existsSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const SHIP_SCRIPT = join(homedir(), ".agents/skills/deliver/scripts/ship_apk.py");
const TAILSCALE_CP = /\btailscale\s+file\s+(?:cp|copy)\b(?![^\n;&|]*--targets\b)/;
const ADB_INSTALL = /\badb\b[^\n;&|]*?\binstall(?:-multiple)?\b([^\n;&|]*)/g;
const CANONICAL = /^[A-Za-z0-9_.]+-\d+\.\d+\.\d+(?:-[a-z0-9][a-z0-9-]*\.\d+)?-\d+-(?:debug|release)\.apk$/;
const ALLOCATED_VAR = /^\$\{?APK_(?:NAME|PATH)\}?$/;

function commandText(toolName: string, input: Record<string, unknown>): string | undefined {
	if (toolName === "bash") return String(input.command ?? "");
	if (toolName === "eval") return String(input.code ?? "");
	return undefined;
}

/**
 * Returns the APK operands of every `adb install` in `text` that are not canonical.
 * Only tokens that name an APK (`*.apk`) or are a bare `$VAR` are judged; anything else
 * (code around a quoted command, flags, serials) is ignored.
 */
export function badAdbInstalls(text: string): string[] {
	const bad: string[] = [];
	for (const match of text.matchAll(ADB_INSTALL)) {
		for (const raw of match[1].split(/\s+/)) {
			const operand = raw.replace(/^["'(\[]+|["'),\]]+$/g, "");
			if (!operand || operand.startsWith("-")) continue;
			const base = operand.split("/").pop() ?? operand;
			if (/\.apk$/i.test(base)) {
				if (!CANONICAL.test(base)) bad.push(operand);
			} else if (/^\$\{?\w+\}?$/.test(base) && !ALLOCATED_VAR.test(base)) {
				bad.push(operand);
			}
		}
	}
	return bad;
}

export function rawTaildrop(text: string): boolean {
	return TAILSCALE_CP.test(text);
}

export default function apkShipGuard(pi: ExtensionAPI): void {
	pi.on("tool_call", async event => {
		const text = commandText(event.toolName, (event.input ?? {}) as Record<string, unknown>);
		if (!text) return;

		if (rawTaildrop(text) && existsSync(SHIP_SCRIPT)) {
			return {
				block: true,
				reason:
					"apk-ship-guard: raw `tailscale file cp` is not allowed. Ship APKs only with " +
					"`python3 ~/.agents/skills/deliver/scripts/ship_apk.py` (allocates the build identity, builds, " +
					"verifies the APK's versionName/versionCode, names it canonically, sends it to the PROFILE device, " +
					"records evidence). See skill://deliver.",
			};
		}

		const bad = badAdbInstalls(text);
		if (bad.length > 0) {
			return {
				block: true,
				reason:
					`apk-ship-guard: adb install of non-canonical APK ${bad.join(", ")}. Build with ` +
					"`eval \"$(python3 ~/.agents/skills/deliver/scripts/ship_apk.py --build-only)\"`, then " +
					"`adb install -r \"$APK_PATH\"`. Only canonical names install: " +
					"<AppName>-<versionName>-<code>-<debug|release>.apk (e.g. PuzzleBox-0.24.0-navuc.9-1073-debug.apk). " +
					"Never install Gradle's app-<variant>.apk. See skill://deliver/references/build-identity.md.",
			};
		}
	});
}
