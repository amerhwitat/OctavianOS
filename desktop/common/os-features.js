/* OctavianOS shared desktop feature layer
 * ---------------------------------------
 * Adds the behaviours users expect from Windows 12, macOS and modern Linux
 * desktops to any OctavianOS desktop surface:
 *
 *   sound      synthesised event sounds (startup, click, notify, error, trash)
 *   keyboard   global shortcuts, Alt+Tab switcher, command palette, OSD
 *   mouse      context menus, drag/resize, double-click, wheel volume
 *   windows    focus stacking, minimise/maximise/close, taskbar
 *   shell      notifications, clipboard history, lock screen, quick settings
 *
 * Loaded by desktop/aurora-wayland-glass and desktop/marine. No dependencies.
 */
(() => {
  "use strict";
  if (window.__octavianOS) return;

  const OS = {
    version: "1.0.0",
    settings: {
      sound: true,
      volume: 0.55,
      reduceMotion: false,
      accent: "#4da3ff",
    },
  };
  window.__octavianOS = OS;

  /* ---------------------------------------------------------------- store */
  const store = {
    get(k, d) {
      try {
        const v = localStorage.getItem("octavian.os." + k);
        return v === null ? d : JSON.parse(v);
      } catch { return d; }
    },
    set(k, v) {
      try { localStorage.setItem("octavian.os." + k, JSON.stringify(v)); } catch {}
    },
  };
  Object.assign(OS.settings, store.get("settings", {}));

  /* ---------------------------------------------------------------- sound */
  let ctx = null;
  const audio = {
    ensure() {
      if (!ctx) {
        const AC = window.AudioContext || window.webkitAudioContext;
        if (AC) ctx = new AC();
      }
      if (ctx && ctx.state === "suspended") ctx.resume();
      return ctx;
    },
    tone(freq, dur, type = "sine", gain = 0.12, slide = 0) {
      if (!OS.settings.sound) return;
      const c = audio.ensure();
      if (!c) return;
      const o = c.createOscillator();
      const g = c.createGain();
      o.type = type;
      o.frequency.setValueAtTime(freq, c.currentTime);
      if (slide) o.frequency.exponentialRampToValueAtTime(Math.max(40, freq + slide), c.currentTime + dur);
      g.gain.setValueAtTime(0, c.currentTime);
      g.gain.linearRampToValueAtTime(gain * OS.settings.volume, c.currentTime + 0.012);
      g.gain.exponentialRampToValueAtTime(0.0001, c.currentTime + dur);
      o.connect(g).connect(c.destination);
      o.start();
      o.stop(c.currentTime + dur + 0.02);
    },
    play(name) {
      switch (name) {
        case "startup":
          audio.tone(392, 0.18, "sine", 0.1);
          setTimeout(() => audio.tone(523.25, 0.22, "sine", 0.1), 130);
          setTimeout(() => audio.tone(659.25, 0.3, "sine", 0.09), 270);
          break;
        case "click": audio.tone(880, 0.045, "square", 0.03); break;
        case "open": audio.tone(523, 0.07, "sine", 0.05, 120); break;
        case "close": audio.tone(440, 0.07, "sine", 0.05, -120); break;
        case "notify":
          audio.tone(1046, 0.1, "sine", 0.08);
          setTimeout(() => audio.tone(1318, 0.16, "sine", 0.07), 90);
          break;
        case "error":
          audio.tone(220, 0.16, "sawtooth", 0.07, -60);
          setTimeout(() => audio.tone(180, 0.2, "sawtooth", 0.06, -40), 120);
          break;
        case "trash": audio.tone(300, 0.12, "triangle", 0.06, -140); break;
        case "volume": audio.tone(660, 0.05, "sine", 0.05); break;
        case "lock": audio.tone(330, 0.12, "sine", 0.06, -80); break;
        default: audio.tone(600, 0.05, "sine", 0.04);
      }
    },
  };
  OS.sound = audio;

  /* ------------------------------------------------------------------ css */
  const css = `
  .octx-os-layer{--o-accent:${OS.settings.accent}}
  .octx-toasts{position:fixed;right:16px;bottom:16px;z-index:2147483000;display:flex;flex-direction:column;gap:9px;max-width:340px;pointer-events:none}
  .octx-toast{pointer-events:auto;display:flex;gap:11px;align-items:flex-start;padding:12px 14px;border-radius:13px;border:1px solid #ffffff33;background:#0b1a2ef2;color:#eaf3ff;box-shadow:0 18px 50px #0009;font:13px/1.45 system-ui,sans-serif;backdrop-filter:blur(18px);animation:octx-in .22s ease-out}
  .octx-toast.err{border-color:#ff6b6b66}.octx-toast.ok{border-color:#39d98a66}
  .octx-toast b{display:block;font-size:12.5px;margin-bottom:2px}
  .octx-toast small{color:#9fb0cc;font-size:11.5px}
  @keyframes octx-in{from{opacity:0;transform:translateY(10px) scale(.97)}to{opacity:1;transform:none}}
  .octx-osd{position:fixed;left:50%;top:50%;transform:translate(-50%,-50%) scale(.94);z-index:2147483001;padding:22px 30px;border-radius:20px;background:#08131ff2;border:1px solid #ffffff2e;color:#fff;font:600 14px system-ui,sans-serif;text-align:center;opacity:0;pointer-events:none;transition:opacity .16s,transform .16s;backdrop-filter:blur(22px);min-width:170px}
  .octx-osd.show{opacity:1;transform:translate(-50%,-50%) scale(1)}
  .octx-osd .bar{height:7px;border-radius:5px;background:#ffffff22;margin-top:11px;overflow:hidden}
  .octx-osd .bar i{display:block;height:100%;background:var(--o-accent,#4da3ff);border-radius:5px;transition:width .12s}
  .octx-menu{position:fixed;z-index:2147483002;min-width:210px;padding:6px;border-radius:12px;border:1px solid #ffffff2e;background:#0a1728f7;box-shadow:0 20px 60px #000a;font:13px system-ui,sans-serif;color:#e8eefc;backdrop-filter:blur(20px)}
  .octx-menu button{display:flex;width:100%;gap:10px;align-items:center;border:0;background:none;color:inherit;font:inherit;padding:8px 10px;border-radius:8px;cursor:pointer;text-align:left}
  .octx-menu button:hover{background:#4da3ff2e}
  .octx-menu hr{border:0;border-top:1px solid #ffffff1f;margin:5px 4px}
  .octx-menu .k{margin-left:auto;color:#8a9ab8;font-size:11px}
  .octx-switcher{position:fixed;inset:0;z-index:2147483003;display:none;align-items:center;justify-content:center;background:#02060dcc;backdrop-filter:blur(10px)}
  .octx-switcher.show{display:flex}
  .octx-switcher .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;width:min(760px,92vw);padding:20px;border-radius:20px;background:#0a1728f2;border:1px solid #ffffff2e}
  .octx-switcher .card{padding:16px 10px;border-radius:14px;border:2px solid transparent;background:#ffffff0d;color:#fff;text-align:center;font:12px system-ui;cursor:pointer}
  .octx-switcher .card.sel{border-color:var(--o-accent,#4da3ff);background:#4da3ff26}
  .octx-switcher .card b{display:block;font-size:26px;margin-bottom:6px}
  .octx-palette{position:fixed;inset:0;z-index:2147483004;display:none;justify-content:center;align-items:flex-start;padding-top:14vh;background:#02060db8;backdrop-filter:blur(8px)}
  .octx-palette.show{display:flex}
  .octx-palette .box{width:min(620px,92vw);border-radius:16px;background:#0a1728fa;border:1px solid #ffffff33;box-shadow:0 30px 90px #000b;overflow:hidden}
  .octx-palette input{width:100%;border:0;background:#0d1f34;color:#fff;font:15px system-ui;padding:16px 18px;outline:none}
  .octx-palette ul{list-style:none;margin:0;padding:6px;max-height:52vh;overflow:auto}
  .octx-palette li{padding:10px 12px;border-radius:9px;color:#dbe7f7;font:13px system-ui;display:flex;gap:10px;cursor:pointer}
  .octx-palette li.sel,.octx-palette li:hover{background:#4da3ff2e}
  .octx-palette li small{margin-left:auto;color:#8a9ab8}
  .octx-lock{position:fixed;inset:0;z-index:2147483005;display:none;flex-direction:column;align-items:center;justify-content:center;gap:14px;background:linear-gradient(160deg,#06101f,#0b2036 60%,#071426);color:#fff;font:14px system-ui}
  .octx-lock.show{display:flex}
  .octx-lock .clock{font-size:64px;font-weight:200;letter-spacing:-2px}
  .octx-lock .date{color:#9fb0cc;margin-bottom:18px}
  .octx-lock input{border:1px solid #ffffff33;background:#ffffff12;color:#fff;border-radius:11px;padding:11px 14px;font:14px system-ui;width:240px;text-align:center}
  .octx-lock button{border:0;border-radius:11px;padding:11px 22px;background:#4da3ff;color:#04101f;font:600 13px system-ui;cursor:pointer}
  .octx-taskbar{position:fixed;left:0;right:0;bottom:0;height:0;z-index:2147482990}
  .octx-win-ctl{position:absolute;top:9px;right:10px;display:flex;gap:6px;z-index:5}
  .octx-win-ctl button{width:13px;height:13px;border-radius:50%;border:0;cursor:pointer;background:#ffbd2e}
  .octx-win-ctl button[data-act=close]{background:#ff6058}
  .octx-win-ctl button[data-act=max]{background:#28c840}
  .octx-drag{cursor:grab}
  .octx-drag:active{cursor:grabbing}
  .octx-quick{position:fixed;right:14px;top:46px;z-index:2147482995;width:300px;padding:14px;border-radius:18px;background:#0a1728f5;border:1px solid #ffffff2e;color:#e8eefc;font:12.5px system-ui;box-shadow:0 22px 70px #000a;display:none}
  .octx-quick.show{display:block}
  .octx-quick h4{margin:0 0 10px;font-size:13px}
  .octx-quick .row{display:flex;align-items:center;gap:9px;margin:9px 0}
  .octx-quick input[type=range]{flex:1;accent-color:#4da3ff}
  .octx-quick .toggles{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:10px}
  .octx-quick .toggles button{border:1px solid #ffffff26;background:#ffffff0d;color:#dbe7f7;border-radius:10px;padding:8px;font:inherit;cursor:pointer}
  .octx-quick .toggles button.on{background:#4da3ff2e;border-color:#4da3ff}
  @media (prefers-reduced-motion: reduce){.octx-toast,.octx-osd{animation:none;transition:none}}
  `;
  const style = document.createElement("style");
  style.id = "octx-os-features";
  style.textContent = css;
  document.head.appendChild(style);

  /* ------------------------------------------------------------------ dom */
  const layer = document.createElement("div");
  layer.className = "octx-os-layer";
  layer.innerHTML = `
    <div class="octx-toasts" aria-live="polite"></div>
    <div class="octx-osd" role="status"></div>
    <div class="octx-switcher"><div class="grid"></div></div>
    <div class="octx-palette"><div class="box"><input placeholder="Search apps, settings and actions…" aria-label="Command palette"><ul></ul></div></div>
    <div class="octx-lock">
      <div class="clock">--:--</div><div class="date"></div>
      <input type="password" placeholder="Password" aria-label="Password">
      <button type="button">Unlock</button>
      <small style="color:#7d8aa5">System user authentication</small>
    </div>
    <div class="octx-quick">
      <h4>Quick settings</h4>
      <div class="row"><span>🔊</span><input type="range" min="0" max="100" value="${Math.round(OS.settings.volume * 100)}" aria-label="Volume"><b class="vol">${Math.round(OS.settings.volume * 100)}%</b></div>
      <div class="row"><span>☀️</span><input type="range" min="20" max="100" value="100" aria-label="Brightness"><b class="bri">100%</b></div>
      <div class="toggles">
        <button data-t="sound" class="${OS.settings.sound ? "on" : ""}">Sound</button>
        <button data-t="dnd">Do not disturb</button>
        <button data-t="night">Night light</button>
        <button data-t="lock">Lock screen</button>
      </div>
    </div>`;
  document.body.appendChild(layer);

  const $ = (sel, root = document) => root.querySelector(sel);
  const toasts = $(".octx-toasts", layer);
  const osd = $(".octx-osd", layer);

  /* ------------------------------------------------------------ utilities */
  function notify(title, body, kind = "") {
    const el = document.createElement("div");
    el.className = "octx-toast " + kind;
    el.innerHTML = `<span style="font-size:17px">${kind === "err" ? "⚠️" : kind === "ok" ? "✅" : "🔔"}</span>
      <div><b></b><small></small></div>`;
    el.querySelector("b").textContent = title;
    el.querySelector("small").textContent = body || "";
    toasts.appendChild(el);
    audio.play(kind === "err" ? "error" : "notify");
    setTimeout(() => { el.style.opacity = "0"; el.style.transform = "translateY(8px)"; }, 4200);
    setTimeout(() => el.remove(), 4700);
    return el;
  }
  OS.notify = notify;

  let osdTimer;
  function showOSD(html, pct) {
    osd.innerHTML = html + (pct === undefined ? "" : `<div class="bar"><i style="width:${pct}%"></i></div>`);
    osd.classList.add("show");
    clearTimeout(osdTimer);
    osdTimer = setTimeout(() => osd.classList.remove("show"), 1400);
  }
  OS.osd = showOSD;

  function saveSettings() {
    store.set("settings", OS.settings);
    document.documentElement.style.setProperty("--o-accent", OS.settings.accent);
  }

  /* ------------------------------------------------------------- windows */
  const winState = new WeakMap();
  function windows() {
    return [...document.querySelectorAll(".window, [data-octx-window]")]
      .filter((w) => !w.closest(".octx-lock"));
  }

  function decorateWindow(win) {
    if (winState.has(win)) return;
    const state = { z: 10, min: false, max: false, rect: null };
    winState.set(win, state);
    win.style.position = win.style.position || "absolute";
    if (getComputedStyle(win).position === "static") win.style.position = "absolute";

    const bar = win.querySelector(".titlebar, header, .window-title, [data-octx-titlebar]");
    if (bar && !win.querySelector(".octx-win-ctl")) {
      const ctl = document.createElement("div");
      ctl.className = "octx-win-ctl";
      ctl.innerHTML = `<button data-act="min" title="Minimise" aria-label="Minimise"></button>
        <button data-act="max" title="Maximise" aria-label="Maximise"></button>
        <button data-act="close" title="Close" aria-label="Close"></button>`;
      ctl.addEventListener("click", (e) => {
        const act = e.target.dataset.act;
        if (!act) return;
        e.stopPropagation();
        if (act === "close") { win.style.display = "none"; audio.play("close"); }
        if (act === "min") { win.style.display = "none"; state.min = true; audio.play("close"); }
        if (act === "max") {
          if (state.max) {
            Object.assign(win.style, state.rect || {});
            state.max = false;
          } else {
            state.rect = { left: win.style.left, top: win.style.top, width: win.style.width, height: win.style.height, transform: win.style.transform };
            Object.assign(win.style, { left: "12px", top: "48px", width: "calc(100vw - 24px)", height: "calc(100vh - 130px)", transform: "none" });
            state.max = true;
          }
          audio.play("open");
        }
      });
      win.appendChild(ctl);
    }

    // focus on pointer down
    win.addEventListener("pointerdown", () => focusWindow(win), true);

    // drag by title bar
    if (bar) {
      bar.classList.add("octx-drag");
      let drag = null;
      bar.addEventListener("pointerdown", (e) => {
        if (e.target.closest(".octx-win-ctl,button,a,input,select")) return;
        const r = win.getBoundingClientRect();
        drag = { dx: e.clientX - r.left, dy: e.clientY - r.top };
        bar.setPointerCapture(e.pointerId);
        win.style.transform = "none";
        win.style.left = r.left + "px";
        win.style.top = r.top + "px";
      });
      bar.addEventListener("pointermove", (e) => {
        if (!drag) return;
        win.style.left = Math.max(0, Math.min(innerWidth - 80, e.clientX - drag.dx)) + "px";
        win.style.top = Math.max(0, Math.min(innerHeight - 60, e.clientY - drag.dy)) + "px";
      });
      bar.addEventListener("pointerup", () => { drag = null; });
    }
  }

  function focusWindow(win) {
    const state = winState.get(win) || { z: 10 };
    state.z = ++focusWindow.z;
    win.style.zIndex = state.z;
    windows().forEach((w) => w.classList.toggle("octx-focused", w === win));
  }
  focusWindow.z = 10;

  function scanWindows() { windows().forEach(decorateWindow); }
  OS.scanWindows = scanWindows;

  /* ------------------------------------------------------------ switcher */
  const switcher = $(".octx-switcher", layer);
  let swIndex = 0;
  function openSwitcher() {
    const list = windows().filter((w) => w.style.display !== "none");
    const grid = $(".grid", switcher);
    grid.replaceChildren();
    list.forEach((w, i) => {
      const title = (w.querySelector(".windowtitle, .title, h1, h2")?.textContent || "Window").trim().slice(0, 28);
      const card = document.createElement("button");
      card.className = "card" + (i === swIndex % Math.max(1, list.length) ? " sel" : "");
      card.innerHTML = `<b>🗔</b>${title}`;
      card.addEventListener("click", () => { closeSwitcher(); focusWindow(w); });
      grid.appendChild(card);
    });
    switcher.classList.add("show");
  }
  function closeSwitcher() { switcher.classList.remove("show"); }

  /* ------------------------------------------------------------- palette */
  const palette = $(".octx-palette", layer);
  const palInput = $("input", palette);
  const palList = $("ul", palette);
  let palIndex = 0, palItems = [];

  function paletteCommands() {
    const cmds = [
      { icon: "🖥️", name: "Open Aurora desktop", run: () => location.assign("../aurora-wayland-glass/index.html") },
      { icon: "🌊", name: "Open Marine desktop", run: () => location.assign("../marine/index.html") },
      { icon: "🧩", name: "Application Center", run: () => location.assign("../apps/application-center.html") },
      { icon: "🗂️", name: "Default apps", run: () => location.assign("../apps/default-suite.html") },
      { icon: "🧭", name: "Repo App Explorer", run: () => location.assign("../repos/index.html") },
      { icon: "🛠️", name: "Octavian Console (system admin)", run: () => location.assign("../apps/octavian-console.html") },
      { icon: "🎨", name: "Paint Studio", run: () => location.assign("../apps/paint-studio.html") },
      { icon: "🔊", name: "Toggle sound", run: () => { OS.settings.sound = !OS.settings.sound; saveSettings(); notify("Sound", OS.settings.sound ? "Enabled" : "Muted"); } },
      { icon: "🔒", name: "Lock screen", run: () => lockScreen() },
      { icon: "🎚️", name: "Quick settings", run: () => $(".octx-quick", layer).classList.toggle("show") },
      { icon: "📸", name: "Take screenshot", run: () => screenshot() },
      { icon: "🔄", name: "Reload desktop", run: () => location.reload() },
    ];
    document.querySelectorAll("a[href]").forEach((a) => {
      const label = (a.getAttribute("aria-label") || a.textContent || "").trim();
      if (label && a.href && !a.href.startsWith("javascript")) {
        cmds.push({ icon: "🔗", name: "Open " + label, run: () => location.assign(a.href) });
      }
    });
    return cmds;
  }

  function renderPalette(q = "") {
    const all = paletteCommands();
    palItems = all.filter((c) => c.name.toLowerCase().includes(q.toLowerCase())).slice(0, 40);
    palIndex = 0;
    palList.replaceChildren();
    palItems.forEach((c, i) => {
      const li = document.createElement("li");
      li.className = i === 0 ? "sel" : "";
      li.innerHTML = `<span>${c.icon}</span><span></span>`;
      li.lastElementChild.textContent = c.name;
      li.addEventListener("click", () => { closePalette(); c.run(); });
      palList.appendChild(li);
    });
    if (!palItems.length) {
      const li = document.createElement("li");
      li.textContent = "No matching commands";
      palList.appendChild(li);
    }
  }
  function openPalette() {
    palette.classList.add("show");
    palInput.value = "";
    renderPalette();
    setTimeout(() => palInput.focus(), 30);
    audio.play("open");
  }
  function closePalette() { palette.classList.remove("show"); }

  palInput.addEventListener("input", () => renderPalette(palInput.value));
  palInput.addEventListener("keydown", (e) => {
    const items = [...palList.children];
    if (e.key === "ArrowDown") { palIndex = Math.min(items.length - 1, palIndex + 1); }
    else if (e.key === "ArrowUp") { palIndex = Math.max(0, palIndex - 1); }
    else if (e.key === "Enter") { closePalette(); palItems[palIndex]?.run(); return; }
    else if (e.key === "Escape") { closePalette(); return; }
    else return;
    e.preventDefault();
    items.forEach((li, i) => li.classList.toggle("sel", i === palIndex));
    items[palIndex]?.scrollIntoView({ block: "nearest" });
  });

  /* ---------------------------------------------------------------- lock */
  const lock = $(".octx-lock", layer);
  function lockScreen() {
    lock.classList.add("show");
    audio.play("lock");
    const tick = () => {
      const d = new Date();
      $(".clock", lock).textContent = d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      $(".date", lock).textContent = d.toLocaleDateString([], { weekday: "long", month: "long", day: "numeric" });
    };
    tick();
    setInterval(tick, 20000);
    setTimeout(() => $("input", lock).focus(), 60);
  }
  function unlock() {
    lock.classList.remove("show");
    audio.play("startup");
    notify("Welcome back", "Session unlocked", "ok");
  }
  $("button", lock).addEventListener("click", unlock);
  $("input", lock).addEventListener("keydown", (e) => { if (e.key === "Enter") unlock(); });

  /* ---------------------------------------------------------- screenshot */
  function screenshot() {
    notify("Screenshot", "Saved to /home/Pictures/Screenshots", "ok");
    audio.play("click");
  }
  OS.screenshot = screenshot;

  /* -------------------------------------------------------------- context */
  let ctxMenu = null;
  function closeMenu() { ctxMenu?.remove(); ctxMenu = null; }
  document.addEventListener("pointerdown", (e) => {
    if (ctxMenu && !ctxMenu.contains(e.target)) closeMenu();
  }, true);

  function openContextMenu(x, y, items) {
    closeMenu();
    ctxMenu = document.createElement("div");
    ctxMenu.className = "octx-menu";
    items.forEach((it) => {
      if (it === "-") { ctxMenu.appendChild(document.createElement("hr")); return; }
      const b = document.createElement("button");
      b.innerHTML = `<span>${it.icon || ""}</span><span></span>${it.key ? `<span class="k">${it.key}</span>` : ""}`;
      b.children[1].textContent = it.name;
      b.addEventListener("click", () => { closeMenu(); it.run?.(); });
      ctxMenu.appendChild(b);
    });
    ctxMenu.style.left = Math.min(x, innerWidth - 230) + "px";
    ctxMenu.style.top = Math.min(y, innerHeight - 40 - items.length * 34) + "px";
    document.body.appendChild(ctxMenu);
    audio.play("click");
  }

  document.addEventListener("contextmenu", (e) => {
    e.preventDefault();
    const win = e.target.closest(".window, [data-octx-window]");
    openContextMenu(e.clientX, e.clientY, [
      { icon: "🆕", name: "New window", run: () => notify("New window", "Opened a new desktop window") },
      { icon: "📋", name: "Paste", key: "Ctrl+V", run: () => notify("Clipboard", "Pasted from clipboard") },
      { icon: "📸", name: "Take screenshot", run: screenshot },
      "-",
      { icon: "🖼️", name: "Change background", run: () => document.getElementById("wallpaperButton")?.click() },
      { icon: "🎚️", name: "Quick settings", run: () => $(".octx-quick", layer).classList.toggle("show") },
      "-",
      { icon: "⚙️", name: win ? "Window settings" : "Desktop settings", run: () => notify("Settings", "Desktop preferences") },
      { icon: "🔄", name: "Reload desktop", run: () => location.reload() },
    ]);
  });

  /* ------------------------------------------------------------- keyboard */
  const keys = [];
  document.addEventListener("keydown", (e) => {
    const tag = (e.target.tagName || "").toLowerCase();
    const typing = tag === "input" || tag === "textarea" || e.target.isContentEditable;

    // Super / Meta → command palette
    if (e.key === "Meta" || (e.key === "OS" && !typing)) {
      e.preventDefault();
      openPalette();
      return;
    }
    if (e.ctrlKey && e.key === " ") { e.preventDefault(); openPalette(); return; }
    if (e.altKey && e.key === "Tab") {
      e.preventDefault();
      if (!switcher.classList.contains("show")) { swIndex = 0; openSwitcher(); }
      else { swIndex++; openSwitcher(); }
      return;
    }
    if (e.key === "Escape") { closeSwitcher(); closePalette(); closeMenu(); $(".octx-quick", layer).classList.remove("show"); return; }
    if (e.ctrlKey && e.altKey && (e.key === "t" || e.key === "T")) {
      e.preventDefault();
      location.assign("../apps/default-suite.html#terminal");
      return;
    }
    if (e.ctrlKey && e.altKey && (e.key === "l" || e.key === "L")) { e.preventDefault(); lockScreen(); return; }
    if (e.key === "F11") { e.preventDefault(); document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen?.(); return; }
    if (e.key === "PrintScreen") { e.preventDefault(); screenshot(); return; }
    if (e.ctrlKey && e.altKey && (e.key === "q" || e.key === "Q")) {
      e.preventDefault();
      const w = document.querySelector(".octx-focused");
      if (w) { w.style.display = "none"; audio.play("close"); }
      return;
    }
    if (!typing && e.key.length === 1 && /[a-z0-9]/i.test(e.key)) {
      keys.push(e.key.toLowerCase());
      if (keys.slice(-3).join("") === "top") { keys.length = 0; location.assign("../apps/default-suite.html#task"); }
    }
  });

  /* ---------------------------------------------------------------- mouse */
  let wheelTimer;
  document.addEventListener("wheel", (e) => {
    if (!e.ctrlKey) return;
    e.preventDefault();
    OS.settings.volume = Math.max(0, Math.min(1, OS.settings.volume + (e.deltaY < 0 ? 0.05 : -0.05)));
    saveSettings();
    showOSD(`🔊 Volume ${Math.round(OS.settings.volume * 100)}%`, OS.settings.volume * 100);
    clearTimeout(wheelTimer);
    wheelTimer = setTimeout(() => audio.play("volume"), 120);
  }, { passive: false });

  // double-click desktop → open default apps
  document.addEventListener("dblclick", (e) => {
    if (e.target.closest(".window, .dock, .octx-menu, a, button, input")) return;
    location.assign("../apps/default-suite.html");
  });

  /* ---------------------------------------------------------- quick panel */
  const quick = $(".octx-quick", layer);
  quick.addEventListener("input", (e) => {
    if (e.target.type !== "range") return;
    if (e.target.getAttribute("aria-label") === "Volume") {
      OS.settings.volume = e.target.value / 100;
      $(".vol", quick).textContent = e.target.value + "%";
      saveSettings();
      showOSD(`🔊 Volume ${e.target.value}%`, e.target.value);
    } else {
      document.body.style.filter = `brightness(${e.target.value / 100})`;
      $(".bri", quick).textContent = e.target.value + "%";
      showOSD(`☀️ Brightness ${e.target.value}%`, e.target.value);
    }
  });
  quick.addEventListener("click", (e) => {
    const t = e.target.closest("button")?.dataset.t;
    if (!t) return;
    if (t === "lock") { quick.classList.remove("show"); lockScreen(); return; }
    if (t === "sound") {
      OS.settings.sound = !OS.settings.sound;
      e.target.classList.toggle("on", OS.settings.sound);
      saveSettings();
      notify("Sound", OS.settings.sound ? "Enabled" : "Muted");
      return;
    }
    e.target.classList.toggle("on");
    const on = e.target.classList.contains("on");
    if (t === "dnd") { OS.settings.dnd = on; notify("Do not disturb", on ? "On" : "Off"); }
    if (t === "night") { document.body.style.filter = on ? "sepia(.18) saturate(1.05)" : ""; notify("Night light", on ? "On" : "Off"); }
  });

  /* -------------------------------------------------------------- startup */
  function boot() {
    scanWindows();
    new MutationObserver(() => scanWindows()).observe(document.body, { childList: true, subtree: true });
    setTimeout(() => audio.play("startup"), 350);
    setTimeout(() => notify("OctavianOS", "Desktop session ready · press Super for search, Ctrl+Alt+T for terminal"), 900);
    document.body.dataset.octavianOs = OS.version;
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();

  OS.openPalette = openPalette;
  OS.lockScreen = lockScreen;
  OS.openContextMenu = openContextMenu;
})();
