// Pure prediction logic. No DOM, no fetch: callers pass loaded data in.

export function normalizeAppNo(s) {
  return s.replace(/\s+/g, "").toUpperCase();
}

export function lookup(appNo, results) {
  const key = normalizeAppNo(appNo);
  const row = results.rows[key];
  if (!row) return null;
  const [roll, score, rank, status] = row;
  return { appNo: key, roll, score, rank, status };
}

export function resultStats(candidate, stats) {
  if (candidate.status !== "OK") return { status: candidate.status };
  const n = stats.appeared;
  let le = 0;
  for (const [score, count] of Object.entries(stats.hist)) if (Number(score) <= candidate.score) le += count;
  const same = stats.hist[candidate.score];
  const lt = le - same;
  return {
    status: "OK",
    percentileLE: (le / n) * 100,
    percentileLT: (lt / n) * 100,
    percentileMid: ((lt + same / 2) / n) * 100,
    percentileRank: ((stats.maxRank - candidate.rank) / (stats.maxRank - 1)) * 100,
    topPercent: ((n - lt) / n) * 100,
    ahead: n - le,
    sameScore: same,
  };
}

// points: [[air, merit], ...] sorted by air. Returns [merit, extrapolated].
function interpolate(points, rank) {
  const first = points[0], last = points[points.length - 1];
  if (rank <= first[0]) return [Math.max(1, Math.round((first[1] * rank) / first[0])), false];
  if (rank > last[0]) return [Math.round((last[1] * rank) / last[0]), true];
  for (let i = 1; i < points.length; i++) {
    const [a1, m1] = points[i - 1], [a2, m2] = points[i];
    if (rank <= a2) return [Math.round(m1 + ((rank - a1) / (a2 - a1)) * (m2 - m1)), false];
  }
}

export function estimateMerit(rank, category, meritMap) {
  const [general, extraG] = interpolate(meritMap.GEN, rank);
  if (category === "GEN") return { general, category: null, extrapolated: extraG };
  const [cat, extraC] = interpolate(meritMap[category], rank);
  return { general, category: cat, extrapolated: extraG || extraC };
}

export const VACANT = 99999;

export function label(ratio) {
  if (ratio >= 1.15) return "High";
  if (ratio >= 1) return "Good";
  if (ratio >= 0.9) return "Borderline";
  return "Low";
}

export function gujaratOptions(merit, category, records) {
  return records.map((rec) => {
    // [label, column, candidate merit] for each merit column the candidate competes on
    const cols = [["Open", "OPEN", merit.general]];
    if (rec.seat === "GQ" && category !== "GEN") cols.push([category, category, merit.category]);
    let best = null, earliest = null;
    for (const [round, vals] of Object.entries(rec.last)) {
      for (const [lab, col, mine] of cols) {
        const value = vals[col];
        if (value == null || mine == null) continue;
        const ratio = value === VACANT ? Infinity : value / mine;
        if (ratio >= 1 && earliest === null) earliest = Number(round);
        if (!best || ratio > best.ratio) best = { ratio, round, lab, value, mine };
      }
    }
    const perRound = cols.map(([lab, col]) => [lab, Object.entries(rec.last).filter(([, v]) => v[col] != null)
      .map(([round, v]) => `R${round} ${v[col] === VACANT ? "vacant" : v[col]}`).join(" · ")])
      .filter(([, txt]) => txt).map(([lab, txt]) => `${lab} ${txt}`).join("; ");
    const reason = !best ? "No 2025 data for your category"
      : (best.value === VACANT ? `Round ${best.round} 2025: seat went vacant`
        : `Round ${best.round} 2025 last ${best.lab} merit ${best.value}; your ${best.lab} merit ~${best.mine}`)
        + ` (${perRound})`;
    return {
      stream: rec.stream, course: rec.course, degree: rec.degree, college: rec.college, type: rec.type,
      route: rec.seat === "GQ" ? "Gujarat State - Govt Quota" : "Gujarat State - Management Quota",
      chance: best ? label(best.ratio) : "Unknown", ratio: best ? best.ratio : null,
      earliestRound: earliest, fee: rec.fee, reason,
    };
  });
}

// Chance comes from 2024 main rounds (R1-R3); the 2025 stray round is used only when those are missing.
export function mccOptions(rank, category, records) {
  return records.map((rec) => {
    const main = rec.last[category], stray = rec.strayLast[category];
    const last = main ?? stray;
    const ratio = last == null ? null : last / rank;
    const parts = [];
    if (main != null) parts.push(`MCC 2024 R1-R3 last AIR ${main}`);
    if (stray != null) parts.push(main != null ? `2025 stray last ${stray}` : `MCC 2025 stray last AIR ${stray}`);
    return {
      stream: rec.stream, course: rec.course, degree: rec.degree, college: rec.college, type: rec.sector,
      route: `MCC - ${rec.quota}`, chance: ratio == null ? "Unknown" : label(ratio), ratio,
      earliestRound: null, fee: null,
      reason: last == null ? "No MCC allotment data for your category" : [...parts, `your AIR ${rank}`].join("; "),
    };
  });
}

export const GOVT_TYPES = new Set(["Govt", "Municipal (Govt)", "GMERS (Govt society)"]);
const REACHABLE = new Set(["High", "Good", "Borderline"]);
const CHANCE_ORDER = { High: 0, Good: 1, Borderline: 2, Low: 3, Unknown: 4 };
const typeOrder = (t) => (GOVT_TYPES.has(t) ? 0 : t === "Private" ? 1 : 2);
const nameKey = (s) => s.toLowerCase().replace(/[^a-z0-9]/g, "");

export function insights(options) {
  const byStream = new Map();
  for (const o of options) {
    if (!byStream.has(o.stream)) byStream.set(o.stream, []);
    byStream.get(o.stream).push(o);
  }
  const out = [];
  for (const [stream, opts] of byStream) {
    const reach = opts.filter((o) => REACHABLE.has(o.chance));
    const govt = reach.filter((o) => GOVT_TYPES.has(o.type)).sort((a, b) => a.ratio - b.ratio);
    const seen = new Set();
    const topGovt = govt.filter((o) => !seen.has(nameKey(o.college)) && seen.add(nameKey(o.college)));
    const govtLow = opts.filter((o) => GOVT_TYPES.has(o.type) && o.chance === "Low").sort((a, b) => b.ratio - a.ratio);
    const fees = reach.map((o) => o.fee).filter((f) => f != null);
    out.push({
      stream, reachable: reach.length, govtReachable: govt.length,
      privateReachable: reach.filter((o) => !GOVT_TYPES.has(o.type)).length,
      topGovt: topGovt.slice(0, 3).map((o) => o.college),
      closestMiss: govt.length === 0 && govtLow.length ? `${govtLow[0].college}: ${govtLow[0].reason}` : null,
      feeMin: fees.length ? Math.min(...fees) : null, feeMax: fees.length ? Math.max(...fees) : null,
    });
  }
  return out.sort((a, b) => b.govtReachable - a.govtReachable);
}

export function predict({ rank, category, domicile }, data) {
  const merit = estimateMerit(rank, category, data.meritMap);
  const options = [
    ...(domicile ? gujaratOptions(merit, category, data.gujarat) : []),
    ...mccOptions(rank, category, data.mcc),
  ].sort((a, b) => typeOrder(a.type) - typeOrder(b.type) || CHANCE_ORDER[a.chance] - CHANCE_ORDER[b.chance]);
  return { merit, options, insights: insights(options) };
}
