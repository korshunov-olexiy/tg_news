document.addEventListener("DOMContentLoaded", () => {
  const currencyDiv = document.getElementById("currency-rates");
  fetch("/api/rates")
    .then(res => res.json())
    .then(data => {
      if (data.usd && data.eur) {
        currencyDiv.innerHTML = `
          <span>💵 USD: <b>${data.usd.buy.toFixed(2)}</b> / <b>${data.usd.sell.toFixed(2)}</b></span><br>
          <span>💶 EUR: <b>${data.eur.buy.toFixed(2)}</b> / <b>${data.eur.sell.toFixed(2)}</b></span>
        `;
      } else {
        currencyDiv.textContent = "Курси недоступні";
      }
    })
    .catch(() => {
      currencyDiv.textContent = "Помилка курсів";
    });
});
