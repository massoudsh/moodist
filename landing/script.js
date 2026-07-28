// Purely decorative interaction for the static landing page:
// animates the mock volume bars in the hero preview so it feels "alive".
document.addEventListener("DOMContentLoaded", () => {
  const bars = document.querySelectorAll(".player-card .bar i");
  bars.forEach((bar) => {
    setInterval(() => {
      const value = 20 + Math.round(Math.random() * 60);
      bar.style.width = `${value}%`;
    }, 2200 + Math.random() * 1500);
  });
});
