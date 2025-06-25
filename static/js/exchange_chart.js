document.addEventListener("DOMContentLoaded", async () => {
  const chartContainer = document.getElementById("exchange-chart-container");
  if (!chartContainer) return;

  try {
    // Показуємо індикатор завантаження
    chartContainer.innerHTML = `
      <h6 class="mb-2 text-center">Графік курсів валют</h6>
      <div class="chart-wrapper d-flex justify-content-center align-items-center">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Завантаження...</span>
        </div>
      </div>
    `;

    // Отримуємо дані історії курсів валют
    console.log("Запит до API: /api/exchange-history");
    const response = await fetch("/api/exchange-history?limit=30", {
      method: "GET",
      headers: {
        Accept: "application/json",
        "Cache-Control": "no-cache",
      },
    });

    if (!response.ok) {
      const errorText = await response.text().catch(() => "Невідома помилка");
      throw new Error(
        `Помилка запиту: ${response.status} ${response.statusText}. ${errorText}`
      );
    }

    const data = await response.json();
    console.log("Отримано даних:", data.length);

    // Перевіряємо, чи є дані
    if (!data || data.length === 0) {
      chartContainer.innerHTML = `
        <h6 class="mb-2 text-center">Графік курсів валют</h6>
        <div class="chart-wrapper">
          <div class="alert alert-warning">Немає даних для відображення графіка</div>
        </div>
      `;
      return;
    }

    // Відновлюємо структуру контейнера
    chartContainer.innerHTML = `
      <h6 class="mb-2 text-center">Графік курсів валют</h6>
      <div class="chart-wrapper">
        <canvas id="exchange-chart"></canvas>
      </div>
    `;

    // Сортуємо дані за датою (від найстарішої до найновішої)
    data.sort((a, b) => new Date(a.date) - new Date(b.date));

    // Підготовка даних для графіка
    const labels = [];
    const usdValues = [];
    const eurValues = [];

    data.forEach((item) => {
      // Форматуємо дату для відображення
      const date = new Date(item.date);
      const formattedDate = `${date.getDate().toString().padStart(2, "0")}.${(
        date.getMonth() + 1
      )
        .toString()
        .padStart(2, "0")}`;

      labels.push(formattedDate);
      usdValues.push(item.usd);
      eurValues.push(item.eur);
    });

    // Створюємо графік
    const ctx = document.getElementById("exchange-chart").getContext("2d");

    new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "USD",
            data: usdValues,
            borderColor: "rgba(54, 162, 235, 1)",
            backgroundColor: "rgba(54, 162, 235, 0.2)",
            borderWidth: 2,
            tension: 0.1,
            pointRadius: 3,
          },
          {
            label: "EUR",
            data: eurValues,
            borderColor: "rgba(255, 99, 132, 1)",
            backgroundColor: "rgba(255, 99, 132, 0.2)",
            borderWidth: 2,
            tension: 0.1,
            pointRadius: 3,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        aspectRatio: 2,
        plugins: {
          legend: {
            position: "top",
            align: "start",
            labels: {
              boxWidth: 12,
              font: {
                size: 10,
              },
              padding: 6,
            },
          },
          tooltip: {
            mode: "index",
            intersect: false,
            callbacks: {
              label: function (context) {
                let label = context.dataset.label || "";
                if (label) {
                  label += ": ";
                }
                if (context.parsed.y !== null) {
                  label += new Intl.NumberFormat("uk-UA", {
                    style: "currency",
                    currency: "UAH",
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  }).format(context.parsed.y);
                }
                return label;
              },
            },
          },
        },
        scales: {
          y: {
            beginAtZero: false,
            ticks: {
              font: {
                size: 10,
              },
              callback: function (value) {
                return value.toFixed(2);
              },
            },
          },
          x: {
            ticks: {
              font: {
                size: 9,
              },
              maxTicksLimit: 10,
            },
          },
        },
        elements: {
          line: {
            borderWidth: 2,
          },
          point: {
            radius: 2,
            hitRadius: 6,
            hoverRadius: 4,
          },
        },
        layout: {
          padding: {
            left: 5,
            right: 5,
            top: 10,
            bottom: 5,
          },
        },
      },
    });
  } catch (error) {
    console.error("Помилка при завантаженні графіка курсів валют:", error);

    // Відображаємо детальну інформацію про помилку
    chartContainer.innerHTML = `
      <h6 class="mb-2 text-center">Графік курсів валют</h6>
      <div class="chart-wrapper">
        <div class="alert alert-danger">
          <p>Не вдалося завантажити графік курсів валют</p>
          <small class="d-block mt-1">${error.message}</small>
        </div>
      </div>
    `;

    // Додаємо кнопку для повторної спроби
    const retryButton = document.createElement("button");
    retryButton.className = "btn btn-sm btn-outline-primary mt-2";
    retryButton.textContent = "Спробувати знову";
    retryButton.onclick = () => window.location.reload();
    chartContainer.querySelector(".chart-wrapper").appendChild(retryButton);
  }
});
