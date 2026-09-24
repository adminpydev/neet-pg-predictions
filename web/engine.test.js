import { test } from "node:test";
import assert from "node:assert/strict";
import { lookup, normalizeAppNo, resultStats } from "./engine.js";

const results = {
  rows: { PG1: ["R1", 300, 2, "OK"], PG2: ["R2", 200, 3, "OK"], PG3: ["R3", 300, 1, "OK"], PG4: ["R4", null, null, "ABSENT"] },
  stats: { appeared: 3, maxRank: 3, hist: { 300: 2, 200: 1 } },
};

test("normalizeAppNo trims spaces and upper-cases", () => {
  assert.equal(normalizeAppNo("  pg 26114274 "), "PG26114274");
});

test("lookup finds candidate or returns null", () => {
  assert.deepEqual(lookup(" pg1", results), { appNo: "PG1", roll: "R1", score: 300, rank: 2, status: "OK" });
  assert.equal(lookup("PG999", results), null);
});

test("resultStats computes percentiles", () => {
  const s = resultStats(lookup("PG1", results), results.stats);
  assert.equal(s.status, "OK");
  assert.equal(s.percentileLE, 100);
  assert.ok(Math.abs(s.percentileLT - 100 / 3) < 1e-9);
  assert.ok(Math.abs(s.percentileMid - 200 / 3) < 1e-9);
  assert.equal(s.percentileRank, 50);
  assert.ok(Math.abs(s.topPercent - 200 / 3) < 1e-9);
  assert.equal(s.ahead, 0);
  assert.equal(s.sameScore, 2);
});

test("resultStats for absent candidate returns only status", () => {
  assert.deepEqual(resultStats(lookup("PG4", results), results.stats), { status: "ABSENT" });
});

import { estimateMerit } from "./engine.js";

const meritMap = {
  GEN: [[17, 1], [8824, 510], [8880, 511], [9000, 520]],
  SEBC: [[133, 1], [8723, 98], [8916, 99]],
};

test("estimateMerit interpolates between 2025 points", () => {
  assert.deepEqual(estimateMerit(8839, "SEBC", meritMap), { general: 510, category: 99, extrapolated: false });
});

test("estimateMerit for GEN has no category merit", () => {
  assert.deepEqual(estimateMerit(8839, "GEN", meritMap), { general: 510, category: null, extrapolated: false });
});

test("estimateMerit beyond list range extrapolates without NaN", () => {
  const m = estimateMerit(20000, "SEBC", meritMap);
  assert.equal(m.extrapolated, true);
  assert.ok(Number.isFinite(m.general) && Number.isFinite(m.category));
  assert.ok(m.category > 99);
});

test("estimateMerit never returns merit below 1", () => {
  assert.equal(estimateMerit(1, "GEN", meritMap).general, 1);
});
