async (page) => {
  const fs = require("fs");
  const path = require("path");

  const projectRoot = process.cwd();
  const styles = fs.readFileSync(path.join(projectRoot, "public", "styles.css"), "utf-8");
  const appScript = fs.readFileSync(path.join(projectRoot, "public", "app.js"), "utf-8");

  const searchPayload = {
    ok: true,
    query: "echo",
    source: "Text search matched 'Amazon Echo Dot (5th Gen)' with score 0.62.",
    result: {
      item: {
        item_id: "amazon_echo_dot",
        item_name: "Amazon Echo Dot (5th Gen)",
        category: "smart_home",
        latest_price: 26.99,
        current_price: 26.99,
        current_price_date: "2026-03-31",
        current_price_source: "shopbot_injection",
        available_sources: ["camelcamelcamel_injection", "sample_seed", "shopbot_injection"],
        camel_url: "https://camelcamelcamel.com/product/B0XXXXX1",
        shopbot_url: null,
      },
      prediction: {
        recommendation: "Buy now",
        reason:
          "The current price ($26.99) is already near the historical low ($25.99) and within 2% of the best near-term forecast.",
        target_price: 23.89,
        buy_window: "Now",
        confidence: "High",
        price_vs_average_pct: -21.2,
        price_vs_low_pct: 3.8,
        best_buy_months: [11, 7, 3],
        best_price_windows: {
          "30": { price: 26.99, date: "2026-03-31" },
          "60": { price: 26.99, date: "2026-03-31" },
          "90": { price: 26.99, date: "2026-03-31" },
        },
        forecast_prices: {
          "30": { date: "2026-04-30", price: 29.01 },
          "60": { date: "2026-05-30", price: 28.68 },
          "90": { date: "2026-06-29", price: 28.34 },
        },
        future_sale_forecasts: [
          {
            sale_name: "Spring Sale",
            sale_month: 3,
            target_date: "2027-03-15",
            predicted_price: 24.53,
          },
          {
            sale_name: "Prime Day",
            sale_month: 7,
            target_date: "2026-07-15",
            predicted_price: 26.67,
          },
          {
            sale_name: "Black Friday / Cyber Monday",
            sale_month: 11,
            target_date: "2026-11-15",
            predicted_price: 23.89,
          },
        ],
        next_sale_name: "Spring Sale",
        reference_date: "2026-03-31",
      },
      seasonal_profile: [
        { month_number: 1, month_label: "January", average_price: 39.66 },
        { month_number: 3, month_label: "March", average_price: 31.66 },
        { month_number: 7, month_label: "July", average_price: 29.99 },
        { month_number: 11, month_label: "November", average_price: 25.99 },
      ],
      trend_6m: [
        { date: "2026-01-15", actual_price: 34.99, forecast_price: null },
        { date: "2026-02-20", actual_price: 29.99, forecast_price: null },
        { date: "2026-03-31", actual_price: 26.99, forecast_price: null },
        { date: "2026-04-30", actual_price: null, forecast_price: 29.01 },
        { date: "2026-05-30", actual_price: null, forecast_price: 28.68 },
        { date: "2026-06-29", actual_price: null, forecast_price: 28.34 },
      ],
      trend_1y: [
        { date: "2026-01-15", actual_price: 34.99, forecast_price: null },
        { date: "2026-02-20", actual_price: 29.99, forecast_price: null },
        { date: "2026-03-31", actual_price: 26.99, forecast_price: null },
        { date: "2026-04-30", actual_price: null, forecast_price: 29.01 },
        { date: "2026-05-30", actual_price: null, forecast_price: 28.68 },
        { date: "2026-06-29", actual_price: null, forecast_price: 28.34 },
      ],
    },
    candidates: [
      { item_id: "fire_tv_stick", item_name: "Amazon Fire TV Stick 4K", category: "smart_home", score: 0.29 },
    ],
  };

  const html = `
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Shopping Price Advisor</title>
        <style>${styles}</style>
      </head>
      <body>
        <div class="page-shell">
          <header class="hero">
            <div class="eyebrow">Assignment 5 • End-to-End AI Application</div>
            <h1>Shopping Price Advisor</h1>
            <p class="lede">Search by item name or upload a product photo to compare current and forecasted prices.</p>
            <div class="hero-meta">
              <span id="health-pill" class="pill pill-muted">Checking data…</span>
            </div>
          </header>

          <main class="layout">
            <section class="control-panel card">
              <div class="panel-heading">
                <h2>Find a Product</h2>
                <p>Use text search for the fastest path.</p>
              </div>
              <form id="search-form" class="stack">
                <label class="field">
                  <span>Search by item name</span>
                  <div class="inline-input">
                    <input id="query-input" name="q" type="text" placeholder="Amazon Echo Dot" />
                    <button type="submit" class="button button-primary">Search</button>
                  </div>
                </label>
              </form>
              <form id="image-form" class="stack">
                <label class="field">
                  <span>Upload a product image</span>
                  <div class="inline-input inline-input-file">
                    <input id="image-input" name="image" type="file" accept=".png,.jpg,.jpeg" />
                    <button type="submit" class="button button-secondary">Analyze Photo</button>
                  </div>
                </label>
              </form>
              <label class="toggle">
                <input id="summary-toggle" type="checkbox" />
                <span>Include optional LLM summary</span>
              </label>
              <div id="message-banner" class="message-banner" hidden></div>
            </section>

            <section id="results" class="results" hidden>
              <article class="card result-hero">
                <div>
                  <div id="result-category" class="eyebrow">Tracked item</div>
                  <h2 id="result-title">Item title</h2>
                  <p id="result-source" class="subtle"></p>
                </div>
                <div class="source-chip-group">
                  <span id="current-source-chip" class="pill pill-dark"></span>
                </div>
              </article>

              <section class="metric-grid">
                <article class="card metric-card"><div class="metric-label">Current Price</div><div id="metric-current" class="metric-value"></div></article>
                <article class="card metric-card accent-card"><div class="metric-label">Recommendation</div><div id="metric-action" class="metric-value"></div></article>
                <article class="card metric-card"><div class="metric-label">Target Price</div><div id="metric-target" class="metric-value"></div></article>
                <article class="card metric-card"><div class="metric-label">Buy Window</div><div id="metric-window" class="metric-value"></div></article>
                <article class="card metric-card"><div class="metric-label">Confidence</div><div id="metric-confidence" class="metric-value"></div></article>
              </section>

              <section class="metric-grid metric-grid-small">
                <article class="card detail-card"><div class="metric-label">Best 30 Days</div><div id="best-30" class="detail-value"></div></article>
                <article class="card detail-card"><div class="metric-label">Best 60 Days</div><div id="best-60" class="detail-value"></div></article>
                <article class="card detail-card"><div class="metric-label">Best 90 Days</div><div id="best-90" class="detail-value"></div></article>
                <article class="card detail-card"><div class="metric-label">Forecast 30 Days</div><div id="forecast-30" class="detail-value"></div></article>
                <article class="card detail-card"><div class="metric-label">Forecast 60 Days</div><div id="forecast-60" class="detail-value"></div></article>
                <article class="card detail-card"><div class="metric-label">Forecast 90 Days</div><div id="forecast-90" class="detail-value"></div></article>
              </section>

              <section class="split-grid">
                <article class="card prose-card">
                  <h3>Recommendation Summary</h3>
                  <p id="recommendation-reason"></p>
                  <div id="recommendation-facts" class="fact-list"></div>
                </article>
                <article class="card prose-card">
                  <h3>Seasonal Profile</h3>
                  <div class="table-wrap">
                    <table><tbody id="seasonal-body"></tbody></table>
                  </div>
                </article>
              </section>

              <section class="split-grid">
                <article class="card chart-card">
                  <div class="chart-header"><h3>6-Month Trend</h3></div>
                  <div id="chart-6m" class="chart-shell"></div>
                </article>
                <article class="card chart-card">
                  <div class="chart-header"><h3>1-Year Trend</h3></div>
                  <div id="chart-1y" class="chart-shell"></div>
                </article>
              </section>

              <section class="split-grid">
                <article class="card prose-card">
                  <h3>Upcoming Sale Forecasts</h3>
                  <div class="table-wrap">
                    <table><tbody id="sales-body"></tbody></table>
                  </div>
                </article>
                <article class="card prose-card">
                  <h3>Alternate Matches</h3>
                  <div id="candidate-empty" class="subtle">Closest alternate text matches will appear here when available.</div>
                  <div class="table-wrap" id="candidate-table-wrap" hidden>
                    <table><tbody id="candidate-body"></tbody></table>
                  </div>
                </article>
              </section>

              <article id="llm-card" class="card prose-card" hidden>
                <h3>LLM Summary</h3>
                <p id="llm-summary"></p>
              </article>
            </section>
          </main>
        </div>
      </body>
    </html>
  `;

  await page.route("**/api/health", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ ok: true, status: "ready", catalog_size: 4 }),
    });
  });

  await page.route("**/api/search?*", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(searchPayload),
    });
  });

  await page.route("**/api/identify-image", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(searchPayload),
    });
  });

  await page.goto("https://example.com", { waitUntil: "domcontentloaded" });
  await page.setContent(html, { waitUntil: "domcontentloaded" });
  await page.addScriptTag({ content: appScript });
  await page.locator("#query-input").fill("echo");
  await page.getByRole("button", { name: "Search" }).click();
  await page.waitForFunction(() => !document.getElementById("results").hidden);

  return {
    title: await page.locator("#result-title").textContent(),
    currentPrice: await page.locator("#metric-current").textContent(),
    action: await page.locator("#metric-action").textContent(),
    health: await page.locator("#health-pill").textContent(),
    chartRendered: (await page.locator("#chart-6m svg").count()) > 0,
    saleRows: await page.locator("#sales-body tr").count(),
  };
}
