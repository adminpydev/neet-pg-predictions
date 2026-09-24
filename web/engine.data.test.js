import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { predict } from "./engine.js";

const dir = new URL("./data/", import.meta.url);
const load = (f) => JSON.parse(readFileSync(new URL(f, dir)));
const built = existsSync(new URL("gujarat.json", dir));

test("AIR 8839 SEBC Gujarat matches the manual report", { skip: !built && "run pipeline.build first" }, () => {
  // reference candidate found by rank so no real application number lives in the repo
  const cand = { rank: Object.values(load("results.json").rows).find((r) => r[2] === 8839)[2] };
  const data = { meritMap: load("merit_map.json"), gujarat: load("gujarat.json"), mcc: load("mcc.json") };
  const { merit, options } = predict({ rank: cand.rank, category: "SEBC", domicile: true }, data);
  assert.deepEqual(merit, { general: 510, category: 99, extrapolated: false });
  const find = (college, stream) => options.find((o) => o.college.startsWith(college) && o.stream === stream
    && o.route === "Gujarat State - Govt Quota" && o.degree === "MD");
  const smimer = find("Surat Municipal", "Dermatology");
  assert.equal(smimer.chance, "High");
  assert.equal(smimer.earliestRound, 1);
  assert.equal(find("B. J. Medical", "Radio-Diagnosis").chance, "Low");
});
