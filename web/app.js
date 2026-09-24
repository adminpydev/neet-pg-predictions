import { GOVT_TYPES, lookup, predict, resultStats } from "./engine.js";

const $ = (id) => document.getElementById(id);
const COLS = [["stream", "Stream"], ["course", "Course"], ["college", "College"], ["type", "Type"], ["route", "Route"],
  ["chance", "Chance"], ["earliestRound", "Earliest round"], ["fee", "Fee / yr"], ["reason", "Reason"]];
const CHANCE_ICON = { High: "✓", Good: "↑", Borderline: "~", Low: "↓", Unknown: "?" };
const REACHABLE = new Set(["High", "Good", "Borderline"]);
const fmt = (n, d = 2) => n.toLocaleString("en-IN", { maximumFractionDigits: d });
const fee = (f) => (f == null ? "" : `₹${fmt(f / 1e5, 1)} L`);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const earliest = (o) => (o.earliestRound ? `Round ${o.earliestRound}` : "");

let data, candidate, options = [], pageSize = 30;

// --- generic reveal helpers ---
const reducedMotion = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
function reveal(section) {
  section.hidden = false;
  section.focus();
  section.scrollIntoView({ behavior: reducedMotion() ? "auto" : "smooth" });
}

// --- load + url params ---
async function load() {
  try {
    const get = (f) => fetch(`data/${f}`).then((r) => { if (!r.ok) throw new Error(f); return r.json(); });
    const [results, meritMap, gujarat, mcc] = await Promise.all(
      ["results.json", "merit_map.json", "gujarat.json", "mcc.json"].map(get));
    data = { results, meritMap, gujarat, mcc };
    $("loading").hidden = true;
    $("form").hidden = false;
    applyUrlParams();
  } catch (err) {
    console.error(err);
    $("loading").hidden = true;
    $("error").textContent = "Couldn't load the results data. Please refresh the page.";
  }
}

function applyUrlParams() {
  const qp = new URLSearchParams(location.search);
  const app = qp.get("app");
  if (!app) return;
  $("app").value = app;
  const cat = qp.get("cat");
  if (cat) for (const r of document.querySelectorAll('input[name="category"]')) r.checked = r.value === cat;
  if (qp.has("dom")) $("domicile").checked = qp.get("dom") !== "0";
  showResult();
  if (qp.get("predict") === "1" && !$("predict").hidden) showPrediction();
}

// --- result ---
function showResult() {
  $("error").textContent = "";
  $("prediction").hidden = true;
  candidate = lookup($("app").value, data.results);
  if (!candidate) {
    $("result").hidden = true;
    $("predict").hidden = true;
    $("error").textContent = "Application number not found in the NEET-PG 2026 result.";
    return;
  }
  renderResult(candidate, resultStats(candidate, data.results.stats));
  reveal($("result"));
}

function renderResult(c, s) {
  $("result").querySelector(".section-title").textContent = `${c.appNo} · Roll ${c.roll}`;
  const stats = $("result").querySelector(".stats"), more = $("result").querySelector(".more");
  const statusMsg = $("result").querySelector(".status-msg");
  $("predict").hidden = s.status !== "OK";
  if (s.status !== "OK") {
    stats.hidden = more.hidden = true;
    statusMsg.hidden = false;
    statusMsg.textContent = `Status: ${s.status}. No prediction available.`;
    return;
  }
  stats.hidden = more.hidden = false;
  statusMsg.hidden = true;
  const [scoreEl, rankEl, topEl] = stats.querySelectorAll(".stat-value");
  scoreEl.textContent = c.score;
  rankEl.textContent = fmt(c.rank, 0);
  topEl.textContent = `${fmt(s.topPercent, 2)}%`;
  const dds = more.querySelectorAll(".kv dd");
  dds[0].textContent = `${fmt(s.percentileLE, 2)}%`;
  dds[1].textContent = `${fmt(s.percentileLT, 2)}%`;
  dds[2].textContent = `${fmt(s.percentileMid, 2)}%`;
  dds[3].textContent = `${fmt(s.percentileRank, 2)}%`;
  dds[4].textContent = fmt(s.ahead, 0);
  dds[5].textContent = fmt(s.sameScore, 0);
}

// --- prediction: outlook + streams ---
function showPrediction() {
  const category = document.querySelector('input[name="category"]:checked').value;
  const domicile = $("domicile").checked;
  const p = predict({ rank: candidate.rank, category, domicile }, data);
  options = p.options;
  renderOutlook(p.merit, p.insights, category, domicile);
  renderStreams(p.insights);
  fillFilter("f-stream", options.map((o) => o.stream));
  fillFilter("f-type", options.map((o) => o.type));
  fillFilter("f-route", options.map((o) => o.route));
  resetToDefaultFilters();
  reveal($("prediction"));
  renderList();
}

function renderOutlook(merit, insights, category, domicile) {
  const govt = insights.reduce((sum, i) => sum + i.govtReachable, 0);
  const streamsWithGovt = insights.filter((i) => i.govtReachable > 0).length;
  const el = $("outlook");
  el.classList.remove("outlook--good", "outlook--none");
  el.classList.add(govt > 0 ? "outlook--good" : "outlook--none");
  el.querySelector(".outlook-verdict").textContent = govt > 0
    ? `Govt seats in reach in ${streamsWithGovt} branches`
    : "No Govt seats in reach — see private and All India options below";
  let meta = `Gujarat General merit ~${merit.general}`;
  if (merit.category != null) meta += ` · ${category} merit ~${merit.category}`;
  if (merit.extrapolated) meta += " Estimate extrapolated beyond 2025 lists.";
  if (!domicile) meta += " Without Gujarat domicile only All India (MCC) seats are shown.";
  el.querySelector(".outlook-meta").textContent = meta;
}

function renderStreams(insights) {
  $("streams").innerHTML = insights.map((i) => `
    <details class="card stream">
      <summary class="stream-head">
        <span class="stream-name">${esc(i.stream)}</span>
        <span class="pill pill-govt">Govt ${i.govtReachable}</span>
        <span class="pill pill-private">Private ${i.privateReachable}</span>
      </summary>
      <div class="stream-body">
        <p>${i.topGovt.length ? esc(i.topGovt.join(", ")) : i.closestMiss ? `None. Closest: ${esc(i.closestMiss)}` : "None"}</p>
        <p class="muted">${i.feeMin == null ? "Fee data not available" : `${esc(fee(i.feeMin))} – ${esc(fee(i.feeMax))} / yr`}</p>
        <button class="btn btn-secondary show-stream" type="button" data-stream="${esc(i.stream)}">Show options</button>
      </div>
    </details>`).join("");
}

// --- filters ---
function fillFilter(id, values) {
  const counts = new Map();
  for (const v of values) counts.set(v, (counts.get(v) || 0) + 1);
  const sel = $(id), first = sel.options[0];
  sel.replaceChildren(first, ...[...counts.keys()].sort().map((v) => new Option(`${v} (${counts.get(v)})`, v)));
}

const currentChance = () => document.querySelector('.chip[aria-pressed="true"]').dataset.chance;
function setChance(value) {
  for (const chip of document.querySelectorAll(".chip")) chip.setAttribute("aria-pressed", String(chip.dataset.chance === value));
}

function resetToDefaultFilters() {
  $("f-sort").value = "chance";
  setChance("reach");
  pageSize = 30;
}

function clearFilters() {
  for (const id of ["f-stream", "f-type", "f-route"]) $(id).selectedIndex = 0;
  resetToDefaultFilters();
  renderList();
}

function filtered() {
  const st = $("f-stream").value, ty = $("f-type").value, ro = $("f-route").value, ch = currentChance();
  return options.filter((o) => (!st || o.stream === st) && (!ty || o.type === ty) && (!ro || o.route === ro)
    && (ch === "all" || (ch === "reach" ? REACHABLE.has(o.chance) : o.chance === ch)));
}

function sorted(rows) {
  const by = $("f-sort").value, arr = rows.slice();
  if (by === "fee-asc") arr.sort((a, b) => (a.fee ?? Infinity) - (b.fee ?? Infinity));
  else if (by === "fee-desc") arr.sort((a, b) => (b.fee ?? -Infinity) - (a.fee ?? -Infinity));
  else if (by === "college") arr.sort((a, b) => a.college.localeCompare(b.college));
  return arr; // "chance": options already arrive in engine order
}

function updateChipCounts() {
  const st = $("f-stream").value, ty = $("f-type").value, ro = $("f-route").value;
  const base = options.filter((o) => (!st || o.stream === st) && (!ty || o.type === ty) && (!ro || o.route === ro));
  const counts = {
    reach: base.filter((o) => REACHABLE.has(o.chance)).length, all: base.length,
    High: base.filter((o) => o.chance === "High").length, Good: base.filter((o) => o.chance === "Good").length,
    Borderline: base.filter((o) => o.chance === "Borderline").length, Low: base.filter((o) => o.chance === "Low").length,
  };
  for (const chip of document.querySelectorAll(".chip")) chip.querySelector(".chip-count").textContent = counts[chip.dataset.chance] ?? 0;
}

// --- list / table / paging ---
function cardHtml(o) {
  return `<article class="card option chance--${esc(o.chance)}">
    <div class="option-top">
      <h3 class="option-college">${esc(o.college)}</h3>
      <span class="chip-chance chance--${esc(o.chance)}"><span class="icon" aria-hidden="true">${CHANCE_ICON[o.chance] || "?"}</span>${esc(o.chance)}</span>
    </div>
    <p class="option-course">${esc(o.course)} · ${esc(o.stream)}</p>
    <ul class="meta">
      <li>${esc(o.type)}</li>
      <li>${esc(o.route)}</li>
      <li>${esc(fee(o.fee))}</li>
      <li>${esc(earliest(o))}</li>
    </ul>
    <details class="why"><summary>Why this chance?</summary><p>${esc(o.reason)}</p></details>
  </article>`;
}

function rowHtml(o) {
  return `<tr>${COLS.map(([k]) => k === "chance"
    ? `<td><span class="chip-chance chance--${esc(o.chance)}"><span class="icon" aria-hidden="true">${CHANCE_ICON[o.chance] || "?"}</span>${esc(o.chance)}</span></td>`
    : `<td>${esc(k === "fee" ? fee(o.fee) : k === "earliestRound" ? earliest(o) : o[k])}</td>`).join("")}</tr>`;
}

function renderList() {
  const rows = sorted(filtered());
  updateChipCounts();
  $("count").textContent = `${rows.length} options · ${rows.filter((o) => GOVT_TYPES.has(o.type)).length} Govt-type`;
  const isEmpty = rows.length === 0;
  $("empty").hidden = !isEmpty;
  $("cards").hidden = isEmpty;
  document.querySelector(".table-wrap").hidden = isEmpty;
  $("more").hidden = isEmpty || rows.length <= pageSize;
  const page = rows.slice(0, pageSize);
  $("cards").innerHTML = page.map(cardHtml).join("");
  $("table").tBodies[0].innerHTML = page.map(rowHtml).join("");
}

function downloadCsv() {
  const rows = sorted(filtered());
  const cell = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const val = (o, k) => (k === "fee" ? fee(o.fee) : k === "earliestRound" ? earliest(o) : o[k]);
  const csv = [COLS.map(([, h]) => cell(h)).join(","), ...rows.map((o) => COLS.map(([k]) => cell(val(o, k))).join(","))].join("\n");
  const a = Object.assign(document.createElement("a"), {
    href: URL.createObjectURL(new Blob([csv], { type: "text/csv" })), download: `${candidate.appNo}-gujarat-options.csv` });
  a.click();
  URL.revokeObjectURL(a.href);
}

// --- wiring ---
$("form").addEventListener("submit", (e) => { e.preventDefault(); showResult(); });
$("predict").addEventListener("click", showPrediction);
["f-stream", "f-type", "f-route", "f-sort"].forEach((id) => $(id).addEventListener("change", () => { pageSize = 30; renderList(); }));
document.querySelector(".chips").addEventListener("click", (e) => {
  const chip = e.target.closest(".chip");
  if (!chip) return;
  setChance(chip.dataset.chance);
  pageSize = 30;
  renderList();
});
$("streams").addEventListener("click", (e) => {
  const btn = e.target.closest(".show-stream");
  if (!btn) return;
  $("f-stream").value = btn.dataset.stream;
  pageSize = 30;
  renderList();
  $("options-title").scrollIntoView({ behavior: reducedMotion() ? "auto" : "smooth" });
});
$("more").addEventListener("click", () => { pageSize += 30; renderList(); });
$("clear").addEventListener("click", clearFilters);
$("csv").addEventListener("click", downloadCsv);

load();
