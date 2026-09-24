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
