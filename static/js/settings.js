document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("config-form");

  fetch("/admin/config")
    .then((res) => res.json())
    .then((data) => {
      form.days_to_keep.value = data.days_to_keep;
      form.MAX_FILE_SIZE_MB.value = data.MAX_FILE_SIZE_MB;
      form.news_update_in_minutes.value = data.news_update_in_minutes;
      form.channels.value = Object.entries(data.channels)
        .map(([ch, name]) => `${ch}: ${name}`)
        .join("\n");
    });

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const config = {
      days_to_keep: parseInt(form.days_to_keep.value),
      MAX_FILE_SIZE_MB: parseInt(form.MAX_FILE_SIZE_MB.value),
      news_update_in_minutes: parseInt(form.news_update_in_minutes.value),
      channels: {},
    };
    const lines = form.channels.value.split("\n");
    lines.forEach((line) => {
      const [key, ...rest] = line.split(":");
      if (key && rest.length) config.channels[key.trim()] = rest.join(":").trim();
    });
    fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    })
      .then((res) => {
        if (res.ok) alert("Конфігурацію збережено");
        else throw new Error("Помилка збереження");
      })
      .catch((err) => alert(err.message));
  });

  const restartBtn = document.getElementById("restart-btn");
  restartBtn.addEventListener("click", () => {
    if (confirm("Перезапустити програму?")) {
      fetch("/admin/restart", { method: "POST" })
        .then(() => alert("Перезапуск..."))
        .catch(() => alert("Помилка перезапуску"));
    }
  });
});
