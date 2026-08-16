const grid = document.querySelector("#scene-grid");
const stage = document.querySelector("#device-stage");
const frontPreview = document.querySelector("#front-preview");
const backPreview = document.querySelector("#back-preview");
const backCue = document.querySelector("#back-cue");
const previewScene = document.querySelector("#preview-scene");
const dynamicToggle = document.querySelector("#dynamic-toggle");
const dynamicDescription = document.querySelector("#dynamic-description");
const switchLabel = document.querySelector("#switch-label");
const deviceMode = document.querySelector("#device-mode");
const toast = document.querySelector("#toast");

let dashboard = null;
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
  frontPreview.replaceChildren();
  if (preset.front_style === "terminal") {
    frontPreview.append(document.createTextNode(`> ${preset.front.text}`));
    const cursor = document.createElement("span");
    cursor.className = "front-cursor";
    cursor.textContent = "_";
    frontPreview.append(cursor);
  } else {
    frontPreview.textContent = preset.front.text;
  }
  backPreview.textContent = preset.back.text;
  backCue.textContent = preset.rear_cue;
  previewScene.textContent = preset.label;
  stage.style.setProperty("--scene-color", preset.front.color);
}

function updateDynamic(enabled) {
  dynamicToggle.checked = enabled;
  stage.classList.toggle("is-dynamic", enabled);
  switchLabel.textContent = enabled ? "Enabled" : "Paused";
  dynamicDescription.textContent = enabled
    ? "Automatic scene changes are allowed. Manual scene choices still work."
    : "Automatic changes are paused. Manual scene choices still work.";
}

function render(state) {
  dashboard = state;
  deviceMode.textContent = state.device_mode === "fake" ? "Demo device" : "BUSY Bar";
  updateDynamic(state.dynamic_enabled);
  grid.replaceChildren();

  state.presets.forEach((preset) => {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "scene-card";
    card.classList.toggle("terminal-scene", preset.front_style === "terminal");
    card.classList.toggle("cyberpunk-scene", preset.front_style === "cyberpunk");
    card.classList.toggle("active", preset.id === state.active_preset);
    card.style.setProperty("--card-color", preset.front.color);
    card.setAttribute("aria-pressed", String(preset.id === state.active_preset));
    const frontText = preset.front_style === "terminal"
      ? `&gt; ${preset.front.text}<span class="front-cursor">_</span>`
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

dynamicToggle.addEventListener("change", async () => {
  const enabled = dynamicToggle.checked;
  updateDynamic(enabled);
  try {
    const response = await fetch("/api/dynamic", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled }),
    });
    if (!response.ok) throw new Error("Update failed");
    dashboard = await response.json();
    showToast(enabled ? "Dynamic scenes enabled" : "Dynamic scenes paused");
  } catch (_error) {
    updateDynamic(!enabled);
    showToast("Could not change automation setting");
  }
});

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
