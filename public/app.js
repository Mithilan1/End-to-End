const elements = {
  healthPill: document.getElementById("health-pill"),
  messageBanner: document.getElementById("message-banner"),
  results: document.getElementById("results"),
  resultCategory: document.getElementById("result-category"),
  resultTitle: document.getElementById("result-title"),
  resultSource: document.getElementById("result-source"),
  currentSourceChip: document.getElementById("current-source-chip"),
  metricCurrent: document.getElementById("metric-current"),
  metricAction: document.getElementById("metric-action"),
  metricTarget: document.getElementById("metric-target"),
  metricWindow: document.getElementById("metric-window"),
  metricConfidence: document.getElementById("metric-confidence"),
  best30: document.getElementById("best-30"),
  best60: document.getElementById("best-60"),
  best90: document.getElementById("best-90"),
  forecast30: document.getElementById("forecast-30"),
  forecast60: document.getElementById("forecast-60"),
  forecast90: document.getElementById("forecast-90"),
  recommendationReason: document.getElementById("recommendation-reason"),
  recommendationFacts: document.getElementById("recommendation-facts"),
  seasonalBody: document.getElementById("seasonal-body"),
  salesBody: document.getElementById("sales-body"),
  candidateEmpty: document.getElementById("candidate-empty"),
  candidateTableWrap: document.getElementById("candidate-table-wrap"),
  candidateBody: document.getElementById("candidate-body"),
  chart6m: document.getElementById("chart-6m"),
  chart1y: document.getElementById("chart-1y"),
  llmCard: document.getElementById("llm-card"),
  llmSummary: document.getElementById("llm-summary"),
  summaryToggle: document.getElementById("summary-toggle"),
  queryInput: document.getElementById("query-input"),
  imageInput: document.getElementById("image-input"),
  searchForm: document.getElementById("search-form"),
  imageForm: document.getElementById("image-form"),
};

function formatMoney(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "n/a";
  }
  return `$${Number(value).toFixed(2)}`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function showMessage(text, tone = "success") {
  elements.messageBanner.hidden = false;
  elements.messageBanner.dataset.tone = tone;
  elements.messageBanner.textContent = text;
}

function clearMessage() {
  elements.messageBanner.hidden = true;
  elements.messageBanner.textContent = "";
  delete elements.messageBanner.dataset.tone;
}

function setHealth(text, ready = false) {
  elements.healthPill.textContent = text;
  elements.healthPill.className = ready ? "pill" : "pill pill-muted";
}

function formatWindow(window) {
  if (!window || window.price === null || window.price === undefined) {
    return "n/a";
  }
  return `${formatMoney(window.price)} • ${window.date}`;
}

function renderFacts(item, prediction) {
  const monthFormatter = new Intl.DateTimeFormat("en-CA", { month: "long" });
  const buyMonths = (prediction.best_buy_months || []).map((monthNumber) =>
    monthFormatter.format(new Date(Date.UTC(2026, Number(monthNumber) - 1, 1))),
  );
  const facts = [
    `Current price is ${prediction.price_vs_average_pct.toFixed(1)}% versus average.`,
    `Current price is ${prediction.price_vs_low_pct.toFixed(1)}% above the historical low.`,
    `Next sale signal: ${prediction.next_sale_name}.`,
    `Best historical buy months: ${buyMonths.join(", ") || "n/a"}.`,
    `Data sources: ${(item.available_sources || []).join(", ") || "n/a"}.`,
  ];

  if (item.amazon_url) {
    facts.push(`Amazon reference: ${item.amazon_url}`);
  }
  if (item.camel_url) {
    facts.push(`CamelCamelCamel reference: ${item.camel_url}`);
  }
  if (item.shopbot_url) {
    facts.push(`Shopbot reference: ${item.shopbot_url}`);
  }

  elements.recommendationFacts.innerHTML = facts
    .map((fact) => `<div class="fact">${escapeHtml(fact)}</div>`)
    .join("");
}

function renderSeasonalProfile(rows) {
  elements.seasonalBody.innerHTML = rows.length
    ? rows
        .map(
          (row) => `
            <tr>
              <td>${escapeHtml(row.month_label)}</td>
              <td>${formatMoney(row.average_price)}</td>
            </tr>
          `,
        )
        .join("")
    : `<tr><td colspan="2">No seasonal profile is available for this item yet.</td></tr>`;
}

function renderSales(rows) {
  elements.salesBody.innerHTML = rows.length
    ? rows
        .map(
          (row) => `
            <tr>
              <td>${escapeHtml(row.sale_name)}</td>
              <td>${escapeHtml(new Date(`${row.target_date}T00:00:00`).toLocaleString("en-CA", { month: "long" }))}</td>
              <td>${escapeHtml(row.target_date)}</td>
              <td>${formatMoney(row.predicted_price)}</td>
            </tr>
          `,
        )
        .join("")
    : `<tr><td colspan="4">No upcoming sale forecasts are available.</td></tr>`;
}

function renderCandidates(rows) {
  if (!rows || rows.length === 0) {
    elements.candidateTableWrap.hidden = true;
    elements.candidateEmpty.hidden = false;
    return;
  }

  elements.candidateEmpty.hidden = true;
  elements.candidateTableWrap.hidden = false;
  elements.candidateBody.innerHTML = rows
    .map(
      (row) => `
        <tr>
          <td>${escapeHtml(row.item_name)}</td>
          <td>${escapeHtml(row.category || "unknown")}</td>
          <td>${row.score.toFixed(2)}</td>
        </tr>
      `,
    )
    .join("");
}

function trendValues(points) {
  return points
    .flatMap((row) => [row.actual_price, row.forecast_price])
    .filter((value) => value !== null && value !== undefined)
    .map(Number);
}

function buildPolyline(points, width, height, leftPad, topPad, color, dashed = false) {
  if (points.length < 2) {
    return "";
  }

  const dates = points.map((point) => new Date(`${point.date}T00:00:00`).getTime());
  const values = points.map((point) => Number(point.price));
  const minX = Math.min(...dates);
  const maxX = Math.max(...dates);
  const minY = Math.min(...values);
  const maxY = Math.max(...values);
  const plotWidth = width - leftPad - 18;
  const plotHeight = height - topPad - 26;
  const xRange = Math.max(maxX - minX, 1);
  const yRange = Math.max(maxY - minY, 1);

  const coords = points.map((point) => {
    const x = leftPad + ((new Date(`${point.date}T00:00:00`).getTime() - minX) / xRange) * plotWidth;
    const y = topPad + plotHeight - ((Number(point.price) - minY) / yRange) * plotHeight;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  return `<polyline fill="none" stroke="${color}" stroke-width="4" ${
    dashed ? 'stroke-dasharray="10 8"' : ""
  } stroke-linecap="round" stroke-linejoin="round" points="${coords.join(" ")}" />`;
}

function renderChart(container, rows) {
  container.innerHTML = "";
  if (!rows || rows.length === 0) {
    container.innerHTML = `<div class="subtle">Not enough history is available for this chart yet.</div>`;
    return;
  }

  const width = 760;
  const height = 250;
  const leftPad = 18;
  const topPad = 16;
  const values = trendValues(rows);
  const minPrice = Math.min(...values);
  const maxPrice = Math.max(...values);
  const actual = rows.filter((row) => row.actual_price !== null).map((row) => ({ date: row.date, price: row.actual_price }));
  const forecast = rows.filter((row) => row.forecast_price !== null).map((row) => ({ date: row.date, price: row.forecast_price }));

  const gridLines = [0, 1, 2, 3].map((index) => {
    const y = topPad + (index / 3) * (height - topPad - 26);
    return `<line x1="${leftPad}" y1="${y}" x2="${width - 18}" y2="${y}" stroke="rgba(61, 42, 27, 0.10)" stroke-width="1" />`;
  });

  const svg = `
    <svg class="chart-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="Price trend chart">
      ${gridLines.join("")}
      ${buildPolyline(actual, width, height, leftPad, topPad, "#40503d")}
      ${buildPolyline(forecast, width, height, leftPad, topPad, "#bf5b2c", true)}
      <text x="${leftPad}" y="${height - 6}" fill="#655b51" font-size="12">Low ${formatMoney(minPrice)}</text>
      <text x="${width - 96}" y="${height - 6}" fill="#655b51" font-size="12">High ${formatMoney(maxPrice)}</text>
    </svg>
    <div class="chart-legend">
      <span><span class="legend-swatch legend-actual"></span>Actual prices</span>
      <span><span class="legend-swatch legend-forecast"></span>Forecast prices</span>
    </div>
  `;

  container.innerHTML = svg;
}

function renderResult(payload) {
  const { item, prediction, seasonal_profile: seasonalProfile, trend_6m: trend6m, trend_1y: trend1y, llm_summary: llmSummary } =
    payload.result;

  elements.results.hidden = false;
  elements.resultCategory.textContent = item.category || "Tracked item";
  elements.resultTitle.textContent = item.item_name;
  elements.resultSource.textContent = payload.source || "";
  elements.currentSourceChip.textContent = `Current price source: ${item.current_price_source || "unknown"} • ${
    item.current_price_date || prediction.reference_date
  }`;

  elements.metricCurrent.textContent = formatMoney(item.current_price ?? item.latest_price);
  elements.metricAction.textContent = prediction.recommendation;
  elements.metricTarget.textContent = formatMoney(prediction.target_price);
  elements.metricWindow.textContent = prediction.buy_window;
  elements.metricConfidence.textContent = prediction.confidence;

  elements.best30.textContent = formatWindow(prediction.best_price_windows["30"]);
  elements.best60.textContent = formatWindow(prediction.best_price_windows["60"]);
  elements.best90.textContent = formatWindow(prediction.best_price_windows["90"]);
  elements.forecast30.textContent = formatMoney(prediction.forecast_prices["30"].price);
  elements.forecast60.textContent = formatMoney(prediction.forecast_prices["60"].price);
  elements.forecast90.textContent = formatMoney(prediction.forecast_prices["90"].price);

  elements.recommendationReason.textContent = prediction.reason;
  renderFacts(item, prediction);
  renderSeasonalProfile(seasonalProfile);
  renderSales(prediction.future_sale_forecasts || []);
  renderCandidates(payload.candidates || []);
  renderChart(elements.chart6m, trend6m);
  renderChart(elements.chart1y, trend1y);

  if (llmSummary) {
    elements.llmCard.hidden = false;
    elements.llmSummary.textContent = llmSummary;
  } else {
    elements.llmCard.hidden = true;
    elements.llmSummary.textContent = "";
  }
}

async function loadHealth() {
  try {
    const response = await fetch("/api/health");
    const data = await response.json();
    if (!response.ok || !data.ok) {
      setHealth("Gold data missing");
      showMessage(data.message || "Gold-layer data is not available yet.", "error");
      return;
    }
    setHealth(`${data.catalog_size} tracked items ready`, true);
  } catch (_error) {
    setHealth("Health check failed");
  showMessage("Could not reach the API. If you are running locally, start the Flask app with `python index.py`.", "error");
  }
}

async function requestAndRender(url, options = {}) {
  clearMessage();

  try {
    const response = await fetch(url, options);
    const data = await response.json();

    if (!response.ok || !data.ok) {
      elements.results.hidden = true;
      showMessage(data.message || data.source || "No matching item was found.", "error");
      renderCandidates(data.candidates || []);
      return;
    }

    renderResult(data);
    showMessage(data.source || "Result loaded.", "success");
  } catch (_error) {
    elements.results.hidden = true;
    showMessage("The request failed before the dashboard could render a result.", "error");
  }
}

elements.searchForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = elements.queryInput.value.trim();
  if (!query) {
    showMessage("Type a product name before searching.", "error");
    return;
  }

  const params = new URLSearchParams({ q: query });
  if (elements.summaryToggle.checked) {
    params.set("summary", "true");
  }

  await requestAndRender(`/api/search?${params.toString()}`);
});

elements.imageForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const image = elements.imageInput.files?.[0];
  if (!image) {
    showMessage("Choose a product image before running image analysis.", "error");
    return;
  }

  const formData = new FormData();
  formData.append("image", image);
  if (elements.summaryToggle.checked) {
    formData.append("summary", "true");
  }

  await requestAndRender("/api/identify-image", {
    method: "POST",
    body: formData,
  });
});

loadHealth();
