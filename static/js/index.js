async function downloadMedia(channel, messageId, btn) {
  btn.disabled = true;
  try {
    const res = await fetch("/api/download-media", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ channel: channel, message_id: messageId }),
    });
    if (res.ok) {
      const data = await res.json();
      btn.outerHTML = `
      <div class="video-thumb" data-src="${data.filename}">
          <video muted class="media-thumb" preload="metadata">
              Ваш браузер не підтримує відео.
          </video>
          <button type="button"
              class="btn btn-danger btn-sm position-absolute top-0 end-0 m-1"
              onclick="deleteMedia(event, '${channel}', '${messageId}', '${data.filename}', this)">
              <span aria-hidden="true">&times;</span>
          </button>
      </div>`;
    } else {
      const err = await res.json();
      alert(
        `Помилка отримання файлу:\n(${channel}/${messageId})\n\n` +
          (err.detail || "Не вдалося завантажити медіа.")
      );
      btn.disabled = false;
    }
  } catch (e) {
    alert("Неочікувана помилка: " + e.message);
    btn.disabled = false;
  }
}

async function deleteMedia(event, channel, messageId, filename, btn) {
  event.stopPropagation();
  const res = await fetch("/api/delete-media", {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filename }),
  });
  if (res.ok) {
    const videoThumb = btn.closest(".video-thumb");
    if (videoThumb) {
      videoThumb.outerHTML = `<button type="button" onclick="event.stopPropagation(); downloadMedia('${channel}', '${messageId}', this)">Завантажити медіа</button>`;
    }
  } else {
    alert("Файл не знайдено.");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("mediaModal");
  const modalVideo = document.getElementById("modalVideo");
  const modalImage = document.getElementById("modalImage");

  document.body.addEventListener("click", (e) => {
    const videoThumb = e.target.closest(".video-thumb");
    // пропустити, якщо натиснута кнопка видалення
    if (e.target.closest("button.btn-danger")) return;
    if (videoThumb) {
      const mediaSrc = videoThumb.getAttribute("data-src");
      if (!mediaSrc) return;
      // Визначаємо тип медіа
      if (mediaSrc.match(/\.(mp4|webm)$/i)) {
        modalVideo.src = mediaSrc;
        modalVideo.style.display = "block";
        modalVideo.classList.remove("d-none");
        modalImage.style.display = "none";
        modalImage.classList.add("d-none");
      } else if (mediaSrc.match(/\.(jpg|jpeg|png|gif)$/i)) {
        modalImage.src = mediaSrc;
        modalImage.style.display = "block";
        modalImage.classList.remove("d-none");
        modalVideo.style.display = "none";
        modalVideo.classList.add("d-none");
      }
      // Відкрити модал вручну
      const modalInstance = bootstrap.Modal.getOrCreateInstance(modal);
      modalInstance.show();
    }
  });

  // Очищення src при закритті модального вікна (Bootstrap 5)
  modal.addEventListener("hidden.bs.modal", function () {
    modalVideo.pause();
    modalVideo.src = "";
    modalImage.src = "";
  });

  // Збільшення зображення при кліку
  document.querySelectorAll("img.media-thumb").forEach((img) => {
    img.addEventListener("click", () => {
      const overlay = document.createElement("div");
      overlay.style.position = "fixed";
      overlay.style.top = 0;
      overlay.style.left = 0;
      overlay.style.width = "100%";
      overlay.style.height = "100%";
      overlay.style.backgroundColor = "rgba(0,0,0,0.8)";
      overlay.style.display = "flex";
      overlay.style.alignItems = "center";
      overlay.style.justifyContent = "center";
      overlay.style.zIndex = 9999;
      const fullImg = document.createElement("img");
      fullImg.src = img.src;
      fullImg.style.maxWidth = "90%";
      fullImg.style.maxHeight = "90%";
      fullImg.style.boxShadow = "0 0 20px #fff";
      fullImg.style.borderRadius = "8px";
      fullImg.style.cursor = "zoom-out";
      overlay.appendChild(fullImg);
      document.body.appendChild(overlay);
      overlay.addEventListener("click", () => {
        document.body.removeChild(overlay);
      });
    });
  });
});

window.downloadMedia = downloadMedia;
window.deleteMedia = deleteMedia;
