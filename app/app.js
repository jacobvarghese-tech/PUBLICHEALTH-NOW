const state = {
  data: null,
  code: "81419",
  year: "2024",
  query: "",
  knownOnly: false,
  selected: null,
};

const codeSelect = document.querySelector("#code");
const yearSelect = document.querySelector("#year");
const queryInput = document.querySelector("#query");
const knownInput = document.querySelector("#known-only");
const rowsBody = document.querySelector("#rows");
const summary = document.querySelector("#summary");
const detail = document.querySelector("#detail");
const gate = document.querySelector("#gate-notice");
const demoCards = document.querySelector("#demo-cards");

function money(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return Number(value).toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
}

function percent(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${(value * 100).toFixed(1)}%`;
}

function growthText(value) {
  if (value === null || value === undefined) return "new";
  const sign = value > 0 ? "+" : "";
  return `${sign}${(value * 100).toFixed(0)}%`;
}

function scoreText(value) {
  return Number(value).toFixed(2);
}

function currentSlice() {
  return state.data.slices.find((slice) => slice.code === state.code && slice.year === state.year);
}

function filteredRows(slice) {
  const needle = state.query.trim().toLowerCase();
  return slice.rows.filter((row) => {
    if (state.knownOnly && !row.known) return false;
    if (!needle) return true;
    const haystack = `${row.name} ${row.city} ${row.state} ${row.npi}`.toLowerCase();
    return haystack.includes(needle);
  });
}

function fillSelectors() {
  const codes = [];
  const seen = new Set();
  state.data.services.forEach((service) => {
    if (seen.has(service.code)) return;
    seen.add(service.code);
    codes.push(service);
  });
  codeSelect.innerHTML = codes
    .map((service) => `<option value="${service.code}">${service.code} — ${service.label}</option>`)
    .join("");
  codeSelect.value = state.code;
  const years = [...new Set(state.data.slices.filter((slice) => slice.code === state.code).map((slice) => slice.year))];
  yearSelect.innerHTML = years.map((year) => `<option value="${year}">${year}</option>`).join("");
  if (!years.includes(state.year)) state.year = years[years.length - 1];
  yearSelect.value = state.year;
}

function renderGate() {
  const gateInfo = state.data.gate;
  gate.textContent = `Label gate failed at ${gateInfo.uniquePositives} joined fraud-type NPIs. The page ranks unusual billing. It does not call anyone a fraud.`;
}

function renderSummary(slice, shown) {
  summary.innerHTML = `
    <span>${shown.length} shown · ${slice.billerCount} billers</span>
    <span>${Math.round(slice.totalServices).toLocaleString()} services</span>
    <span>Median charge ${money(slice.medianCharge)}</span>
    <span>${slice.knownCount} known sanctioned on this list</span>
  `;
}

function renderRows(slice) {
  const shown = filteredRows(slice);
  renderSummary(slice, shown);
  if (!shown.length) {
    rowsBody.innerHTML = `<tr><td colspan="6">No billers match.</td></tr>`;
    return;
  }
  rowsBody.innerHTML = shown
    .map((row) => {
      const badges = [
        row.known ? `<span class="badge">Known sanctioned</span>` : "",
        row.demo ? `<span class="badge demo">Video example</span>` : "",
      ].join(" ");
      const selected = state.selected === row.npi ? "selected" : "";
      const known = row.known ? "known" : "";
      return `<tr class="${selected} ${known}" data-npi="${row.npi}">
        <td>${row.rank}</td>
        <td><div class="name">${row.name}</div><div class="meta">${row.city}, ${row.state} · ${row.npi}</div>${badges}</td>
        <td>${percent(row.nationalShare)}</td>
        <td>${growthText(row.growth)}</td>
        <td>${row.chargeRatio.toFixed(2)}×</td>
        <td>${scoreText(row.score)}</td>
      </tr>`;
    })
    .join("");
}

function renderDetail(slice) {
  const row = slice.rows.find((item) => item.npi === state.selected) || slice.rows[0];
  if (!row) {
    detail.innerHTML = "<h2>No row</h2>";
    return;
  }
  state.selected = row.npi;
  const knownLine = row.known
    ? `<p>This NPI is on the October 15, 2026 fraud-type exclusion list as ${row.knownType}. The exclusion reason does not name this HCPCS code. The match is a check, not proof this service caused the exclusion.</p>`
    : `<p>This score is a resemblance to an unusual billing pattern. It is not a statement that this biller committed fraud.</p>`;
  detail.innerHTML = `
    <h2>${row.name}</h2>
    <p class="meta">${row.city}, ${row.state} ${row.zip} · NPI ${row.npi}</p>
    <dl>
      <dt>Score</dt><dd>${scoreText(row.score)} · rank ${row.rank} of ${slice.billerCount}</dd>
      <dt>Services</dt><dd>${Math.round(row.services).toLocaleString()} · ${percent(row.nationalShare)} of this code</dd>
      <dt>Beneficiaries</dt><dd>${row.beneficiaries ? Math.round(row.beneficiaries).toLocaleString() : "suppressed"}</dd>
      <dt>Services per beneficiary</dt><dd>${row.perBeneficiary === null ? "—" : row.perBeneficiary.toFixed(2)}</dd>
      <dt>ZIP share</dt><dd>${row.zip} holds ${percent(row.zipShare)} of national services</dd>
      <dt>Growth</dt><dd>${growthText(row.growth)}</dd>
      <dt>Submitted charge</dt><dd>${money(row.charge)} · ${row.chargeRatio.toFixed(2)}× the median</dd>
      <dt>Medicare payment</dt><dd>${money(row.payment)}</dd>
    </dl>
    ${knownLine}
  `;
}

function renderDemo() {
  const slice = state.data.slices.find((item) => item.code === "81419" && item.year === "2024");
  if (!slice) return;
  const cards = state.data.demoNpis
    .map((npi) => slice.rows.find((row) => row.npi === npi))
    .filter(Boolean);
  demoCards.className = "cards";
  demoCards.innerHTML = cards
    .map(
      (row) => `<article class="card">
        <strong>${row.name}</strong>
        <p class="meta">${row.city}, ${row.state} · NPI ${row.npi}</p>
        <p>2024 rank ${row.rank} of ${slice.billerCount}. ${Math.round(row.services).toLocaleString()} services, ${percent(row.nationalShare)} of national 81419 billing. ZIP ${row.zip} share ${percent(row.zipShare)}.</p>
      </article>`
    )
    .join("");
}

function render() {
  fillSelectors();
  const slice = currentSlice();
  if (!slice) {
    rowsBody.innerHTML = `<tr><td colspan="6">No rows for this selection.</td></tr>`;
    return;
  }
  if (!slice.rows.some((row) => row.npi === state.selected)) state.selected = null;
  renderRows(slice);
  renderDetail(slice);
}

codeSelect.addEventListener("change", () => {
  state.code = codeSelect.value;
  state.selected = null;
  render();
});

yearSelect.addEventListener("change", () => {
  state.year = yearSelect.value;
  state.selected = null;
  render();
});

queryInput.addEventListener("input", () => {
  state.query = queryInput.value;
  render();
});

knownInput.addEventListener("change", () => {
  state.knownOnly = knownInput.checked;
  render();
});

rowsBody.addEventListener("click", (event) => {
  const row = event.target.closest("tr");
  if (!row) return;
  state.selected = row.dataset.npi;
  render();
});

fetch("data/rankings.json")
  .then((response) => response.json())
  .then((data) => {
    state.data = data;
    renderGate();
    renderDemo();
    render();
  })
  .catch(() => {
    gate.textContent = "Could not load data/rankings.json. Serve the app folder, or open it from a local server, so the data file can load.";
  });
