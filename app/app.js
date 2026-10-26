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
  line_srvc_cnt_mean: "Services, mean",
  line_srvc_cnt_sum: "Services, sum",
  line_srvc_cnt_median: "Services, median",
  line_srvc_cnt_std: "Services, std",
  line_srvc_cnt_min: "Services, min",
  line_srvc_cnt_max: "Services, max",
  bene_unique_cnt_mean: "Beneficiaries, mean",
  bene_unique_cnt_sum: "Beneficiaries, sum",
  bene_unique_cnt_median: "Beneficiaries, median",
  bene_unique_cnt_std: "Beneficiaries, std",
  bene_unique_cnt_min: "Beneficiaries, min",
  bene_unique_cnt_max: "Beneficiaries, max",
  bene_day_srvc_cnt_mean: "Days, mean",
  bene_day_srvc_cnt_sum: "Days, sum",
  bene_day_srvc_cnt_median: "Days, median",
  bene_day_srvc_cnt_std: "Days, std",
  bene_day_srvc_cnt_min: "Days, min",
  bene_day_srvc_cnt_max: "Days, max",
  average_submitted_chrg_amt_mean: "Charge, mean",
  average_submitted_chrg_amt_sum: "Charge, sum",
  average_submitted_chrg_amt_median: "Charge, median",
  average_submitted_chrg_amt_std: "Charge, std",
  average_submitted_chrg_amt_min: "Charge, min",
  average_submitted_chrg_amt_max: "Charge, max",
  average_medicare_payment_amt_mean: "Payment, mean",
  average_medicare_payment_amt_sum: "Payment, sum",
  average_medicare_payment_amt_median: "Payment, median",
  average_medicare_payment_amt_std: "Payment, std",
  average_medicare_payment_amt_min: "Payment, min",
  average_medicare_payment_amt_max: "Payment, max",
};

const form = document.querySelector("#score-form");
const scoreButton = document.querySelector("#score-button");
const searchButton = document.querySelector("#search-button");
const scoreResult = document.querySelector("#score-result");
const yearSelect = document.querySelector("#year");
const queryInput = document.querySelector("#query");
const resultsBody = document.querySelector("#results");
const demoCards = document.querySelector("#demo-cards");
const pinNote = document.querySelector("#pin-note");
const resultCount = document.querySelector("#result-count");
const resultNote = document.querySelector("#result-note");
const lookupStatus = document.querySelector("#lookup-status");
const crumbs = document.querySelector("#crumbs");
const profile = document.querySelector("#profile");

const US_BOUNDS = L.latLngBounds([17.5, -170], [72.5, -64]);
const US_CENTER = [39.8, -98.6];
const mapNode = document.querySelector("#map");
const map = mapNode
  ? L.map(mapNode, {
      attributionControl: false,
      maxBounds: US_BOUNDS,
      maxBoundsViscosity: 1,
      minZoom: 4,
      maxZoom: 12,
    }).setView(US_CENTER, 4)
  : null;
if (map) {
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 12,
  }).addTo(map);
  map.setMaxBounds(US_BOUNDS);
  window.setTimeout(lockMapToAmerica, 0);
}
let marker = null;
let openRow = null;

const RESEMBLANCE = "Resembles later exclusions.";

function fillForm(row) {
  if (!form) {
    return;
  }
  for (const name of FEATURES) {
    const input = form.elements[name];
    const value = row[name];
    input.value = value == null ? "" : String(value);
  }
}

function applyExtracted(fields) {
  let filled = 0;
  if (queryInput && fields.query) {
    queryInput.value = fields.query;
    filled += 1;
  }
  if (yearSelect && fields.year) {
    const match = Array.from(yearSelect.options).find((option) => option.value === String(fields.year) || option.textContent.trim() === String(fields.year));
    if (match) {
      yearSelect.value = match.value;
      filled += 1;
    }
  }
  if (form) {
    for (const name of FEATURES) {
      if (fields[name] == null || String(fields[name]).trim() === "") {
        continue;
      }
      const input = form.elements[name];
      if (!input) {
        continue;
      }
      input.value = String(fields[name]);
      filled += 1;
    }
  }
  return filled;
}

async function fillFromAttachment(event) {
  event.preventDefault();
  const button = document.querySelector("#attachment-button");
  const status = document.querySelector("#attachment-status");
  const npiInput = document.querySelector("#attachment-npi");
  const yearInput = document.querySelector("#attachment-year");
  const fileInput = document.querySelector("#attachment-file");
  const npi = npiInput ? npiInput.value.trim() : "";
  const file = fileInput && fileInput.files ? fileInput.files[0] : null;
  if (!/^\d{10}$/.test(npi)) {
    const message = "Need a 10-digit NPI.";
    if (status) {
      status.textContent = message;
    }
    announce(message);
    if (npiInput) {
      npiInput.focus();
    }
    return;
  }
  if (!file) {
    const message = "Choose a file.";
    if (status) {
      status.textContent = message;
    }
    announce(message);
    if (fileInput) {
      fileInput.focus();
    }
    return;
  }
  const body = new FormData();
  body.append("attachment", file, file.name);
  const year = yearInput ? yearInput.value : "";
  const address = `/api/attachment?npi=${encodeURIComponent(npi)}&year=${encodeURIComponent(year)}`;
  setBusy(button, true, "Reading");
  if (status) {
    status.textContent = "Reading";
  }
  announce("Reading");
  try {
    const response = await fetch(address, { method: "POST", body });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `the attachment service returned ${response.status}`);
    }
    const filled = applyExtracted(payload.fields || {});
    const missing = (payload.missing || []).length;
    const message = filled
      ? `${filled} filled.`
      : "None filled.";
    if (status) {
      status.textContent = message;
    }
    announce(message);
  } catch (error) {
    const message = fetchFailure("Attachment", error);
    if (status) {
      status.textContent = message;
    }
    announce(message);
  } finally {
    setBusy(button, false);
  }
}

async function fillFromNotes(button, notesId, statusId, kind) {
  const notes = document.querySelector(notesId);
  const status = document.querySelector(statusId);
  const text = notes ? notes.value.trim() : "";
  if (!text) {
    const message = "Add notes.";
    if (status) {
      status.textContent = message;
    }
    announce(message);
    if (notes) {
      notes.focus();
    }
    return;
  }
  setBusy(button, true, "Reading");
  if (status) {
    status.textContent = "Reading";
  }
  announce("Reading");
  try {
    const response = await fetch("/api/extract", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ kind, notes: text }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `the extract service returned ${response.status}`);
    }
    const filled = applyExtracted(payload.fields || {});
    const missing = (payload.missing || []).length;
    const message = filled
      ? `${filled} filled.`
      : "None filled.";
    if (status) {
      status.textContent = message;
    }
    announce(message);
  } catch (error) {
    const message = fetchFailure("Fill", error);
    if (status) {
      status.textContent = message;
    }
    announce(message);
  } finally {
    setBusy(button, false);
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
    lines.push(Number(payload.score).toFixed(2));
  }
  if (payload.percentile != null) {
    lines.push(Number(payload.percentile).toFixed(2));
  } else if (payload.percentile_text) {
    lines.push(payload.percentile_text);
  }
  if (payload.incomplete && !stored) {
    lines.push("Incomplete");
  }
  return lines.join(" ");
}

function isFlagged(payload) {
  const stored = payload.stored_score === true && payload.score != null;
  if (payload.incomplete && !stored) {
    return false;
  }
  if (payload.percentile == null || payload.outside_top_1 == null) {
    return false;
  }
  return payload.outside_top_1 === false;
}

function flagMark() {
  const wrap = document.createElement("span");
  wrap.className = "flag-mark";
  wrap.title = "Flagged";
  wrap.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M12 3.2 21.2 20.4H2.8L12 3.2z"/><path fill="#1b1b1b" d="M11 9.2h2v6.2h-2zm0 7.4h2V19h-2z"/></svg>`;
  const text = document.createElement("span");
  text.className = "usa-sr-only";
  text.textContent = "Flagged";
  wrap.appendChild(text);
  return wrap;
}

function verdictSentence(payload) {
  const stored = payload.stored_score === true && payload.score != null;
  if (payload.incomplete && !stored) {
    return "Incomplete. A blank billing number stays blank, so this row has no verdict.";
  }
  if (payload.percentile == null) {
    return "No verdict. This row has no percentile.";
  }
  const year = payload.Year || "2024";
  const rank = Number(payload.percentile).toFixed(2);
  if (payload.outside_top_1) {
    return `${year} percentile ${rank}. This row is outside the top 1 percent. Not flagged.`;
  }
  return `${year} percentile ${rank}. This row is inside the top 1 percent. Flagged.`;
}

function showScore(payload) {
  if (!scoreResult) {
    return;
  }
  const stored = payload.stored_score === true && payload.score != null;
  scoreResult.textContent = resultText(payload);
  scoreResult.dataset.incomplete = payload.incomplete && !stored ? "true" : "false";
  scoreResult.dataset.storedScore = stored ? "true" : "false";
  announce(scoreResult.textContent);
  const panel = document.querySelector("#verdict");
  if (!panel) {
    return;
  }
  panel.hidden = false;
  const title = isFlagged(payload)
    ? "Flagged"
    : payload.incomplete && !stored
      ? "Incomplete"
      : "Not flagged";
  const heading = document.querySelector("#verdict-title");
  heading.replaceChildren();
  if (isFlagged(payload)) {
    heading.appendChild(flagMark());
  }
  heading.append(document.createTextNode(title));
  const npi = document.querySelector("#attachment-npi");
  const year = document.querySelector("#attachment-year");
  const who = [
    npi && npi.value.trim() ? `NPI ${npi.value.trim()}` : "",
    year && year.value ? year.value : "2024",
  ].filter(Boolean).join(" · ");
  document.querySelector("#verdict-meta").textContent = who;
  document.querySelector("#verdict-percentile").textContent = payload.percentile == null
    ? "—"
    : Number(payload.percentile).toFixed(2);
  document.querySelector("#verdict-score").textContent = payload.score == null
    ? "—"
    : Number(payload.score).toFixed(2);
  document.querySelector("#verdict-specialty").textContent = payload.Specialty || "Blank";
  document.querySelector("#verdict-services").textContent = formatAmount(payload.line_srvc_cnt_mean);
  document.querySelector("#verdict-sentence").textContent = verdictSentence(payload);
  panel.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function announce(message) {
  lookupStatus.textContent = "";
  lookupStatus.textContent = message;
}

function setBusy(button, busy, waiting) {
  button.disabled = busy;
  button.setAttribute("aria-busy", busy ? "true" : "false");
  if (busy) {
    if (!button.dataset.idleLabel) {
      button.dataset.idleLabel = button.textContent;
    }
    button.textContent = waiting;
    return;
  }
  if (button.dataset.idleLabel) {
    button.textContent = button.dataset.idleLabel;
  }
}

function fetchFailure(action, error) {
  const detail = error && error.message ? error.message : "request failed";
  return `${action} failed. ${detail}`;
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
  if (!profile) {
    return;
  }
  profile.hidden = false;
  const year = row.Year || (yearSelect ? yearSelect.value : "2024");
  const name = row.Name || "Stored row";
  const heading = document.querySelector("#profile-name");
  heading.replaceChildren();
  if (isFlagged(row)) {
    heading.appendChild(flagMark());
  }
  heading.append(document.createTextNode(name));
  const place = [row.City, row.State, row.ZIP].filter(Boolean).join(", ");
  document.querySelector("#profile-place").textContent = place;
  document.querySelector("#profile-meta").textContent = [row.NPI ? `NPI ${row.NPI}` : "", row.Specialty || ""].filter(Boolean).join(" · ");
  const percentile = row.percentile == null ? "—" : Number(row.percentile).toFixed(2);
  document.querySelector("#stat-percentile").textContent = percentile;
  document.querySelector("#stat-specialty").textContent = row.Specialty || "Blank";
  document.querySelector("#stat-services").textContent = formatAmount(row.line_srvc_cnt_mean);
  document.querySelector("#stat-charge").textContent = formatMoney(row.average_submitted_chrg_amt_mean);
  document.querySelector("#stat-rankline").textContent = row.percentile_text || "";
  document.querySelector("#profile-resemblance").textContent = RESEMBLANCE;

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
  setBusy(scoreButton, true, "Scoring");
  announce("Scoring");
  try {
    const response = await fetch("/api/score", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(readForm()),
    });
    if (!response.ok) {
      throw new Error(`the score service returned ${response.status}`);
    }
    const payload = await response.json();
    showScore(payload);
    showProfile({ ...readForm(), ...payload, Name: "Typed row", Year: "2024" });
  } catch (error) {
    const message = fetchFailure("Score", error);
    scoreResult.textContent = message;
    announce(message);
  } finally {
    setBusy(scoreButton, false);
  }
}

function placePin(row) {
  if (!map) {
    return;
  }
  openRow = row;
  if (marker) {
    map.removeLayer(marker);
    marker = null;
  }
  const pin = row.pin;
  if (!pin) {
    if (pinNote) {
      pinNote.textContent = "No pin.";
    }
    return;
  }
  marker = L.marker([pin.lat, pin.lon]).addTo(map);
  marker.on("click", () => openStoredRow(row.Year, row.NPI));
  marker.on("keypress", (event) => {
    const key = event.originalEvent && event.originalEvent.key;
    if (key === "Enter" || key === " ") {
      openStoredRow(row.Year, row.NPI);
    }
  });
  const pinZoom = Math.min(9, map.getMaxZoom());
  const pinPoint = L.latLng(pin.lat, pin.lon);
  map.setView(US_BOUNDS.contains(pinPoint) ? pinPoint : map.getCenter(), pinZoom);
  if (pinNote) {
    pinNote.textContent = `${pin.city}, ${pin.state} ${pin.zip}`;
  }
  setTimeout(lockMapToAmerica, 0);
}

let resizeTimer = 0;
function lockMapToAmerica() {
  if (!map) {
    return;
  }
  const box = mapNode.getBoundingClientRect();
  if (box.width < 20 || box.height < 20) {
    return;
  }
  map.invalidateSize({ pan: false, debounceMoveend: true });
  const fitted = map.getBoundsZoom(US_BOUNDS, true, L.point(24, 24));
  const zoom = Math.max(3, Math.min(fitted, 6));
  map.setMinZoom(3);
  map.setMaxBounds(null);
  map.setView(US_BOUNDS.getCenter(), zoom, { animate: false });
  map.setMaxBounds(US_BOUNDS);
}
function watchBox(node) {
  if (!node || typeof ResizeObserver !== "function") {
    return;
  }
  const watcher = new ResizeObserver(() => {
    window.clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(lockMapToAmerica, 40);
  });
  watcher.observe(node);
}
watchBox(mapNode);
watchBox(document.querySelector(".main-pane"));
window.addEventListener("resize", () => {
  window.clearTimeout(resizeTimer);
  resizeTimer = window.setTimeout(lockMapToAmerica, 40);
});

async function openStoredRow(year, npi) {
  const response = await fetch(`/api/row?year=${encodeURIComponent(year)}&npi=${encodeURIComponent(npi)}`);
  const row = await response.json();
  if (!row.found) {
    const message = "No row.";
    scoreResult.textContent = message;
    announce(message);
    return;
  }
  yearSelect.value = String(year);
  fillForm(row);
  placePin(row);
  showScore(row);
  showProfile(row);
  announce(row.Name || "Open");
  return row;
}

function renderResults(rows, query, total) {
  if (!resultsBody) {
    return;
  }
  resultsBody.replaceChildren();
  const browserPane = resultsBody.closest(".provider_box");
  if (browserPane) {
    browserPane.classList.toggle("is-empty", rows.length === 0);
  }
  const shown = total && total > rows.length ? `${rows.length} of ${total}` : String(rows.length);
  if (resultCount) {
    resultCount.textContent = rows.length ? shown : "";
  }
  if (crumbs) {
    crumbs.textContent = query
      ? `Medicare Fraud Flagger » Search for ${query}`
      : "Medicare Fraud Flagger";
  }
  for (const row of rows) {
    const tr = document.createElement("tr");
    tr.dataset.npi = row.NPI;
    tr.dataset.year = row.Year;
    const who = document.createElement("td");
    const name = document.createElement("a");
    name.className = "prov_name";
    name.href = `#${row.Year || ""}-${row.NPI || ""}`;
    name.replaceChildren();
    if (isFlagged(row)) {
      name.appendChild(flagMark());
    }
    name.append(document.createTextNode(row.Name || row.NPI || ""));
    name.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
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
    tr.tabIndex = 0;
    tr.setAttribute("role", "button");
    tr.setAttribute(
      "aria-label",
      `${isFlagged(row) ? "Flagged. " : ""}Open ${row.Name || row.NPI || "stored row"}, percentile ${row.percentile == null ? "not stored" : Number(row.percentile).toFixed(2)}`,
    );
    tr.addEventListener("click", () => openStoredRow(row.Year, row.NPI));
    tr.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openStoredRow(row.Year, row.NPI);
      }
    });
    resultsBody.appendChild(tr);
  }
  const note = rows.length ? `${rows.length}` : "No rows.";
  if (resultNote) {
    resultNote.textContent = note;
  }
  announce(resultCount && resultCount.textContent ? `${resultCount.textContent}. ${note}` : note);
}

async function searchStored() {
  const year = yearSelect.value;
  const q = queryInput.value.trim();
  setBusy(searchButton, true, "Searching");
  announce("Searching");
  try {
    const first = await fetch(`/api/search?year=${encodeURIComponent(year)}&q=${encodeURIComponent(q)}&limit=40`);
    if (!first.ok) {
      throw new Error(`the search service returned ${first.status}`);
    }
    const preview = await first.json();
    const previewRows = preview.rows || [];
    renderResults(previewRows, q, preview.total);
    if (previewRows.length === 1 && (preview.total || 1) === 1) {
      await openStoredRow(previewRows[0].Year, previewRows[0].NPI);
    }
    const total = preview.total || previewRows.length;
    if (!previewRows.length || previewRows.length >= total) {
      return;
    }
    resultNote.textContent = "Loading";
    announce("Loading");
    setBusy(searchButton, false);
    const rest = await fetch(`/api/search?year=${encodeURIComponent(year)}&q=${encodeURIComponent(q)}`);
    if (!rest.ok) {
      throw new Error(`the search service returned ${rest.status}`);
    }
    const payload = await rest.json();
    if (queryInput.value.trim() !== q || yearSelect.value !== year) {
      return;
    }
    const rows = payload.rows || [];
    renderResults(rows, q, payload.total);
    if (rows.length === 1) {
      await openStoredRow(rows[0].Year, rows[0].NPI);
    }
  } catch (error) {
    const message = fetchFailure("Search", error);
    resultNote.textContent = message;
    announce(message);
  } finally {
    setBusy(searchButton, false);
  }
}

function renderDemos(rows) {
  if (!demoCards) {
    return;
  }
  demoCards.replaceChildren();
  for (const row of rows) {
    const npi = row.npi || row.NPI;
    const card = document.createElement("button");
    card.type = "button";
    card.className = "demo-card";
    card.dataset.npi = npi;
    const title = document.createElement("h3");
    title.textContent = `${row.Name || "Named lab"} (${npi})`;
    const body = document.createElement("p");
    body.textContent = resultText(row);
    card.append(title, body);
    card.addEventListener("click", () => openStoredRow(2024, npi));
    demoCards.appendChild(card);
  }
}

async function loadDemos() {
  const response = await fetch("/api/demos");
  const payload = await response.json();
  renderDemos(payload.rows || []);
}

if (form) {
  form.addEventListener("submit", scoreTyped);
}
const searchExtractButton = document.querySelector("#search-extract-button");
if (searchExtractButton) {
  searchExtractButton.addEventListener("click", () => {
    fillFromNotes(searchExtractButton, "#search-notes", "#search-extract-status", "search");
  });
}
const attachmentForm = document.querySelector("#model-upload");
if (attachmentForm) {
  attachmentForm.addEventListener("submit", fillFromAttachment);
}
const modelExtractButton = document.querySelector("#model-extract-button");
if (modelExtractButton) {
  modelExtractButton.addEventListener("click", () => {
    fillFromNotes(modelExtractButton, "#model-notes", "#model-extract-status", "model");
  });
}
const lookupForm = document.querySelector("#lookup-form");
if (lookupForm) {
  lookupForm.addEventListener("submit", (event) => {
    event.preventDefault();
    searchStored();
  });
}

const examples = document.querySelector(".search-examples");
if (examples) {
  examples.addEventListener("click", (event) => {
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
}

if (demoCards) {
  loadDemos();
}
