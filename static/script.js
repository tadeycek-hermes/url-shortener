const API = "";

const urlInput = document.getElementById("urlInput");
const customInput = document.getElementById("customCodeInput");
const shortenBtn = document.getElementById("shortenBtn");
const resultCard = document.getElementById("result");
const shortUrlA = document.getElementById("shortUrl");
const copyBtn = document.getElementById("copyBtn");
const metaText = document.getElementById("metaText");
const errorCard = document.getElementById("error");
const urlList = document.getElementById("urlList");

async function shorten() {
  const url = urlInput.value.trim();
  const custom = customInput.value.trim() || undefined;

  if (!url) {
    showError("Please enter a URL");
    return;
  }

  shortenBtn.disabled = true;
  shortenBtn.textContent = "Shortening...";
  hideError();
  resultCard.classList.add("hidden");

  try {
    const res = await fetch(`${API}/api/shorten`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, custom_code: custom }),
    });

    const data = await res.json();
    if (!res.ok) {
      showError(data.detail || "Something went wrong");
      return;
    }

    shortUrlA.href = data.short_url;
    shortUrlA.textContent = data.short_url;
    metaText.textContent = `Redirects to: ${data.original_url}`;
    resultCard.classList.remove("hidden");
    urlInput.value = "";
    customInput.value = "";
    loadUrls();
  } catch (e) {
    showError("Network error. Is the backend running?");
  } finally {
    shortenBtn.disabled = false;
    shortenBtn.textContent = "Shorten";
  }
}

function showError(msg) {
  errorCard.textContent = msg;
  errorCard.classList.remove("hidden");
}

function hideError() {
  errorCard.classList.add("hidden");
}

copyBtn.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(shortUrlA.href);
    copyBtn.textContent = "Copied!";
    setTimeout(() => (copyBtn.textContent = "Copy"), 1500);
  } catch {
    copyBtn.textContent = "Failed";
  }
});

shortenBtn.addEventListener("click", shorten);
urlInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") shorten();
});

async function loadUrls() {
  try {
    const res = await fetch(`${API}/api/urls`);
    const data = await res.json();
    urlList.innerHTML = "";

    if (data.length === 0) {
      urlList.innerHTML = `<div class="empty">No URLs yet. Create one above!</div>`;
      return;
    }

    for (const item of data) {
      const div = document.createElement("div");
      div.className = "url-item";
      div.innerHTML = `
        <div class="top">
          <a class="short" href="/${item.short_code}" target="_blank">${location.origin}/${item.short_code}</a>
          <span class="stats">${item.clicks} clicks</span>
        </div>
        <div class="original">${item.original_url}</div>
        <div class="stats">${item.created_at}</div>
      `;
      urlList.appendChild(div);
    }
  } catch (e) {
    urlList.innerHTML = `<div class="empty">Could not load recent URLs.</div>`;
  }
}

loadUrls();
