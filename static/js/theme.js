function setTheme(theme) {
  if (theme === "dark") {
    document.documentElement.setAttribute("data-bs-theme", "dark");
    localStorage.setItem("theme", "dark");
    const toggle = document.getElementById("theme-toggle");
    if (toggle) toggle.textContent = "☀️";
  } else {
    document.documentElement.setAttribute("data-bs-theme", "light");
    localStorage.setItem("theme", "light");
    const toggle = document.getElementById("theme-toggle");
    if (toggle) toggle.textContent = "🌙";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const savedTheme = localStorage.getItem("theme") || "light";
  setTheme(savedTheme);

  const themeToggle = document.getElementById("theme-toggle");
  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-bs-theme");
      const newTheme = current === "light" ? "dark" : "light";
      setTheme(newTheme);
    });
  }
});

window.setTheme = setTheme;
