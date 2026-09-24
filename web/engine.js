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
