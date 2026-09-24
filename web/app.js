import { GOVT_TYPES, lookup, predict, resultStats } from "./engine.js";

const $ = (id) => document.getElementById(id);
const COLS = [["stream", "Stream"], ["course", "Course"], ["college", "College"], ["type", "Type"], ["route", "Route"],
  ["chance", "Chance"], ["earliestRound", "Earliest round"], ["fee", "Fee / yr"], ["reason", "Reason"]];
const fmt = (n, d = 2) => n.toLocaleString("en-IN", { maximumFractionDigits: d });
const fee = (f) => (f == null ? "" : `₹${fmt(f / 1e5, 1)} L`);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

let data, candidate, options = [];

async function load() {
  const get = (f) => fetch(`data/${f}`).then((r) => { if (!r.ok) throw new Error(f); return r.json(); });
  const [results, meritMap, gujarat, mcc] = await Promise.all(
    ["results.json", "merit_map.json", "gujarat.json", "mcc.json"].map(get));
  data = { results, meritMap, gujarat, mcc };
  $("loading").hidden = true;
  $("form").hidden = false;
}

function showResult(e) {
  e.preventDefault();
  $("error").textContent = "";
  $("prediction").hidden = true;
  candidate = lookup($("app").value, data.results);
  if (!candidate) {
    $("result").hidden = $("predict").hidden = true;
    $("error").textContent = "Application number not found in the NEET-PG 2026 result.";
    return;
  }
  const s = resultStats(candidate, data.results.stats);
  const card = (k, v) => `<div class="card">${k}<b>${v}</b></div>`;
  $("result").innerHTML = `<h2>${esc(candidate.appNo)} · Roll ${esc(candidate.roll)}</h2>` + (s.status !== "OK"
    ? `<p>Status: <b>${esc(s.status)}</b>. No prediction available.</p>`
    : `<div class="cards">${[
        card("Score (out of 720)", candidate.score), card("All India Rank", fmt(candidate.rank, 0)),
        card("Percentile (≤ score)", fmt(s.percentileLE, 4)), card("Percentile (< score)", fmt(s.percentileLT, 4)),
        card("Percentile (mid-rank)", fmt(s.percentileMid, 4)), card("Percentile (from rank)", fmt(s.percentileRank, 4)),
        card("Top %", fmt(s.topPercent, 3)), card("Candidates ahead", fmt(s.ahead, 0)),
        card("Same score", fmt(s.sameScore, 0))].join("")}</div>`);
  $("result").hidden = false;
  $("predict").hidden = s.status !== "OK";
}

function showPrediction() {
  const category = $("category").value, domicile = $("domicile").checked;
  const p = predict({ rank: candidate.rank, category, domicile }, data);
  options = p.options;
  const m = p.merit;
  $("merit").innerHTML = `<h2>Predicted Gujarat merit</h2><p>General merit <b>~${m.general}</b>` +
    (m.category != null ? ` · ${category} merit <b>~${m.category}</b>` : "") +
    `</p><p class="disclaimer">AIR ${fmt(candidate.rank, 0)} placed between the candidates around it in the 2025 Gujarat merit lists.` +
    (m.extrapolated ? " Your rank is beyond the 2025 list, so this is extrapolated and less reliable." : "") +
    (domicile ? "" : " Without Gujarat domicile only MCC seats in Gujarat colleges are shown.") + "</p>";
  $("insights").innerHTML = `<table><thead><tr><th>Stream</th><th>Govt options</th><th>Private/other</th>
    <th>Best Govt options</th><th>Fee range</th></tr></thead><tbody>${p.insights.map((i) => `<tr>
    <td>${esc(i.stream)}</td><td>${i.govtReachable}</td><td>${i.privateReachable}</td>
    <td>${esc(i.topGovt.join("; ") || (i.closestMiss ? `None. Closest: ${i.closestMiss}` : "None"))}</td>
    <td>${i.feeMin == null ? "" : `${fee(i.feeMin)} – ${fee(i.feeMax)}`}</td></tr>`).join("")}</tbody></table>`;
  fillFilter("f-stream", options.map((o) => o.stream));
  fillFilter("f-type", options.map((o) => o.type));
  fillFilter("f-route", options.map((o) => o.route));
  $("prediction").hidden = false;
  renderTable();
}

function fillFilter(id, values) {
  const sel = $(id), first = sel.options[0];
  sel.replaceChildren(first, ...[...new Set(values)].sort().map((v) => new Option(v, v)));
}

function filtered() {
  const [st, ty, ro, ch] = ["f-stream", "f-type", "f-route", "f-chance"].map((id) => $(id).value);
  return options.filter((o) => (!st || o.stream === st) && (!ty || o.type === ty) && (!ro || o.route === ro)
    && (!ch || (ch === "reach" ? ["High", "Good", "Borderline"].includes(o.chance) : o.chance === ch)));
}

function renderTable() {
  const rows = filtered();
  $("count").textContent = `${rows.length} options (${rows.filter((o) => GOVT_TYPES.has(o.type)).length} Govt-type)`;
  $("table").tHead.innerHTML = `<tr>${COLS.map(([, h]) => `<th>${h}</th>`).join("")}</tr>`;
  $("table").tBodies[0].innerHTML = rows.map((o) => `<tr>${COLS.map(([k]) => `<td${k === "chance" ? ` class="${o.chance}"` : ""}>${
    esc(k === "fee" ? fee(o.fee) : k === "earliestRound" ? (o.earliestRound ? `Round ${o.earliestRound}` : "") : o[k])}</td>`).join("")}</tr>`).join("");
}

function downloadCsv() {
  const cell = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const csv = [COLS.map(([, h]) => cell(h)).join(","), ...filtered().map((o) => COLS.map(([k]) => cell(o[k])).join(","))].join("\n");
  const a = Object.assign(document.createElement("a"), {
    href: URL.createObjectURL(new Blob([csv], { type: "text/csv" })), download: `${candidate.appNo}-gujarat-options.csv` });
  a.click();
  URL.revokeObjectURL(a.href);
}

$("form").addEventListener("submit", showResult);
$("predict").addEventListener("click", showPrediction);
["f-stream", "f-type", "f-route", "f-chance"].forEach((id) => $(id).addEventListener("change", renderTable));
$("csv").addEventListener("click", downloadCsv);
load().catch((err) => { $("loading").textContent = `Could not load data (${err.message}). Run: .venv/bin/python -m pipeline.build`; });
