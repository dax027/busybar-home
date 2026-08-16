const grid = document.querySelector("#scene-grid");
const stage = document.querySelector("#device-stage");
const frontPreview = document.querySelector("#front-preview");
const backPreview = document.querySelector("#back-preview");
const backCue = document.querySelector("#back-cue");
const previewScene = document.querySelector("#preview-scene");
const deviceMode = document.querySelector("#device-mode");
const connectionPill = document.querySelector("#connection-pill");
const toast = document.querySelector("#toast");
const refreshStatusButton = document.querySelector("#refresh-status");
const deviceName = document.querySelector("#device-name");
const statusBattery = document.querySelector("#status-battery");
const statusPower = document.querySelector("#status-power");
const statusFirmware = document.querySelector("#status-firmware");
const statusApi = document.querySelector("#status-api");
const statusUptime = document.querySelector("#status-uptime");
const statusNote = document.querySelector("#status-note");
const batteryMeterLevel = document.querySelector("#battery-meter-level");

let toastTimer = null;
let deviceLabel = "BUSY Bar";

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("visible");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("visible"), 2200);
}

function displayValue(value) {
  return value === null || value === undefined || value === "" ? "Unavailable" : String(value);
}

function titleCase(value) {
  const text = displayValue(value);
  return text === "Unavailable" ? text : text.replaceAll("_", " ").replace(/^./, (letter) => letter.toUpperCase());
}

function renderDeviceStatus(status) {
  connectionPill.classList.toggle("is-offline", !status.connected);
  const connectionLabel = `${deviceLabel} ${status.connected ? "online" : "offline"}`;
  deviceMode.textContent = connectionLabel;
  connectionPill.setAttribute("aria-label", connectionLabel);
  deviceName.textContent = displayValue(status.device_name);
  statusBattery.textContent = status.battery_percent === null ? "Unavailable" : `${status.battery_percent}%`;
  statusPower.textContent = titleCase(status.power_state);
  statusFirmware.textContent = displayValue(status.firmware_version);
  statusApi.textContent = displayValue(status.api_version);
  statusUptime.textContent = displayValue(status.uptime);
  const batteryLevel = status.battery_percent ?? 0;
  batteryMeterLevel.style.width = `${Math.max(0, Math.min(100, batteryLevel))}%`;
  statusNote.textContent = "Updated just now · Status refreshes only when requested.";
}

async function refreshDeviceStatus() {
  refreshStatusButton.disabled = true;
  statusNote.textContent = "Reading device status…";
  try {
    const response = await fetch("/api/device/status");
    if (!response.ok) throw new Error("Device status unavailable");
    renderDeviceStatus(await response.json());
  } catch (error) {
    connectionPill.classList.add("is-offline");
    deviceMode.textContent = `${deviceLabel} offline`;
    connectionPill.setAttribute("aria-label", `${deviceLabel} offline`);
    statusNote.textContent = "Could not read device status. Try again when the BUSY Bar is available.";
    showToast(error.message || "Could not read device status");
  } finally {
    refreshStatusButton.disabled = false;
  }
}

function setPreview(preset) {
  stage.classList.toggle("terminal-scene", preset.front_style === "terminal");
  stage.classList.toggle("cyberpunk-scene", preset.front_style === "cyberpunk");
  stage.classList.toggle("low-battery-scene", preset.front_style === "low_battery");
  stage.classList.toggle("daydream-scene", preset.front_style === "daydream");
  frontPreview.replaceChildren();
  if (preset.front_style === "terminal") {
    frontPreview.append(document.createTextNode(`> ${preset.front.text}`));
    const cursor = document.createElement("span");
    cursor.className = "front-cursor";
    cursor.textContent = "_";
    frontPreview.append(cursor);
  } else if (preset.front_style === "low_battery") {
    const battery = document.createElement("span");
    battery.className = "battery-glyph";
    battery.setAttribute("aria-hidden", "true");
    const copy = document.createElement("span");
    copy.className = "battery-copy";
    const label = document.createElement("span");
    label.className = "battery-label";
    label.textContent = preset.front.text;
    const subLabel = document.createElement("span");
    subLabel.className = "battery-sub-label";
    subLabel.textContent = "BATTERY";
    copy.append(label, subLabel);
    frontPreview.append(battery, copy);
  } else if (preset.front_style === "daydream") {
    const leftCloud = document.createElement("span");
    leftCloud.className = "daydream-cloud daydream-cloud-left";
    leftCloud.setAttribute("aria-hidden", "true");
    const label = document.createElement("span");
    label.className = "daydream-label";
    label.textContent = preset.front.text;
    const rightCloud = document.createElement("span");
    rightCloud.className = "daydream-cloud daydream-cloud-right";
    rightCloud.setAttribute("aria-hidden", "true");
    frontPreview.append(leftCloud, label, rightCloud);
  } else {
    frontPreview.textContent = preset.front.text;
  }
  backPreview.textContent = preset.back.text;
  backCue.textContent = preset.rear_cue;
  previewScene.textContent = preset.label;
  stage.style.setProperty("--scene-color", preset.front.color);
}

function render(state) {
  deviceLabel = state.device_mode === "fake" ? "Demo" : "BUSY Bar";
  deviceMode.textContent = `${deviceLabel} device`;
  grid.replaceChildren();

  state.presets.forEach((preset) => {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "scene-card";
    card.classList.toggle("terminal-scene", preset.front_style === "terminal");
    card.classList.toggle("cyberpunk-scene", preset.front_style === "cyberpunk");
    card.classList.toggle("low-battery-scene", preset.front_style === "low_battery");
    card.classList.toggle("daydream-scene", preset.front_style === "daydream");
    card.classList.toggle("active", preset.id === state.active_preset);
    card.style.setProperty("--card-color", preset.front.color);
    card.setAttribute("aria-pressed", String(preset.id === state.active_preset));
    const frontText = preset.front_style === "terminal"
      ? `&gt; ${preset.front.text}<span class="front-cursor">_</span>`
      : preset.front_style === "low_battery"
        ? `<span class="battery-glyph" aria-hidden="true"></span><span class="battery-copy"><span class="battery-label">${preset.front.text}</span><span class="battery-sub-label">BATTERY</span></span>`
      : preset.front_style === "daydream"
        ? `<span class="daydream-cloud daydream-cloud-left" aria-hidden="true"></span><span class="daydream-label">${preset.front.text}</span><span class="daydream-cloud daydream-cloud-right" aria-hidden="true"></span>`
      : preset.front.text;
    card.innerHTML = `
      <span class="card-display">${frontText}</span>
      <span class="scene-title"><span>${preset.label}</span><i aria-hidden="true"></i></span>
      <p>${preset.description}</p>
      <span class="card-action">Set scene →</span>
    `;
    card.addEventListener("mouseenter", () => setPreview(preset));
    card.addEventListener("focus", () => setPreview(preset));
    card.addEventListener("click", () => activate(preset, card));
    grid.append(card);
  });

  const active = state.presets.find((preset) => preset.id === state.active_preset);
  setPreview(active || state.presets[0]);
}

async function activate(preset, card) {
  card.disabled = true;
  try {
    const response = await fetch(`/api/presets/${preset.id}/activate`, { method: "POST" });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.detail || "Device command failed");
    }
    const payload = await response.json();
    render(payload.state);
    showToast(`${preset.label} is now active`);
  } catch (error) {
    showToast(error.message || "Could not update the display");
  } finally {
    card.disabled = false;
  }
}

fetch("/api/dashboard")
  .then((response) => {
    if (!response.ok) throw new Error("Dashboard unavailable");
    return response.json();
  })
  .then(render)
  .then(refreshDeviceStatus)
  .catch(() => {
    deviceMode.textContent = "Offline";
    showToast("Dashboard could not load");
  });

refreshStatusButton.addEventListener("click", refreshDeviceStatus);
