const REFRESH_MS = 8000;

const grid = document.getElementById("service-grid");
const emptyState = document.getElementById("empty-state");
const summaryLine = document.getElementById("summary-line");
const form = document.getElementById("add-service-form");
const toggleFormBtn = document.getElementById("toggle-form-btn");
const cancelFormBtn = document.getElementById("cancel-form-btn");

toggleFormBtn.addEventListener("click", () => form.classList.toggle("hidden"));
cancelFormBtn.addEventListener("click", () => form.classList.add("hidden"));

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = {
    name: document.getElementById("name").value,
    url: document.getElementById("url").value,
    method: document.getElementById("method").value,
    expected_status: Number(document.getElementById("expected_status").value),
    check_interval_seconds: Number(document.getElementById("check_interval_seconds").value),
  };

  const response = await fetch("/api/services", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (response.ok) {
    form.reset();
    form.classList.add("hidden");
    loadStatus();
  } else {
    alert("Could not add service. Check the fields and try again.");
  }
});

async function deleteService(id) {
  if (!confirm("Remove this service from monitoring?")) return;
  await fetch(`/api/services/${id}`, { method: "DELETE" });
  loadStatus();
}

function pillClass(status) {
  if (status === "up") return "pill pill-up";
  if (status === "down") return "pill pill-down";
  return "pill pill-unknown";
}

function renderUptimeStrip(history) {
  // Pad to 24 slots on the left so a new service starts with empty (unknown) blocks.
  const padded = Array(Math.max(0, 24 - history.length)).fill("unknown").concat(history);
  return padded
    .map((status) => `<span class="uptime-block ${status}"></span>`)
    .join("");
}

function renderCard(item) {
  const { service, current_status, response_time_ms, uptime_percent_24h, recent_history } = item;
  return `
    <article class="card">
      <div class="card-header">
        <div>
          <div class="card-name">${escapeHtml(service.name)}</div>
        </div>
        <span class="${pillClass(current_status)}">${current_status}</span>
      </div>
      <p class="card-url">${escapeHtml(service.method)} ${escapeHtml(service.url)}</p>
      <div class="uptime-strip">${renderUptimeStrip(recent_history)}</div>
      <div class="card-meta">
        <span>Uptime (24h) <strong>${uptime_percent_24h}%</strong></span>
        <span>Latency <strong>${response_time_ms != null ? response_time_ms + "ms" : "—"}</strong></span>
      </div>
      <div class="card-footer">
        <button class="link-danger" onclick="deleteService(${service.id})">Remove</button>
      </div>
    </article>
  `;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

async function loadStatus() {
  try {
    const response = await fetch("/api/status");
    const items = await response.json();

    if (items.length === 0) {
      grid.innerHTML = "";
      emptyState.classList.remove("hidden");
      summaryLine.textContent = "0 services monitored";
      return;
    }

    emptyState.classList.add("hidden");
    grid.innerHTML = items.map(renderCard).join("");

    const upCount = items.filter((i) => i.current_status === "up").length;
    summaryLine.textContent = `${upCount}/${items.length} services up`;
  } catch (err) {
    summaryLine.textContent = "Could not reach the API";
  }
}

loadStatus();
setInterval(loadStatus, REFRESH_MS);
