const grid = document.querySelector("#scene-grid");
const stage = document.querySelector("#device-stage");
const frontPreview = document.querySelector("#front-preview");
const backPreview = document.querySelector("#back-preview");
const backCue = document.querySelector("#back-cue");
const previewScene = document.querySelector("#preview-scene");
const deviceMode = document.querySelector("#device-mode");
const toast = document.querySelector("#toast");

let toastTimer = null;

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("visible");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("visible"), 2200);
}

function setPreview(preset) {
  stage.classList.toggle("terminal-scene", preset.front_style === "terminal");
  stage.classList.toggle("cyberpunk-scene", preset.front_style === "cyberpunk");
  stage.classList.toggle("low-battery-scene", preset.front_style === "low_battery");
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
  } else {
    frontPreview.textContent = preset.front.text;
  }
  backPreview.textContent = preset.back.text;
  backCue.textContent = preset.rear_cue;
  previewScene.textContent = preset.label;
  stage.style.setProperty("--scene-color", preset.front.color);
}

function render(state) {
  deviceMode.textContent = state.device_mode === "fake" ? "Demo device" : "BUSY Bar";
  grid.replaceChildren();

  state.presets.forEach((preset) => {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "scene-card";
    card.classList.toggle("terminal-scene", preset.front_style === "terminal");
    card.classList.toggle("cyberpunk-scene", preset.front_style === "cyberpunk");
    card.classList.toggle("low-battery-scene", preset.front_style === "low_battery");
    card.classList.toggle("active", preset.id === state.active_preset);
    card.style.setProperty("--card-color", preset.front.color);
    card.setAttribute("aria-pressed", String(preset.id === state.active_preset));
    const frontText = preset.front_style === "terminal"
      ? `&gt; ${preset.front.text}<span class="front-cursor">_</span>`
      : preset.front_style === "low_battery"
        ? `<span class="battery-glyph" aria-hidden="true"></span><span class="battery-copy"><span class="battery-label">${preset.front.text}</span><span class="battery-sub-label">BATTERY</span></span>`
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
  .catch(() => {
    deviceMode.textContent = "Offline";
    showToast("Dashboard could not load");
  });
