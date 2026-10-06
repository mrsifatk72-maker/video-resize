/* Dr. Tanim Ahmed — portfolio interactions (no dependencies) */
(() => {
  "use strict";

  const root = document.documentElement;
  const $ = (sel, ctx = document) => ctx.querySelector(sel);
  const $$ = (sel, ctx = document) => Array.from(ctx.querySelectorAll(sel));
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)");
  const desktopXp = window.matchMedia("(min-width: 1024px)");

  /* ---------- Intro ---------- */
  const ready = () => requestAnimationFrame(() => root.classList.add("is-ready"));
  if (document.fonts && document.fonts.ready) {
    Promise.race([document.fonts.ready, new Promise((r) => setTimeout(r, 700))]).then(ready);
  } else {
    ready();
  }

  /* ---------- Count-up ---------- */
  const countUp = (el) => {
    if (el.dataset.counted) return;
    el.dataset.counted = "1";
    const target = parseInt(el.dataset.count, 10);
    if (reduceMotion.matches || !target) { el.textContent = target; return; }
    const duration = target > 10 ? 1800 : 1100;
    const start = performance.now();
    const tick = (now) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(2, -10 * t);
      el.textContent = Math.round(target * (t === 1 ? 1 : eased));
      if (t < 1) requestAnimationFrame(tick);
    };
    el.textContent = "0";
    requestAnimationFrame(tick);
  };

  /* ---------- Reveal on scroll ---------- */
  const revealEls = $$("[data-reveal]");
  const countEls = $$("[data-count]");
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-in");
        $$("[data-count]", entry.target).forEach(countUp);
        io.unobserve(entry.target);
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.12 });
    revealEls.forEach((el) => io.observe(el));

    const cio = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        countUp(entry.target);
        cio.unobserve(entry.target);
      });
    }, { threshold: 0.6 });
    countEls.forEach((el) => cio.observe(el));
  } else {
    revealEls.forEach((el) => el.classList.add("is-in"));
  }

  /* ---------- Navigation ---------- */
  const nav = $("[data-nav]");
  const menu = $("[data-menu]");
  const toggle = $("[data-menu-toggle]");
  const links = $$("[data-link]");
  let menuOpen = false;

  const sectionIO = "IntersectionObserver" in window && new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      const id = entry.target.id;
      links.forEach((a) => {
        const on = a.dataset.link === id;
        a.classList.toggle("is-active", on);
        if (on) a.setAttribute("aria-current", "true"); else a.removeAttribute("aria-current");
      });
    });
  }, { rootMargin: "-45% 0px -50% 0px" });
  if (sectionIO) $$("[data-section]").forEach((s) => sectionIO.observe(s));

  const setMenu = (open) => {
    menuOpen = open;
    toggle.setAttribute("aria-expanded", String(open));
    toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    document.body.classList.toggle("menu-open", open);
    if (open) {
      nav.classList.remove("is-hidden");
      menu.hidden = false;
      requestAnimationFrame(() => requestAnimationFrame(() => menu.classList.add("is-open")));
      setTimeout(() => { const first = $("a", menu); if (first) first.focus({ preventScroll: true }); }, 350);
    } else {
      menu.classList.remove("is-open");
      const done = () => { if (!menuOpen) menu.hidden = true; };
      reduceMotion.matches ? done() : setTimeout(done, 650);
    }
  };
  toggle.addEventListener("click", () => setMenu(!menuOpen));
  $$("a", menu).forEach((a) => a.addEventListener("click", () => setMenu(false)));
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && menuOpen) { setMenu(false); toggle.focus(); }
    if (e.key === "Tab" && menuOpen) {
      const focusables = [toggle, ...$$("a", menu)];
      const first = focusables[0], last = focusables[focusables.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });
  window.matchMedia("(min-width: 1181px)").addEventListener("change", (e) => { if (e.matches && menuOpen) setMenu(false); });

  /* ---------- Scroll-linked effects ---------- */
  const timeline = $("[data-timeline]");
  const timelineFill = $("[data-timeline-fill]");
  const philosophy = $("[data-philosophy]");
  const philosophyFill = $("[data-philosophy-fill]");
  const parallaxEls = $$("[data-parallax]");
  let lastY = window.scrollY;
  let ticking = false;

  const progress = (el, startRatio, endRatio) => {
    const r = el.getBoundingClientRect();
    const vh = window.innerHeight;
    const start = vh * startRatio;
    const total = r.height + vh * (startRatio - endRatio);
    return Math.min(1, Math.max(0, (start - r.top) / total));
  };

  const onScroll = () => {
    ticking = false;
    const y = window.scrollY;

    nav.classList.toggle("is-scrolled", y > 24);
    if (!menuOpen) {
      const goingDown = y > lastY + 4;
      const goingUp = y < lastY - 4;
      if (goingDown && y > window.innerHeight * 0.9) nav.classList.add("is-hidden");
      else if (goingUp || y < 200) nav.classList.remove("is-hidden");
    }
    lastY = y;

    if (timeline && timelineFill) timelineFill.style.setProperty("--p", progress(timeline, 0.75, 0.55).toFixed(4));
    if (philosophy && philosophyFill) philosophyFill.style.setProperty("--p", progress(philosophy, 0.85, 0.6).toFixed(4));

    if (!reduceMotion.matches) {
      const vh = window.innerHeight;
      parallaxEls.forEach((img) => {
        const r = img.parentElement.getBoundingClientRect();
        if (r.bottom < -100 || r.top > vh + 100) return;
        const offset = (r.top + r.height / 2 - vh / 2) * parseFloat(img.dataset.parallax || 0.05);
        img.style.transform = `translate3d(0, ${(-offset).toFixed(1)}px, 0) scale(1.08)`;
      });
    }
  };
  const requestTick = () => { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } };
  window.addEventListener("scroll", requestTick, { passive: true });
  window.addEventListener("resize", requestTick, { passive: true });
  onScroll();

  /* ---------- Expertise (tabs on desktop, accordion on mobile) ---------- */
  const xp = $("[data-xp]");
  if (xp) {
    const items = $$(".xp__item", xp);
    const setActive = (item, { allowClose = false } = {}) => {
      const wasActive = item.classList.contains("is-active");
      items.forEach((it) => {
        const on = it === item ? !(allowClose && wasActive) : false;
        it.classList.toggle("is-active", on);
        $(".xp__head", it).setAttribute("aria-expanded", String(on));
      });
    };
    let hoverTimer;
    items.forEach((item) => {
      const head = $(".xp__head", item);
      head.addEventListener("click", () => setActive(item, { allowClose: !desktopXp.matches }));
      head.addEventListener("mouseenter", () => {
        if (!desktopXp.matches || !finePointer.matches) return;
        clearTimeout(hoverTimer);
        hoverTimer = setTimeout(() => setActive(item), 90);
      });
      head.addEventListener("mouseleave", () => clearTimeout(hoverTimer));
    });
    // Desktop always shows one panel
    desktopXp.addEventListener("change", (e) => {
      if (e.matches && !items.some((it) => it.classList.contains("is-active"))) setActive(items[0]);
    });
  }

  /* ---------- Gallery: filters + lightbox ---------- */
  const gallery = $("[data-gallery]");
  const chips = $$("[data-filter]");
  const lb = $("[data-lightbox]");
  if (gallery && lb) {
    const tiles = $$(".g", gallery);
    chips.forEach((chip) => chip.addEventListener("click", () => {
      const f = chip.dataset.filter;
      chips.forEach((c) => {
        const on = c === chip;
        c.classList.toggle("is-active", on);
        c.setAttribute("aria-pressed", String(on));
      });
      tiles.forEach((t) => {
        const show = f === "all" || t.dataset.cat === f;
        t.classList.toggle("is-hidden", !show);
        if (show) { t.style.animation = "none"; void t.offsetWidth; t.style.animation = ""; }
      });
    }));

    const lbImg = $("[data-lb-img]", lb);
    const lbCap = $("[data-lb-cap]", lb);
    const lbCount = $("[data-lb-count]", lb);
    const lbClose = $("[data-lb-close]", lb);
    const lbPrev = $("[data-lb-prev]", lb);
    const lbNext = $("[data-lb-next]", lb);
    let current = 0;
    let visible = [];
    let opener = null;

    const show = (i) => {
      current = (i + visible.length) % visible.length;
      const btn = $(".g__btn", visible[current]);
      const thumb = $("img", btn);
      const cap = $(".g__cap", btn);
      const cat = $(".g__cat", cap);
      lbImg.src = btn.dataset.full;
      lbImg.alt = thumb.alt;
      lbCap.textContent = cap.textContent.replace(cat.textContent, "").trim();
      lbCount.textContent = `${String(current + 1).padStart(2, "0")} / ${String(visible.length).padStart(2, "0")}`;
      // Warm the next image
      const next = visible[(current + 1) % visible.length];
      if (next) { const pre = new Image(); pre.src = $(".g__btn", next).dataset.full; }
    };
    const open = (tile) => {
      visible = tiles.filter((t) => !t.classList.contains("is-hidden"));
      opener = document.activeElement;
      show(visible.indexOf(tile));
      lb.hidden = false;
      document.body.classList.add("lb-open");
      requestAnimationFrame(() => requestAnimationFrame(() => lb.classList.add("is-open")));
      lbClose.focus({ preventScroll: true });
    };
    const close = () => {
      lb.classList.remove("is-open");
      document.body.classList.remove("lb-open");
      setTimeout(() => { lb.hidden = true; lbImg.removeAttribute("src"); }, reduceMotion.matches ? 0 : 350);
      if (opener) opener.focus({ preventScroll: true });
    };

    tiles.forEach((t) => $(".g__btn", t).addEventListener("click", () => open(t)));
    lbClose.addEventListener("click", close);
    lbPrev.addEventListener("click", () => show(current - 1));
    lbNext.addEventListener("click", () => show(current + 1));
    lb.addEventListener("click", (e) => { if (e.target === lb) close(); });
    document.addEventListener("keydown", (e) => {
      if (lb.hidden) return;
      if (e.key === "Escape") close();
      else if (e.key === "ArrowLeft") show(current - 1);
      else if (e.key === "ArrowRight") show(current + 1);
      else if (e.key === "Tab") {
        const f = [lbClose, lbPrev, lbNext];
        const idx = f.indexOf(document.activeElement);
        e.preventDefault();
        f[(idx + (e.shiftKey ? -1 : 1) + f.length) % f.length].focus();
      }
    });
    let touchX = null;
    lb.addEventListener("touchstart", (e) => { touchX = e.touches[0].clientX; }, { passive: true });
    lb.addEventListener("touchend", (e) => {
      if (touchX === null) return;
      const dx = e.changedTouches[0].clientX - touchX;
      if (Math.abs(dx) > 50) show(current + (dx < 0 ? 1 : -1));
      touchX = null;
    });
  }

  /* ---------- Interests glow follows pointer ---------- */
  const glow = $("[data-interest-glow]");
  if (glow && finePointer.matches && !reduceMotion.matches) {
    const section = glow.parentElement;
    section.addEventListener("pointermove", (e) => {
      const r = section.getBoundingClientRect();
      glow.style.setProperty("--gx", `${e.clientX - r.left}px`);
      glow.style.setProperty("--gy", `${e.clientY - r.top}px`);
    });
  }

  /* ---------- Magnetic buttons ---------- */
  if (finePointer.matches && !reduceMotion.matches) {
    $$("[data-magnetic]").forEach((btn) => {
      btn.addEventListener("pointermove", (e) => {
        const r = btn.getBoundingClientRect();
        const x = (e.clientX - r.left - r.width / 2) / r.width;
        const y = (e.clientY - r.top - r.height / 2) / r.height;
        btn.style.transform = `translate(${(x * 8).toFixed(1)}px, ${(y * 6).toFixed(1)}px)`;
      });
      btn.addEventListener("pointerleave", () => { btn.style.transform = ""; });
    });
  }
})();
