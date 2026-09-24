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

import { gujaratOptions, label, mccOptions } from "./engine.js";

const merit = { general: 510, category: 99, extrapolated: false };
const guj = (last, extra = {}) => ({ code: "X", college: "College X", type: "Govt", course: "Dermatology",
  stream: "Dermatology", degree: "MD", seat: "GQ", fee: 130800, seats: 2, last, ...extra });

test("label thresholds", () => {
  assert.deepEqual([1.15, 1, 0.9, 0.89].map(label), ["High", "Good", "Borderline", "Low"]);
});

test("SEBC candidate reaches seat via SEBC merit in round 1", () => {
  const [o] = gujaratOptions(merit, "SEBC", [guj({ 1: { OPEN: 100, SEBC: 132 }, 2: { SEBC: 156 } })]);
  assert.equal(o.chance, "High");
  assert.equal(o.earliestRound, 1);
  assert.equal(o.route, "Gujarat State - Govt Quota");
  assert.match(o.reason, /SEBC merit 156/);
});

test("far-away seat is Low", () => {
  const [o] = gujaratOptions(merit, "SEBC", [guj({ 1: { OPEN: 28, SEBC: 14 }, 4: { OPEN: 70, SEBC: 20 } })]);
  assert.equal(o.chance, "Low");
  assert.equal(o.earliestRound, null);
});

test("GEN candidate is never matched on a category column", () => {
  const [o] = gujaratOptions({ general: 510, category: null }, "GEN", [guj({ 1: { OPEN: 100, SEBC: 9999 } })]);
  assert.equal(o.chance, "Low");
});

test("management quota uses OPEN only", () => {
  const [o] = gujaratOptions(merit, "SEBC", [guj({ 1: { OPEN: 600, SEBC: 5 } }, { seat: "MQ", type: "Private" })]);
  assert.equal(o.chance, "High");
  assert.equal(o.route, "Gujarat State - Management Quota");
});

test("vacant seat (99999) is reachable", () => {
  const [o] = gujaratOptions(merit, "SEBC", [guj({ 3: { OPEN: 99999 } })]);
  assert.equal(o.chance, "High");
  assert.equal(o.earliestRound, 3);
  assert.match(o.reason, /vacant/);
});

test("rounds missing the candidate's column give Unknown, not NaN", () => {
  const [o] = gujaratOptions(merit, "ST", [guj({ 1: { SEBC: 50 } })]);
  assert.equal(o.chance, "Unknown");
  assert.equal(o.ratio, null);
});

test("mccOptions uses last rank for the candidate's category", () => {
  const rec = { college: "B. J. Medical College", stream: "General Surgery", course: "M.S. (GENERAL SURGERY)",
    degree: "MS", quota: "All India 50%", sector: "Govt", rounds: ["2024 R3"],
    last: { GEN: 8000, EWS: null, SEBC: 10500, SC: 20000, ST: null } };
  const [o] = mccOptions(8839, "SEBC", [rec]);
  assert.equal(o.chance, "High");
  assert.equal(o.route, "MCC - All India 50%");
  assert.match(o.reason, /10500/);
  assert.equal(mccOptions(8839, "ST", [rec])[0].chance, "Unknown");
});
