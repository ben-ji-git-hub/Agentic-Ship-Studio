(() => {
  const root = document.documentElement;
  const spotlight = document.getElementById("fluidSpotlight");
  let raf = 0;
  let targetX = window.innerWidth * 0.5;
  let targetY = window.innerHeight * 0.3;
  let currentX = targetX;
  let currentY = targetY;

  function step() {
    currentX += (targetX - currentX) * 0.14;
    currentY += (targetY - currentY) * 0.14;
    root.style.setProperty("--spot-x", `${currentX}px`);
    root.style.setProperty("--spot-y", `${currentY}px`);
    if (spotlight) {
      spotlight.style.transform = `translate(${currentX - 220}px, ${currentY - 220}px)`;
    }
    raf = window.requestAnimationFrame(step);
  }

  function onPointerMove(event) {
    targetX = event.clientX;
    targetY = event.clientY;
  }

  function onScroll() {
    const depth = Math.min(window.scrollY / 500, 1);
    root.style.setProperty("--depth", depth.toFixed(3));
  }

  function setupReveal() {
    const nodes = Array.from(
      document.querySelectorAll(".panel, .hero, .subtitle, .showcase-card, .tutorial-step-card")
    );
    nodes.forEach((node) => node.classList.add("reveal"));

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("in-view");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.16 }
    );

    nodes.forEach((node) => observer.observe(node));
  }

  function setupFloatTilt() {
    const cards = Array.from(document.querySelectorAll("[data-float='card']"));
    cards.forEach((card) => {
      card.addEventListener("pointermove", (event) => {
        const rect = card.getBoundingClientRect();
        const dx = (event.clientX - rect.left) / rect.width - 0.5;
        const dy = (event.clientY - rect.top) / rect.height - 0.5;
        card.style.transform = `perspective(800px) rotateX(${(-dy * 4).toFixed(2)}deg) rotateY(${(
          dx * 4
        ).toFixed(2)}deg) translateY(-2px)`;
      });
      card.addEventListener("pointerleave", () => {
        card.style.transform = "";
      });
    });
  }

  function init() {
    setupReveal();
    setupFloatTilt();
    onScroll();
    step();
    window.addEventListener("pointermove", onPointerMove, { passive: true });
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }

  window.addEventListener("beforeunload", () => {
    if (raf) {
      window.cancelAnimationFrame(raf);
    }
  });
})();
