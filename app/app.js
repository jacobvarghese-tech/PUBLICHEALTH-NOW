const FEATURES = [
  "Specialty",
  "Gender",
  "line_srvc_cnt_mean",
  "line_srvc_cnt_sum",
  "line_srvc_cnt_median",
  "line_srvc_cnt_std",
  "line_srvc_cnt_min",
  "line_srvc_cnt_max",
  "bene_unique_cnt_mean",
  "bene_unique_cnt_sum",
  "bene_unique_cnt_median",
  "bene_unique_cnt_std",
  "bene_unique_cnt_min",
  "bene_unique_cnt_max",
  "bene_day_srvc_cnt_mean",
  "bene_day_srvc_cnt_sum",
  "bene_day_srvc_cnt_median",
  "bene_day_srvc_cnt_std",
  "bene_day_srvc_cnt_min",
  "bene_day_srvc_cnt_max",
  "average_submitted_chrg_amt_mean",
  "average_submitted_chrg_amt_sum",
  "average_submitted_chrg_amt_median",
  "average_submitted_chrg_amt_std",
  "average_submitted_chrg_amt_min",
  "average_submitted_chrg_amt_max",
  "average_medicare_payment_amt_mean",
  "average_medicare_payment_amt_sum",
  "average_medicare_payment_amt_median",
  "average_medicare_payment_amt_std",
  "average_medicare_payment_amt_min",
  "average_medicare_payment_amt_max",
];

const FEATURE_LABELS = {
  Specialty: "Specialty",
  Gender: "Gender",
  line_srvc_cnt_mean: "Services per code, mean",
  line_srvc_cnt_sum: "Services per code, sum",
  line_srvc_cnt_median: "Services per code, median",
  line_srvc_cnt_std: "Services per code, std",
  line_srvc_cnt_min: "Services per code, min",
  line_srvc_cnt_max: "Services per code, max",
  bene_unique_cnt_mean: "Unique beneficiaries, mean",
  bene_unique_cnt_sum: "Unique beneficiaries, sum",
  bene_unique_cnt_median: "Unique beneficiaries, median",
  bene_unique_cnt_std: "Unique beneficiaries, std",
  bene_unique_cnt_min: "Unique beneficiaries, min",
  bene_unique_cnt_max: "Unique beneficiaries, max",
  bene_day_srvc_cnt_mean: "Beneficiary days, mean",
  bene_day_srvc_cnt_sum: "Beneficiary days, sum",
  bene_day_srvc_cnt_median: "Beneficiary days, median",
  bene_day_srvc_cnt_std: "Beneficiary days, std",
  bene_day_srvc_cnt_min: "Beneficiary days, min",
  bene_day_srvc_cnt_max: "Beneficiary days, max",
  average_submitted_chrg_amt_mean: "Submitted charge, mean",
  average_submitted_chrg_amt_sum: "Submitted charge, sum",
  average_submitted_chrg_amt_median: "Submitted charge, median",
  average_submitted_chrg_amt_std: "Submitted charge, std",
  average_submitted_chrg_amt_min: "Submitted charge, min",
  average_submitted_chrg_amt_max: "Submitted charge, max",
  average_medicare_payment_amt_mean: "Medicare payment, mean",
  average_medicare_payment_amt_sum: "Medicare payment, sum",
  average_medicare_payment_amt_median: "Medicare payment, median",
  average_medicare_payment_amt_std: "Medicare payment, std",
  average_medicare_payment_amt_min: "Medicare payment, min",
  average_medicare_payment_amt_max: "Medicare payment, max",
};

const form = document.querySelector("#score-form");
const scoreResult = document.querySelector("#score-result");
const yearSelect = document.querySelector("#year");
const queryInput = document.querySelector("#query");
const resultsBody = document.querySelector("#results");
const demoCards = document.querySelector("#demo-cards");
const pinNote = document.querySelector("#pin-note");
const resultCount = document.querySelector("#result-count");
const resultNote = document.querySelector("#result-note");
const crumbs = document.querySelector("#crumbs");
const profile = document.querySelector("#profile");

const map = L.map("map", { attributionControl: false }).setView([39.8, -98.6], 4);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 12,
}).addTo(map);
let marker = null;
let openRow = null;

function resemblanceLine() {
  return "A high score is a resemblance, not a fraud finding.";
}

function fillForm(row) {
  for (const name of FEATURES) {
    const input = form.elements[name];
    const value = row[name];
    input.value = value == null ? "" : String(value);
  }
}

function readForm() {
  const row = {};
  for (const name of FEATURES) {
    row[name] = form.elements[name].value;
  }
  return row;
}

function resultText(payload) {
  const lines = [];
  const stored = payload.stored_score === true && payload.score != null;
  if (payload.score != null) {
    lines.push(`Score: ${Number(payload.score).toFixed(6)}.`);
  }
  if (payload.percentile_text) {
    lines.push(payload.percentile_text);
  }
  if (payload.incomplete && !stored) {
    const missing = (payload.missing || []).join(", ");
    lines.push(`Incomplete row. Missing: ${missing}.`);
  }
  lines.push(payload.resemblance || resemblanceLine());
  return lines.join(" ");
}

function showScore(payload) {
  const stored = payload.stored_score === true && payload.score != null;
  scoreResult.textContent = resultText(payload);
  scoreResult.dataset.incomplete = payload.incomplete && !stored ? "true" : "false";
  scoreResult.dataset.storedScore = stored ? "true" : "false";
}

function formatAmount(value) {
  if (value == null || String(value).trim() === "") {
    return "Blank";
  }
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return String(value);
  }
  return number.toLocaleString("en-US", { maximumFractionDigits: 2 });
}

function formatMoney(value) {
  if (value == null || String(value).trim() === "") {
    return "Blank";
  }
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return String(value);
  }
  return number.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
}

function showProfile(row) {
  profile.hidden = false;
  const year = row.Year || yearSelect.value;
  const name = row.Name || "Stored row";
  document.querySelector("#profile-name").textContent = name;
  document.querySelector("#profile-crumbs").textContent = `Medicare Fraud Flagger » ${year} » ${row.City || "Unknown city"}`;
  const place = [row.City, row.State, row.ZIP].filter(Boolean).join(", ");
  document.querySelector("#profile-place").textContent = place || "No city is stored on this row.";
  document.querySelector("#profile-meta").textContent = `NPI ${row.NPI || ""} · ${row.Specialty || "Specialty blank"}`;
  document.querySelector("#glance-heading").textContent = `At a glance: this provider in ${year}`;
  const percentile = row.percentile == null ? "—" : Number(row.percentile).toFixed(2);
  document.querySelector("#stat-percentile").textContent = percentile;
  document.querySelector("#stat-specialty").textContent = row.Specialty || "Blank";
  document.querySelector("#stat-services").textContent = formatAmount(row.line_srvc_cnt_mean);
  document.querySelector("#stat-charge").textContent = formatMoney(row.average_submitted_chrg_amt_mean);
  document.querySelector("#stat-rankline").textContent = row.percentile_text || "";
  document.querySelector("#profile-resemblance").textContent = row.resemblance || resemblanceLine();

  const body = document.querySelector("#feature-body");
  body.replaceChildren();
  for (const name of FEATURES) {
    const tr = document.createElement("tr");
    const label = document.createElement("td");
    label.textContent = FEATURE_LABELS[name] || name;
    const value = document.createElement("td");
    const raw = row[name];
    value.textContent = raw == null || String(raw).trim() === "" ? "" : String(raw);
    tr.append(label, value);
    body.appendChild(tr);
  }
}

async function scoreTyped(event) {
  event.preventDefault();
  const response = await fetch("/api/score", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(readForm()),
  });
  const payload = await response.json();
  showScore(payload);
  showProfile({ ...readForm(), ...payload, Name: "Typed row", Year: "2024" });
}

function placePin(row) {
  openRow = row;
  if (marker) {
    map.removeLayer(marker);
    marker = null;
  }
  const pin = row.pin;
  if (!pin) {
    pinNote.textContent = `${row.City || "Unknown city"}, ${row.State || ""} ${row.ZIP || ""}. No ZIP coordinate is stored, so there is no pin. The row is still open.`;
    return;
  }
  marker = L.marker([pin.lat, pin.lon]).addTo(map);
  marker.on("click", () => openStoredRow(row.Year, row.NPI));
  map.setView([pin.lat, pin.lon], 9);
  pinNote.textContent = `Pin for ${row.Name || row.NPI} at ${pin.city}, ${pin.state} ${pin.zip}. Click the pin to open this row.`;
  setTimeout(() => map.invalidateSize(), 0);
}

async function openStoredRow(year, npi) {
  const response = await fetch(`/api/row?year=${encodeURIComponent(year)}&npi=${encodeURIComponent(npi)}`);
  const row = await response.json();
  if (!row.found) {
    scoreResult.textContent = `No stored row for NPI ${npi} in ${year}. ${resemblanceLine()}`;
    return;
  }
  yearSelect.value = String(year);
  fillForm(row);
  placePin(row);
  showScore(row);
  showProfile(row);
  return row;
}

function renderResults(rows, query, total) {
  resultsBody.replaceChildren();
  const shown = total && total > rows.length ? `${rows.length} of ${total}` : String(rows.length);
  const label = query ? `results for “${query}”` : "results";
  resultCount.textContent = rows.length ? `${shown} ${label}` : "";
  crumbs.textContent = query
    ? `Medicare Fraud Flagger » Search for ${query}`
    : "Medicare Fraud Flagger";
  for (const row of rows) {
    const tr = document.createElement("tr");
    tr.dataset.npi = row.NPI;
    tr.dataset.year = row.Year;
    const who = document.createElement("td");
    const name = document.createElement("a");
    name.className = "prov_name";
    name.href = `#${row.Year || ""}-${row.NPI || ""}`;
    name.textContent = row.Name || row.NPI || "";
    name.addEventListener("click", (event) => {
      event.preventDefault();
      openStoredRow(row.Year, row.NPI);
    });
    const specialty = document.createElement("p");
    specialty.textContent = row.Specialty || "";
    const address = document.createElement("div");
    address.className = "address";
    const place = document.createElement("p");
    place.textContent = [row.City, row.State, row.ZIP].filter(Boolean).join(", ");
    const npi = document.createElement("p");
    npi.textContent = row.NPI || "";
    address.append(place, npi);
    who.append(name, specialty, address);
    const rank = document.createElement("td");
    rank.className = "right_num";
    const num = document.createElement("span");
    num.className = "num";
    num.textContent = row.percentile == null ? "—" : Number(row.percentile).toFixed(2);
    rank.appendChild(num);
    tr.append(who, rank);
    tr.addEventListener("click", () => openStoredRow(row.Year, row.NPI));
    resultsBody.appendChild(tr);
  }
  resultNote.textContent = rows.length
    ? `${rows.length} stored rows. Click a row to open that provider.`
    : "No stored rows matched.";
}

async function searchStored() {
  const year = yearSelect.value;
  const q = queryInput.value.trim();
  const first = await fetch(`/api/search?year=${encodeURIComponent(year)}&q=${encodeURIComponent(q)}&limit=40`);
  const preview = await first.json();
  const previewRows = preview.rows || [];
  renderResults(previewRows, q, preview.total);
  resultNote.textContent = previewRows.length
    ? "Loading the rest of this search."
    : "No stored rows matched.";
  if (previewRows.length === 1 && (preview.total || 1) === 1) {
    await openStoredRow(previewRows[0].Year, previewRows[0].NPI);
  }
  const rest = await fetch(`/api/search?year=${encodeURIComponent(year)}&q=${encodeURIComponent(q)}`);
  const payload = await rest.json();
  if (queryInput.value.trim() !== q || yearSelect.value !== year) {
    return;
  }
  const rows = payload.rows || [];
  renderResults(rows, q, payload.total);
  if (rows.length === 1) {
    await openStoredRow(rows[0].Year, rows[0].NPI);
  }
}

function renderDemos(rows) {
  demoCards.replaceChildren();
  for (const row of rows) {
    const card = document.createElement("article");
    card.className = "demo-card";
    card.dataset.npi = row.npi || row.NPI;
    const title = document.createElement("h3");
    title.textContent = `${row.Name || "Named lab"} (${row.npi || row.NPI})`;
    const body = document.createElement("p");
    body.textContent = resultText(row);
    card.appendChild(title);
    card.appendChild(body);
    card.addEventListener("click", () => openStoredRow(2024, row.npi || row.NPI));
    demoCards.appendChild(card);
  }
}

async function loadDemos() {
  const response = await fetch("/api/demos");
  const payload = await response.json();
  renderDemos(payload.rows || []);
}

form.addEventListener("submit", scoreTyped);
document.querySelector("#lookup-form").addEventListener("submit", (event) => {
  event.preventDefault();
  searchStored();
});

document.querySelector(".search-examples").addEventListener("click", (event) => {
  const link = event.target.closest("a");
  if (!link) {
    return;
  }
  event.preventDefault();
  if (link.dataset.year) {
    yearSelect.value = link.dataset.year;
  }
  if (link.dataset.open) {
    queryInput.value = link.dataset.open;
    openStoredRow(link.dataset.year || yearSelect.value, link.dataset.open);
    return;
  }
  if (link.dataset.query) {
    queryInput.value = link.dataset.query;
    searchStored();
  }
});

loadDemos();
