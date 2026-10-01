import { describe, expect, it } from "vitest";

import { settleVerse } from "../src/reader/core";
import { recordingChanged, type RecordingIdentity } from "../src/reader/player-logic";

const alafasy: RecordingIdentity = {
  scriptId: "hafs",
  reciter: { id: "ar.alafasy", url: "https://host/{ayah}.mp3" },
};

describe("recording identity", () => {
  it("keeps playing when nothing is loaded or nothing changed", () => {
    expect(recordingChanged(null, alafasy)).toBe(false);
    expect(recordingChanged(alafasy, { ...alafasy })).toBe(false);
  });

  it("stops when the reciter changes", () => {
    const other = { scriptId: "hafs", reciter: { id: "ar.husary", url: alafasy.reciter!.url } };

    expect(recordingChanged(alafasy, other)).toBe(true);
  });

  it("stops when the URL template of the same reciter changes", () => {
    const moved = { scriptId: "hafs", reciter: { id: "ar.alafasy", url: "https://other/{ayah}" } };

    expect(recordingChanged(alafasy, moved)).toBe(true);
  });

  it("stops when the script changes, and when the reciter is cleared", () => {
    expect(recordingChanged(alafasy, { ...alafasy, scriptId: "warsh" })).toBe(true);
    expect(recordingChanged(alafasy, { scriptId: "hafs", reciter: null })).toBe(true);
  });
});

describe("linked verse", () => {
  it("drops a verse the chapter does not have", () => {
    expect(settleVerse(999, 286)).toBeNull();
    expect(settleVerse(0, 286)).toBeNull();
  });

  it("keeps a verse that exists, and no verse", () => {
    expect(settleVerse(255, 286)).toBe(255);
    expect(settleVerse(null, 286)).toBeNull();
  });

  it("revalidates against the new script: Duri 67:31 is not in Hafs 67", () => {
    expect(settleVerse(31, 31)).toBe(31);
    expect(settleVerse(31, 30)).toBeNull();
  });
});
