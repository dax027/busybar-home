const deviceLog = document.querySelector("#device-log");
const logEmpty = document.querySelector("#log-empty");
const logMetadata = document.querySelector("#log-metadata");
const captureLogsButton = document.querySelector("#capture-logs");

function formatBytes(size) {
  if (size < 1024) return `${size} B`;
  return `${(size / 1024).toFixed(1)} KiB`;
}

async function captureLogs() {
  captureLogsButton.disabled = true;
  captureLogsButton.textContent = "Capturing…";
  logMetadata.textContent = "Requesting a fresh diagnostic dump from the BUSY Bar…";
  try {
    const response = await fetch("/api/device/logs/capture", { method: "POST" });
    if (!response.ok) throw new Error("Device log capture failed");
    const payload = await response.json();
    deviceLog.textContent = payload.content || "The device returned an empty log.";
    deviceLog.hidden = false;
    logEmpty.hidden = true;
    const truncation = payload.truncated ? " · showing the newest 512 KiB" : "";
    logMetadata.textContent = `${payload.path} · ${formatBytes(payload.size_bytes)}${truncation}`;
  } catch (error) {
    deviceLog.hidden = true;
    logEmpty.hidden = false;
    logEmpty.textContent = error.message || "Could not capture the device log.";
    logMetadata.textContent = "Capture failed";
  } finally {
    captureLogsButton.disabled = false;
    captureLogsButton.textContent = "Capture device log";
  }
}

captureLogsButton.addEventListener("click", captureLogs);
