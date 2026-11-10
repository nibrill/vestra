(() => {
  "use strict";
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const safe = (fn) => { try { return fn(); } catch (_) { return null; } };

  // ---- Theme -------------------------------------------------------------
  const root = document.documentElement;
  const stored = safe(() => localStorage.getItem("vestra-theme"));
  const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  const setTheme = (t) => {
    root.dataset.theme = t;
    $$("[data-theme-toggle] i").forEach((i) => (i.className = t === "dark" ? "fa-solid fa-sun" : "fa-regular fa-moon"));
  };
  const forced = new URLSearchParams(location.search).get("theme");  // ?theme=dark para previsualizar
  setTheme(forced === "dark" || forced === "light" ? forced : stored || (prefersDark ? "dark" : "light"));
  $$("[data-theme-toggle]").forEach((b) =>
    b.addEventListener("click", () => {
      const next = root.dataset.theme === "dark" ? "light" : "dark";
      setTheme(next);
      safe(() => localStorage.setItem("vestra-theme", next));
    })
  );

  // ---- Sticky nav shadow -------------------------------------------------
  const nav = $(".nav");
  if (nav) {
    const onScroll = () => nav.classList.toggle("scrolled", window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  // ---- Drawers (store + admin) ------------------------------------------
  $$("[data-toggle]").forEach((btn) =>
    btn.addEventListener("click", () => {
      const target = $(btn.dataset.toggle);
      if (target) target.classList.toggle("open");
    })
  );
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") $$(".drawer.open, .admin__side.open").forEach((d) => d.classList.remove("open"));
  });
  $$(".drawer-backdrop").forEach((b) => b.addEventListener("click", () => $$(".drawer.open").forEach((d) => d.classList.remove("open"))));

  // ---- Toasts ------------------------------------------------------------
  $$(".toast").forEach((t, i) => {
    setTimeout(() => {
      t.classList.add("out");
      setTimeout(() => t.remove(), 400);
    }, 4200 + i * 600);
    t.addEventListener("click", () => t.remove());
  });

  // ---- Reveal on scroll --------------------------------------------------
  const reveals = $$(".reveal");
  if ("IntersectionObserver" in window && reveals.length) {
    const io = new IntersectionObserver(
      (entries) => entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } }),
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );
    reveals.forEach((el, i) => { el.style.setProperty("--i", i % 4); io.observe(el); });
  } else reveals.forEach((el) => el.classList.add("in"));

  // ---- Password visibility ----------------------------------------------
  $$(".toggle-pass").forEach((btn) =>
    btn.addEventListener("click", () => {
      const input = btn.parentElement.querySelector("input");
      const show = input.type === "password";
      input.type = show ? "text" : "password";
      btn.querySelector("i").className = show ? "fa-regular fa-eye-slash" : "fa-regular fa-eye";
    })
  );

  // ---- Confirm dialogs on destructive forms ------------------------------
  $$("form[data-confirm]").forEach((f) =>
    f.addEventListener("submit", (e) => { if (!confirm(f.dataset.confirm)) e.preventDefault(); })
  );

  // ---- Auto-submit selects ----------------------------------------------
  $$("[data-autosubmit]").forEach((s) => s.addEventListener("change", () => s.form.submit()));
  $$("[data-nav-select]").forEach((s) => s.addEventListener("change", () => (window.location.href = s.value)));

  // ---- Image dropzone preview -------------------------------------------
  $$(".dropzone").forEach((zone) => {
    const input = $("input[type=file]", zone);
    const label = $(".dz-label", zone);
    const show = (file) => {
      if (!file || !file.type.startsWith("image/")) return;
      const url = URL.createObjectURL(file);
      let img = $("img.dz-preview", zone);
      if (!img) { img = document.createElement("img"); img.className = "dz-preview"; zone.prepend(img); }
      img.src = url;
      if (label) label.textContent = file.name;
    };
    input.addEventListener("change", () => show(input.files[0]));
    ["dragenter", "dragover"].forEach((ev) => zone.addEventListener(ev, (e) => { e.preventDefault(); zone.classList.add("drag"); }));
    ["dragleave", "drop"].forEach((ev) => zone.addEventListener(ev, (e) => { e.preventDefault(); zone.classList.remove("drag"); }));
    zone.addEventListener("drop", (e) => { input.files = e.dataTransfer.files; show(input.files[0]); });
  });

  // ---- Slug helper (admin categories) -----------------------------------
  const nombre = $("[data-slug-source]");
  const slug = $("[data-slug-target]");
  if (nombre && slug) {
    nombre.addEventListener("input", () => {
      if (slug.dataset.touched) return;
      slug.value = nombre.value.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
    });
    slug.addEventListener("input", () => (slug.dataset.touched = "1"));
  }
})();
