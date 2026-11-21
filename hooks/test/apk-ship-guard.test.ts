// Run: bun test hooks/
import { describe, expect, test } from "bun:test";
import { badAdbInstalls, rawTaildrop } from "../pre/apk-ship-guard";

// Assembled at runtime so this file never trips the guard it tests.
const taildrop = (rest: string) => `${["tail", "scale"].join("")} file ${rest}`;

describe("rawTaildrop", () => {
	test("refuses a raw copy", () => expect(rawTaildrop(taildrop("cp app.apk tab:"))).toBe(true));
	test("refuses the long spelling", () => expect(rawTaildrop(`cd x && ${taildrop("copy a.apk tab:")}`)).toBe(true));
	test("allows listing targets", () => expect(rawTaildrop(taildrop("cp --targets"))).toBe(false));
	test("allows ship_apk.py", () => expect(rawTaildrop("python3 ~/.agents/skills/deliver/scripts/ship_apk.py --slug x")).toBe(false));
});

describe("badAdbInstalls", () => {
	test("allows a canonical name", () => expect(badAdbInstalls("adb install -r out/PuzzleBox-0.24.0-navuc.9-1073-debug.apk")).toEqual([]));
	test("allows the allocated variable", () => expect(badAdbInstalls('adb install -r "$APK_PATH"')).toEqual([]));
	test("refuses Gradle's default name", () =>
		expect(badAdbInstalls("adb -s emu install -r app/build/outputs/apk/debug/app-debug.apk")).toEqual(["app/build/outputs/apk/debug/app-debug.apk"]));
	test("refuses an unallocated variable", () => expect(badAdbInstalls("adb install $APK")).toEqual(["$APK"]));
});
