const form = document.getElementById("search-form");
const resultsEl = document.getElementById("results");
const noticeEl = document.getElementById("notice");
const statusMessageEl = document.getElementById("status-message");
const submitButton = form.querySelector("button[type=submit]");

function showNotice(text) {
  if (!text) {
    noticeEl.classList.add("hidden");
    return;
  }
  noticeEl.textContent = text;
  noticeEl.classList.remove("hidden");
}

function showStatusMessage(text, variant = "error") {
  if (!text) {
    statusMessageEl.classList.add("hidden");
    return;
  }
  statusMessageEl.textContent = text;
  statusMessageEl.className = variant === "info" ? "status-message info" : "status-message";
}

function clearStatusMessage() {
  statusMessageEl.classList.add("hidden");
}

function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = value ?? "";
  return div.innerHTML;
}

function renderAds(ads) {
  if (ads.length === 0) {
    resultsEl.innerHTML = "";
    showStatusMessage("Không tìm thấy quảng cáo phù hợp với keyword.", "info");
    return;
  }
  clearStatusMessage();

  resultsEl.innerHTML = ads
    .map((ad) => {
      const statusClass = ad.status === "ACTIVE" ? "active" : "inactive";
      const platforms = (ad.platforms || []).join(", ") || "—";
      const started = ad.start_date || "—";

      const landingButton = ad.landing_url
        ? `<a href="${escapeHtml(ad.landing_url)}" target="_blank" rel="noopener">Open Landing Page</a>`
        : "";
      const libraryButton = ad.ad_library_url
        ? `<a class="primary" href="${escapeHtml(ad.ad_library_url)}" target="_blank" rel="noopener">Open Ad Library</a>`
        : "";

      return `
        <article class="ad-card">
          <div class="page-name">${escapeHtml(ad.page_name || "(Unknown page)")}</div>
          ${ad.headline ? `<p class="headline">${escapeHtml(ad.headline)}</p>` : ""}
          ${ad.body ? `<p class="body-text">${escapeHtml(ad.body)}</p>` : ""}
          ${ad.description ? `<p class="description">${escapeHtml(ad.description)}</p>` : ""}
          <div class="meta-row">
            <span><span class="badge ${statusClass}">${escapeHtml(ad.status || "UNKNOWN")}</span></span>
            <span>Started: ${escapeHtml(started)}</span>
            <span>Platforms: ${escapeHtml(platforms)}</span>
          </div>
          <div class="actions">
            ${libraryButton}
            ${landingButton}
          </div>
        </article>
      `;
    })
    .join("");
}

async function handleErrorResponse(response) {
  let message = `Lỗi không xác định (HTTP ${response.status}).`;
  try {
    const body = await response.json();
    if (body.error) message = body.error;
    else if (body.detail) message = body.detail;
  } catch (_) {
    // ignore body parse failure, keep default message
  }
  showStatusMessage(message, "error");
  resultsEl.innerHTML = "";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const keyword = document.getElementById("keyword").value.trim();
  if (!keyword) return;

  const country = document.getElementById("country").value;
  const status = document.getElementById("status").value;
  const adType = document.getElementById("ad_type").value;

  submitButton.disabled = true;
  submitButton.textContent = "Searching...";
  clearStatusMessage();
  showNotice(null);
  resultsEl.innerHTML = "";

  const params = new URLSearchParams({ keyword, country, status, ad_type: adType });

  try {
    const response = await fetch(`/api/ads/search?${params.toString()}`);
    if (!response.ok) {
      await handleErrorResponse(response);
      return;
    }
    const payload = await response.json();
    showNotice(payload.meta?.limitation_notice);
    renderAds(payload.data || []);
  } catch (error) {
    showStatusMessage("Không thể kết nối tới máy chủ. Vui lòng kiểm tra kết nối mạng và thử lại.", "error");
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = "Search Ads";
  }
});
