const fileInput = document.querySelector("#file-input");
const dropzone = document.querySelector("#dropzone");
const form = document.querySelector("#upload-form");
const uploadButton = document.querySelector("#upload-button");
const uploadError = document.querySelector("#upload-error");
const selectedFile = document.querySelector("#selected-file");
const audioPreview = document.querySelector("#audio-preview");
const statusPanel = document.querySelector(".status-panel");
const statusPill = document.querySelector("#status-pill");
const statusHeading = document.querySelector("#status-heading");
const statusCopy = document.querySelector("#status-copy");
const progressTrack = document.querySelector("#progress-track");
const progressFill = document.querySelector("#progress-fill");
const resetButton = document.querySelector("#reset-upload");
const questionSection = document.querySelector("#question-section");
const questionForm = document.querySelector("#question-form");
const questionInput = document.querySelector("#question-input");
const starterQueryButtons = document.querySelectorAll(".starter-chip");
const askButton = document.querySelector("#ask-button");
const queryError = document.querySelector("#query-error");
const answerEmpty = document.querySelector("#answer-empty");
const answerView = document.querySelector("#answer-view");
const answerSummary = document.querySelector("#answer-summary");
const generationState = document.querySelector("#generation-state");
const answerTime = document.querySelector("#answer-time");
const matchList = document.querySelector("#match-list");
const bytesInMegabyte = 1024 * 1024;
let currentFile = null;
let previewUrl = null;
let pollTimer = null;
let activeAudioId = localStorage.getItem("resonance:lastAudioId");
let queryPending = false;

const messages = {
  queued: ["In the queue", "The worker will begin processing this recording shortly."],
  processing: ["Processing audio", "Transcription and indexing are running in the background."],
  ready: ["Recording is ready", "This audio has been transcribed and indexed."],
  failed: ["Processing failed", "The backend could not finish this recording."],
};

function formatBytes(bytes) {
  if (bytes < bytesInMegabyte) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / bytesInMegabyte).toFixed(1)} MB`;
}

function formatDuration(milliseconds) {
  if (!Number.isFinite(milliseconds) || milliseconds <= 0) return "--:--";
  const seconds = Math.floor(milliseconds / 1000);
  const minutesPart = Math.floor(seconds / 60);
  return `${String(minutesPart).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
}

function showError(message) {
  uploadError.textContent = message;
  uploadError.hidden = false;
}

function clearError() {
  uploadError.textContent = "";
  uploadError.hidden = true;
}

function setState(state, copy = "") {
  const defaults = messages[state];
  statusPill.dataset.status = state;
  statusPill.textContent = state === "idle" ? "STANDBY" : state.toUpperCase();
  statusHeading.textContent = defaults?.[0] ?? "Waiting for audio";
  statusCopy.textContent = copy || defaults?.[1] || "The upload and processing state will appear here.";
  statusPanel.dataset.status = state;
  statusPanel.dataset.active = String(state !== "idle");
  resetButton.hidden = !["ready", "failed"].includes(state);
  questionSection.hidden = state !== "ready";
  questionInput.disabled = state !== "ready" || queryPending;
  starterQueryButtons.forEach((button) => {
    button.disabled = state !== "ready" || queryPending;
  });
  askButton.disabled = state !== "ready" || queryPending;
}

function clearAnswer() {
  answerSummary.textContent = "";
  generationState.hidden = true;
  answerTime.textContent = "";
  matchList.replaceChildren();
  answerView.hidden = true;
  answerView.setAttribute("aria-busy", "false");
  answerEmpty.hidden = false;
  queryError.textContent = "";
  queryError.hidden = true;
}

function formatTimestamp(milliseconds) {
  const totalSeconds = Math.floor(milliseconds / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  const prefix = hours > 0 ? `${String(hours).padStart(2, "0")}:` : "";
  return `${prefix}${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

function renderAnswer(result) {
  generationState.hidden = true;
  answerSummary.textContent = result.summary;
  answerTime.textContent = `PRIMARY MATCH  ${formatTimestamp(result.primary_start_ms)} - ${formatTimestamp(result.primary_end_ms)}`;
  matchList.replaceChildren();

  for (const match of result.matches) {
    const item = document.createElement("li");
    const time = document.createElement("span");
    const text = document.createElement("p");
    time.className = "match-time";
    time.textContent = `${formatTimestamp(match.start_ms)} - ${formatTimestamp(match.end_ms)}`;
    text.textContent = match.text;
    item.append(time, text);
    matchList.append(item);
  }

  document.querySelector("#match-count").textContent = `${result.matches.length} MATCHES`;
  answerEmpty.hidden = true;
  answerView.hidden = false;
  answerView.setAttribute("aria-busy", "false");
}

function makeWaveform() {
  const wave = document.querySelector("#waveform");
  const heights = [18, 34, 61, 42, 76, 29, 51, 82, 38, 64, 24, 46, 70, 32, 88, 41, 57, 27, 73, 36, 54, 82, 30, 63, 43, 77, 25, 49, 68, 34, 84, 45, 59, 28, 72, 40, 88, 32, 55, 75, 22, 48, 65, 35, 81, 43, 60, 26, 70, 39, 86, 31, 53, 74, 24, 46, 67, 37, 82, 42, 58, 28, 71, 34, 88, 45];
  for (const height of heights) {
    const bar = document.createElement("span");
    bar.style.setProperty("--bar-height", `${height}%`);
    wave.append(bar);
  }
}

function chooseFile(file) {
  if (!file) return;
  currentFile = file;
  clearError();
  clearAnswer();
  activeAudioId = null;
  localStorage.removeItem("resonance:lastAudioId");
  window.clearTimeout(pollTimer);
  selectedFile.hidden = false;
  document.querySelector("#file-name").textContent = file.name;
  document.querySelector("#file-size").textContent = formatBytes(file.size);
  document.querySelector("#asset-name").textContent = file.name;
  document.querySelector("#asset-id").textContent = "Assigned after upload";
  document.querySelector("#asset-duration").textContent = "Reading file";
  uploadButton.disabled = false;
  uploadButton.firstElementChild.textContent = "Upload recording";
  progressTrack.hidden = true;
  progressFill.style.width = "0%";
  setState("idle");

  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = URL.createObjectURL(file);
  audioPreview.src = previewUrl;
  audioPreview.hidden = false;
  audioPreview.onloadedmetadata = () => {
    document.querySelector("#asset-duration").textContent = formatDuration(audioPreview.duration * 1000);
  };
  audioPreview.onerror = () => {
    document.querySelector("#asset-duration").textContent = "Unavailable";
  };
}

function clearSelectedFile() {
  currentFile = null;
  fileInput.value = "";
  selectedFile.hidden = true;
  audioPreview.pause();
  audioPreview.removeAttribute("src");
  audioPreview.load();
  audioPreview.hidden = true;
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = null;
  uploadButton.disabled = true;
  document.querySelector("#asset-name").textContent = "No file selected";
  document.querySelector("#asset-duration").textContent = "--:--";
}

function uploadAudio(file) {
  const request = new XMLHttpRequest();
  const formData = new FormData();
  formData.append("file", file);
  uploadButton.disabled = true;
  uploadButton.firstElementChild.textContent = "Uploading 0%";
  progressTrack.hidden = false;
  setState("uploading", "Sending the recording to the API.");
  clearError();

  request.open("POST", "/api/v1/audio");
  request.upload.addEventListener("progress", (event) => {
    if (!event.lengthComputable) return;
    const percent = Math.round((event.loaded / event.total) * 100);
    progressFill.style.width = `${percent}%`;
    uploadButton.firstElementChild.textContent = `Uploading ${percent}%`;
  });

  request.addEventListener("load", () => {
    let result;
    try {
      result = JSON.parse(request.responseText);
    } catch {
      uploadButton.disabled = false;
      showError("The server returned an unreadable response.");
      setState("failed", "The upload response could not be read.");
      return;
    }

    if (request.status < 200 || request.status >= 300) {
      uploadButton.disabled = false;
      const detail = result.detail;
      const message = typeof detail === "object" ? detail.message : detail;
      showError(message || `Upload failed with status ${request.status}.`);
      setState("failed", "The backend rejected this upload.");
      return;
    }

    document.querySelector("#asset-id").textContent = result.id;
    document.querySelector("#asset-name").textContent = result.original_filename;
    document.querySelector("#asset-duration").textContent = formatDuration(result.duration_ms);
    activeAudioId = result.id;
    localStorage.setItem("resonance:lastAudioId", result.id);
    progressTrack.hidden = true;
    setState(result.status, "Upload accepted. Waiting for the worker.");
    pollAudio(result.id);
  });

  request.addEventListener("error", () => {
    uploadButton.disabled = false;
    showError("Could not reach the API. Check that the backend is running.");
    setState("failed", "The upload request did not reach the backend.");
  });

  request.send(formData);
}

async function pollAudio(audioId) {
  try {
    const response = await fetch(`/api/v1/audio/${encodeURIComponent(audioId)}`);
    const asset = await response.json();
    if (!response.ok) throw new Error(asset.detail?.message || asset.detail || "Could not read audio status.");

    document.querySelector("#asset-id").textContent = asset.id;
    document.querySelector("#asset-name").textContent = asset.original_filename;
    document.querySelector("#asset-duration").textContent = formatDuration(asset.duration_ms);
    setState(asset.status, asset.failure_message || "");

    if (["queued", "processing"].includes(asset.status)) {
      pollTimer = window.setTimeout(() => pollAudio(audioId), 2500);
    } else if (asset.status === "failed") {
      showError(asset.failure_message || "Audio processing failed.");
    }
  } catch (error) {
    setState("processing", "Status check failed temporarily. Retrying shortly.");
    pollTimer = window.setTimeout(() => pollAudio(audioId), 5000);
  }
}

document.querySelector("#choose-file").addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", () => chooseFile(fileInput.files[0]));
document.querySelector("#remove-file").addEventListener("click", clearSelectedFile);

dropzone.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropzone.classList.add("is-dragging");
});
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("is-dragging"));
dropzone.addEventListener("drop", (event) => {
  event.preventDefault();
  dropzone.classList.remove("is-dragging");
  chooseFile(event.dataTransfer.files[0]);
});

form.addEventListener("submit", (event) => {
  event.preventDefault();
  if (currentFile) uploadAudio(currentFile);
});

questionForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!activeAudioId || !questionInput.value.trim() || queryPending) return;

  queryPending = true;
  queryError.textContent = "";
  queryError.hidden = true;
  answerEmpty.hidden = true;
  answerView.hidden = false;
  answerView.setAttribute("aria-busy", "true");
  answerSummary.textContent = "Searching the transcript and preparing an answer...";
  generationState.hidden = false;
  answerTime.textContent = "";
  matchList.replaceChildren();
  askButton.firstElementChild.textContent = "Thinking";
  setState("ready");

  try {
    const response = await fetch(`/api/v1/audio/${encodeURIComponent(activeAudioId)}/queries`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question: questionInput.value.trim(),
        top_k: Number(document.querySelector("#top-k-select").value),
      }),
    });
    const result = await response.json();
    if (!response.ok) {
      const detail = result.detail;
      throw new Error(typeof detail === "object" ? detail.message || "Could not answer this question." : detail || "Could not answer this question.");
    }
    renderAnswer(result);
  } catch (error) {
    generationState.hidden = true;
    answerView.hidden = true;
    answerEmpty.hidden = false;
    queryError.textContent = error.message || "Could not reach the query service. Try again.";
    queryError.hidden = false;
  } finally {
    queryPending = false;
    askButton.firstElementChild.textContent = "Ask question";
    setState("ready");
  }
});

starterQueryButtons.forEach((button) => {
  button.addEventListener("click", () => {
    questionInput.value = button.dataset.question;
    queryError.textContent = "";
    queryError.hidden = true;
    questionInput.focus();
  });
});

resetButton.addEventListener("click", () => {
  window.clearTimeout(pollTimer);
  localStorage.removeItem("resonance:lastAudioId");
  activeAudioId = null;
  clearAnswer();
  clearSelectedFile();
  clearError();
  progressTrack.hidden = true;
  document.querySelector("#asset-id").textContent = "Not assigned";
  setState("idle");
});

makeWaveform();
const previousAudioId = activeAudioId;
if (previousAudioId) {
  document.querySelector("#asset-id").textContent = previousAudioId;
  setState("processing", "Restoring the latest recording status.");
  pollAudio(previousAudioId);
}