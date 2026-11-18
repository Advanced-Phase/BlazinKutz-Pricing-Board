function renderService(service, index) {
  const number = String(index + 1).padStart(2, "0");
  const item = document.createElement("article");
  item.className = `menu-item${service.featured ? " featured" : ""}`;
  item.innerHTML = `
    <span class="service-number">${number}</span>
    <div class="service-info">
      <div class="service-name"></div>
      <div class="service-detail"></div>
    </div>
    <strong class="service-price"></strong>`;
  item.querySelector(".service-name").textContent = service.name;
  item.querySelector(".service-detail").textContent = service.detail;
  item.querySelector(".service-price").textContent = `${service.prefix || ""}$${service.price}${service.suffix || ""}`;
  return item;
}

async function loadMenu() {
  const columns = document.querySelector("#menu-columns");
  try {
    const response = await fetch("menu.json", { cache: "no-cache" });
    if (!response.ok) throw new Error(`Menu request failed (${response.status})`);
    const { copy, services, earlyBird } = await response.json();
    const midpoint = Math.ceil(services.length / 2);
    const menuColumns = [services.slice(0, midpoint), services.slice(midpoint)].map((group, columnIndex) => {
      const column = document.createElement("div");
      column.className = "menu-column";
      column.append(...group.map((service, index) => renderService(service, columnIndex * midpoint + index)));
      return column;
    });
    const special = renderService(earlyBird, services.length);
    special.classList.add("early-bird");
    document.querySelectorAll("[data-copy]").forEach(element => {
      const value = copy[element.dataset.copy];
      if (typeof value === "string") element.textContent = value;
    });
    columns.replaceChildren(...menuColumns, special);
  } catch (error) {
    columns.textContent = "Pricing is temporarily unavailable. Please ask your barber for current prices.";
    console.error(error);
  }
}

loadMenu();

// Scale the whole composition uniformly; preserve desktop sizing above 1024px.
const mobileBoard = matchMedia("(max-width: 1024px)");
function fitMobileBoard() {
  const viewport = window.visualViewport;
  const width = viewport ? viewport.width : innerWidth;
  const height = viewport ? viewport.height : innerHeight;
  const scale = Math.min(width / 1920, height / 1080);
  const style = document.documentElement.style;
  style.setProperty("--board-scale", scale);
  style.setProperty("--board-left", `${(width - 1920 * scale) / 2}px`);
  style.setProperty("--board-top", `${(height - 1080 * scale) / 2}px`);
}
fitMobileBoard();
let fitFrame = 0;
let rotationTimer;
let viewportChanging = false;
function scheduleMobileFit() {
  if (mobileBoard.matches) {
    viewportChanging = true;
    document.documentElement.classList.add("viewport-changing");
    cancelAnimationFrame(fireFrame);
    fireFrame = 0;
    clearTimeout(rotationTimer);
    rotationTimer = setTimeout(() => {
      fitMobileBoard();
      viewportChanging = false;
      document.documentElement.classList.remove("viewport-changing");
      updateFire();
    }, 300);
  }
  if (fitFrame) return;
  fitFrame = requestAnimationFrame(() => {
    fitFrame = 0;
    fitMobileBoard();
  });
}
addEventListener("resize", scheduleMobileFit);
mobileBoard.addEventListener("change", scheduleMobileFit);
window.visualViewport?.addEventListener("resize", scheduleMobileFit);

// Procedural fire: low-resolution rendering keeps the animation smooth on a Pi.
const flameCanvas = document.querySelector("#flame-canvas");
let flameContext = null;
let fireFrame = 0;
const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
const particles = [];
let flameWidth = 0;
let flameHeight = 0;
let lastFrame = 0;

function resizeFlames() {
  // Keep a stable, modest backing store on mobile through every rotation.
  // CSS scales it with the board; particle positions never need rebuilding.
  const rect = flameCanvas.getBoundingClientRect();
  const scale = Math.min(devicePixelRatio || 1, 1.25);
  const width = mobileBoard.matches ? 960 : Math.max(1, Math.round(rect.width * scale));
  const height = mobileBoard.matches ? 103 : Math.max(1, Math.round(rect.height * scale));
  if (width === flameWidth && height === flameHeight) return false;
  flameWidth = width;
  flameHeight = height;
  flameCanvas.width = flameWidth;
  flameCanvas.height = flameHeight;
  return true;
}

function createFlame(seedAtBottom = true) {
  const size = flameHeight * (.06 + Math.random() * .105);
  return {
    x: Math.random() * flameWidth,
    y: seedAtBottom ? flameHeight + size * .35 : Math.random() * flameHeight,
    originX: Math.random() * flameWidth,
    radius: size,
    life: 0,
    maxLife: .62 + Math.random() * .75,
    speed: flameHeight * (.48 + Math.random() * .52),
    sway: .7 + Math.random() * 1.6,
    phase: Math.random() * Math.PI * 2,
    tone: Math.random()
  };
}

function resetFire() {
  particles.length = 0;
  const count = Math.min(260, Math.max(110, Math.round((mobileBoard.matches ? 2400 : flameWidth) / 7)));
  for (let i = 0; i < count; i += 1) particles.push(createFlame(false));
}

function paintFlame(particle, now) {
  const progress = particle.life / particle.maxLife;
  const fade = Math.sin(Math.min(1, progress) * Math.PI);
  const taper = 1 - progress * .72;
  const turbulence = Math.sin(now * .004 * particle.sway + particle.phase) * particle.radius * .72;
  const x = particle.x + turbulence + Math.sin(progress * 11 + particle.phase) * particle.radius * .2;
  const radius = Math.max(1, particle.radius * taper);

  const gradient = flameContext.createRadialGradient(x, particle.y, 0, x, particle.y, radius);
  if (particle.tone > .86 && progress < .48) {
    gradient.addColorStop(0, `rgba(255,251,222,${.94 * fade})`);
    gradient.addColorStop(.3, `rgba(255,226,137,${.88 * fade})`);
    gradient.addColorStop(1, "rgba(211,164,47,0)");
  } else if (progress < .68) {
    gradient.addColorStop(0, `rgba(244,207,95,${.74 * fade})`);
    gradient.addColorStop(.46, `rgba(215,170,52,${.67 * fade})`);
    gradient.addColorStop(1, "rgba(139,103,25,0)");
  } else {
    gradient.addColorStop(0, `rgba(222,181,66,${.48 * fade})`);
    gradient.addColorStop(.55, `rgba(148,111,29,${.36 * fade})`);
    gradient.addColorStop(1, "rgba(55,40,8,0)");
  }

  flameContext.fillStyle = gradient;
  flameContext.beginPath();
  flameContext.ellipse(x, particle.y, radius * .72, radius * 1.48, 0, 0, Math.PI * 2);
  flameContext.fill();
}

function drawFire(timestamp = 0) {
  if (document.hidden || viewportChanging || !flameContext) return;
  const delta = lastFrame ? Math.min((timestamp - lastFrame) / 1000, .04) : .016;
  lastFrame = timestamp;
  flameContext.clearRect(0, 0, flameWidth, flameHeight);

  // A dim, uneven coal-bed glow anchors the moving flames to the bottom edge.
  const bed = flameContext.createLinearGradient(0, flameHeight * .55, 0, flameHeight);
  bed.addColorStop(0, "rgba(141,105,27,0)");
  bed.addColorStop(.62, "rgba(192,146,36,.2)");
  bed.addColorStop(1, "rgba(237,197,78,.58)");
  flameContext.fillStyle = bed;
  flameContext.fillRect(0, flameHeight * .45, flameWidth, flameHeight * .55);

  flameContext.globalCompositeOperation = "lighter";
  particles.forEach((particle, index) => {
    particle.life += delta;
    particle.y -= particle.speed * delta * (.72 + particle.life / particle.maxLife * .45);
    particle.x += Math.sin(timestamp * .0017 + particle.phase) * delta * 7;
    paintFlame(particle, timestamp);
    if (particle.life >= particle.maxLife || particle.y < -particle.radius) particles[index] = createFlame();
  });
  if (mobileBoard.matches) {
    // Bake the existing top fade into canvas pixels rather than a CSS mask layer.
    flameContext.globalCompositeOperation = "destination-in";
    const fade = flameContext.createLinearGradient(0, 0, 0, flameHeight);
    fade.addColorStop(0, "rgba(0,0,0,0)");
    fade.addColorStop(.28, "rgba(0,0,0,1)");
    fade.addColorStop(1, "rgba(0,0,0,1)");
    flameContext.fillStyle = fade;
    flameContext.fillRect(0, 0, flameWidth, flameHeight);
  }
  flameContext.globalCompositeOperation = "source-over";

  if (!reducedMotion) fireFrame = requestAnimationFrame(drawFire);
}

// One animation loop, paused while hidden. Reallocate only when size changes.
function updateFire() {
  if (document.hidden || viewportChanging) {
    cancelAnimationFrame(fireFrame);
    fireFrame = 0;
    return;
  }
  flameContext ||= flameCanvas.getContext("2d", { alpha: true });
  if (!flameContext) return;
  const resized = resizeFlames();
  if (resized || !particles.length) resetFire();
  if (!fireFrame || reducedMotion) {
    lastFrame = 0;
    drawFire();
  }
}

let fireResizeTimer;
addEventListener("resize", () => {
  clearTimeout(fireResizeTimer);
  fireResizeTimer = setTimeout(updateFire, 150);
});
mobileBoard.addEventListener("change", updateFire);
document.addEventListener("visibilitychange", updateFire);
updateFire();
