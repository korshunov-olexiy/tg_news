document.addEventListener("DOMContentLoaded", () => {
  const rawList = JSON.parse(
    document.getElementById("channel-map-json").textContent
  );

  // rawList — це масив пар [channel, title]
  const channelList = rawList.map((pair) => pair[0]);

  const currentChannel =
    new URLSearchParams(window.location.search).get("channel") ||
    channelList[0];

  let currentIndex = channelList.indexOf(currentChannel);
  const searchParams = new URLSearchParams(window.location.search);

  const goTo = (index) => {
    index = (index + channelList.length) % channelList.length; // циклічний індекс
    const nextChannel = channelList[index];
    searchParams.set("channel", nextChannel);

    // Анімація
    const container = document.querySelector(".news-feed");
    container.classList.add("fade-out");
    setTimeout(() => {
      window.location.href = `/?${searchParams.toString()}`;
    }, 200);
  };

  // Кнопки ⟨ ⟩
  const prevBtn = document.getElementById("prev-channel-btn");
  const nextBtn = document.getElementById("next-channel-btn");

  if (prevBtn && nextBtn) {
    prevBtn.addEventListener("click", () => goTo(currentIndex - 1));
    nextBtn.addEventListener("click", () => goTo(currentIndex + 1));
  }

  // визначаємо div, в якому буде спрацьовувати swipe
  const swipeZone = document.querySelector(".swipeZone");
  let touchStartX = null;

  if (swipeZone) {
    swipeZone.addEventListener("touchstart", (e) => {
      if (e.touches.length === 1) {
        const x = e.touches[0].clientX;
        if (x > 30 && x < window.innerWidth - 30) {
          touchStartX = x;
        }
      }
    });

    swipeZone.addEventListener("touchend", (e) => {
      if (touchStartX === null) return;
      const delta = touchStartX - e.changedTouches[0].clientX;
      if (Math.abs(delta) > 50) {
        if (delta > 0) goTo(currentIndex + 1); // вліво
        else goTo(currentIndex - 1); // вправо
      }
      touchStartX = null;
    });
  }
});
