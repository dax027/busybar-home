const grid = document.querySelector("#scene-grid");
const stage = document.querySelector("#device-stage");
const frontPreviewFallback = document.querySelector("#front-preview-fallback");
const liveFrontPreview = document.querySelector("#live-front-preview");
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
const tickerForm = document.querySelector("#ticker-form");
const tickerMessage = document.querySelector("#ticker-message");
const tickerCharacterCount = document.querySelector("#ticker-character-count");
const tickerFontColor = document.querySelector("#ticker-font-color");
const tickerFontColorValue = document.querySelector("#ticker-font-color-value");
const tickerBackgroundColor = document.querySelector("#ticker-background-color");
const tickerBackgroundColorValue = document.querySelector("#ticker-background-color-value");
const tickerSpeed = document.querySelector("#ticker-speed");
const tickerSpeedValue = document.querySelector("#ticker-speed-value");
const tickerPreview = document.querySelector("#ticker-preview");
const tickerPreviewIndicator = document.querySelector("#ticker-preview-indicator");
const tickerPreviewNote = document.querySelector("#ticker-preview-note");
const tickerDeployButton = document.querySelector("#ticker-deploy");

let toastTimer = null;
let deviceLabel = "BUSY Bar";
let tickerPreviewTimer = null;
let tickerPreviewUrl = null;
let tickerPreviewRequest = null;
let deviceClientMode = "fake";
let liveFrameSocket = null;
let liveFrameReconnectTimer = null;
let liveFrameFailures = 0;
let selectedPreviewLabel = "Choose a scene";

const FRONT_SCREEN_WIDTH = 72;
const FRONT_SCREEN_HEIGHT = 16;
const FRONT_SCREEN_RGB_BYTES = FRONT_SCREEN_WIDTH * FRONT_SCREEN_HEIGHT * 3;
const LIVE_FRAME_RECONNECT_MS = 1500;
const liveFrontContext = liveFrontPreview.getContext("2d");
const liveFrontImage = liveFrontContext.createImageData(FRONT_SCREEN_WIDTH, FRONT_SCREEN_HEIGHT);

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

function showLiveFrameFallback() {
  stage.classList.remove("has-live-frame");
  liveFrontPreview.hidden = true;
  frontPreviewFallback.hidden = false;
  previewScene.textContent = selectedPreviewLabel;
}

function paintRgbFrame(rgb, image, context) {
  const rgba = image.data;
  for (let source = 0, target = 0; source < rgb.length; source += 3, target += 4) {
    rgba[target] = rgb[source];
    rgba[target + 1] = rgb[source + 1];
    rgba[target + 2] = rgb[source + 2];
    rgba[target + 3] = 255;
  }
  context.putImageData(image, 0, 0);
}

function drawLiveFrontFrame(buffer) {
  const rgb = new Uint8Array(buffer);
  if (rgb.byteLength !== FRONT_SCREEN_RGB_BYTES) return;
  paintRgbFrame(rgb, liveFrontImage, liveFrontContext);
  liveFrontPreview.hidden = false;
  frontPreviewFallback.hidden = true;
  stage.classList.add("has-live-frame");
  previewScene.textContent = "Device now";
  liveFrameFailures = 0;
}

function scheduleLiveFrontReconnect() {
  clearTimeout(liveFrameReconnectTimer);
  if (deviceClientMode !== "official" || document.hidden) return;
  liveFrameReconnectTimer = window.setTimeout(connectLiveFrontPreview, LIVE_FRAME_RECONNECT_MS);
}

function connectLiveFrontPreview() {
  if (
    deviceClientMode !== "official" ||
    document.hidden ||
    liveFrameSocket?.readyState === WebSocket.CONNECTING ||
    liveFrameSocket?.readyState === WebSocket.OPEN
  ) return;

  clearTimeout(liveFrameReconnectTimer);
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const socket = new WebSocket(`${protocol}//${window.location.host}/ws/device/screen/front`);
  socket.binaryType = "arraybuffer";
  liveFrameSocket = socket;

  socket.addEventListener("message", (event) => {
    if (event.data instanceof ArrayBuffer) drawLiveFrontFrame(event.data);
  });
  socket.addEventListener("close", () => {
    if (liveFrameSocket === socket) liveFrameSocket = null;
    liveFrameFailures += 1;
    if (liveFrameFailures >= 3) showLiveFrameFallback();
    scheduleLiveFrontReconnect();
  });
}

function disconnectLiveFrontPreview() {
  clearTimeout(liveFrameReconnectTimer);
  liveFrameReconnectTimer = null;
  if (!liveFrameSocket) return;
  const socket = liveFrameSocket;
  liveFrameSocket = null;
  socket.close(1000, "Dashboard paused");
}

function startLiveFrontPreview() {
  connectLiveFrontPreview();
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
  selectedPreviewLabel = preset.label;
  stage.classList.toggle("terminal-scene", preset.front_style === "terminal");
  stage.classList.toggle("cyberpunk-scene", preset.front_style === "cyberpunk");
  stage.classList.toggle("low-battery-scene", preset.front_style === "low_battery");
  stage.classList.toggle("daydream-scene", preset.front_style === "daydream");
  frontPreviewFallback.replaceChildren();
  if (preset.front_preview) {
    const preview = document.createElement("img");
    preview.className = "native-animation-preview";
    preview.src = preset.front_preview;
    preview.alt = `${preset.label} animated front display`;
    frontPreviewFallback.append(preview);
  } else if (preset.front_style === "terminal") {
    frontPreviewFallback.append(document.createTextNode(`> ${preset.front.text}`));
    const cursor = document.createElement("span");
    cursor.className = "front-cursor";
    cursor.textContent = "_";
    frontPreviewFallback.append(cursor);
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
    frontPreviewFallback.append(battery, copy);
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
    frontPreviewFallback.append(leftCloud, label, rightCloud);
  } else {
    frontPreviewFallback.textContent = preset.front.text;
  }
  previewScene.textContent = stage.classList.contains("has-live-frame")
    ? "Device now"
    : selectedPreviewLabel;
  stage.style.setProperty("--scene-color", preset.front.color);
}

function render(state) {
  deviceClientMode = state.device_mode;
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
    const frontText = preset.front_preview
      ? `<img class="native-animation-preview" src="${preset.front_preview}" alt="${preset.label} animated front display">`
      : preset.front_style === "terminal"
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
    connectLiveFrontPreview();
    showToast(`${preset.label} is now active`);
  } catch (error) {
    showToast(error.message || "Could not update the display");
  } finally {
    card.disabled = false;
  }
}

function tickerPayload() {
  const effect = tickerForm.querySelector('input[name="ticker-effect"]:checked');
  return {
    message: tickerMessage.value,
    font_color: tickerFontColor.value.toUpperCase(),
    background_color: tickerBackgroundColor.value.toUpperCase(),
    speed: Number(tickerSpeed.value),
    effect: effect.value,
  };
}

function syncTickerLabels() {
  tickerCharacterCount.textContent = String(tickerMessage.value.length);
  tickerFontColorValue.textContent = tickerFontColor.value.toUpperCase();
  tickerBackgroundColorValue.textContent = tickerBackgroundColor.value.toUpperCase();
  tickerSpeedValue.textContent = `${tickerSpeed.value} px/s`;
}

function errorDetail(payload, fallback) {
  if (typeof payload.detail === "string") return payload.detail;
  if (Array.isArray(payload.detail) && payload.detail[0]?.msg) return payload.detail[0].msg;
  return fallback;
}

async function refreshTickerPreview() {
  syncTickerLabels();
  if (!tickerMessage.value.trim()) {
    tickerPreviewIndicator.textContent = "Needs a message";
    tickerPreviewIndicator.classList.add("is-error");
    tickerPreviewNote.textContent = "Enter a message to generate the preview.";
    return;
  }

  tickerPreviewRequest?.abort();
  tickerPreviewRequest = new AbortController();
  tickerPreviewIndicator.textContent = "Rendering";
  tickerPreviewIndicator.classList.remove("is-error");
  try {
    const response = await fetch("/api/ticker/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(tickerPayload()),
      signal: tickerPreviewRequest.signal,
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(errorDetail(payload, "Preview could not be generated"));
    }
    const previewUrl = URL.createObjectURL(await response.blob());
    if (tickerPreviewUrl) URL.revokeObjectURL(tickerPreviewUrl);
    tickerPreviewUrl = previewUrl;
    tickerPreview.src = previewUrl;
    tickerPreviewIndicator.textContent = "Ready";
    tickerPreviewNote.textContent = "This animation uses the same frames that will be sent to the device.";
  } catch (error) {
    if (error.name === "AbortError") return;
    tickerPreviewIndicator.textContent = "Preview error";
    tickerPreviewIndicator.classList.add("is-error");
    tickerPreviewNote.textContent = error.message || "Preview could not be generated.";
  }
}

function queueTickerPreview() {
  syncTickerLabels();
  clearTimeout(tickerPreviewTimer);
  tickerPreviewTimer = setTimeout(refreshTickerPreview, 220);
}

function showTickerOnStage() {
  stage.classList.remove("terminal-scene", "cyberpunk-scene", "low-battery-scene", "daydream-scene");
  frontPreviewFallback.replaceChildren();
  const preview = document.createElement("img");
  preview.className = "native-animation-preview";
  preview.src = tickerPreview.src;
  preview.alt = "Active custom ticker";
  frontPreviewFallback.append(preview);
  previewScene.textContent = "Custom ticker";
  stage.style.setProperty("--scene-color", tickerFontColor.value);
}

async function deployTicker(event) {
  event.preventDefault();
  tickerDeployButton.disabled = true;
  tickerDeployButton.textContent = "Deploying…";
  try {
    const response = await fetch("/api/ticker/deploy", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(tickerPayload()),
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(errorDetail(payload, "Ticker deployment failed"));
    }
    const payload = await response.json();
    document.querySelectorAll(".scene-card").forEach((card) => {
      card.classList.remove("active");
      card.setAttribute("aria-pressed", "false");
    });
    showTickerOnStage();
    renderDeviceStatus(payload.device);
    connectLiveFrontPreview();
    showToast("Custom ticker is now active");
  } catch (error) {
    showToast(error.message || "Ticker deployment failed");
  } finally {
    tickerDeployButton.disabled = false;
    tickerDeployButton.textContent = "Deploy to BUSY Bar";
  }
}

fetch("/api/dashboard")
  .then((response) => {
    if (!response.ok) throw new Error("Dashboard unavailable");
    return response.json();
  })
  .then((state) => {
    render(state);
    startLiveFrontPreview();
    return refreshDeviceStatus();
  })
  .catch(() => {
    deviceMode.textContent = "Offline";
    showToast("Dashboard could not load");
  });

refreshStatusButton.addEventListener("click", refreshDeviceStatus);
tickerForm.addEventListener("input", queueTickerPreview);
tickerForm.addEventListener("change", queueTickerPreview);
tickerForm.addEventListener("submit", deployTicker);
document.addEventListener("visibilitychange", () => {
  if (document.hidden) disconnectLiveFrontPreview();
  else connectLiveFrontPreview();
});
window.addEventListener("pagehide", disconnectLiveFrontPreview);
refreshTickerPreview();
