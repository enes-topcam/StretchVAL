/* monitors.js - monitor secimi, aspect filtre, cozunurluk + Hz listesi */

// Stretched icin populer oranlar - vurgulanir
const STRETCHED_ASPECTS = new Set(["4:3", "5:4"]);
// Oranlarin siralama onceligi
const ASPECT_ORDER = ["4:3", "5:4", "16:9", "16:10", "21:9", "3:2", "32:9"];

async function loadMonitors() {
    const layout = $("#monitorLayout");
    layout.innerHTML = '<div class="hint">Monitörler taranıyor…</div>';
    try {
        state.monitors = await window.pywebview.api.get_monitors();
    } catch (e) {
        layout.innerHTML = '<div class="hint">Hata: ' + e + '</div>';
        return;
    }
    renderMonitors();
    $("#btnRevert").disabled = false;
}

function renderMonitors() {
    const layout = $("#monitorLayout");
    layout.innerHTML = "";
    state.monitors.forEach((m, i) => {
        const card = el("div", "monitor");
        card.dataset.device = m.device_name;
        if (m.device_name === state.selectedDevice) card.classList.add("selected");

        const icon = el("div", "mon-icon");
        icon.innerHTML = `<span class="mon-num">${i + 1}</span>`;
        const name = el("div", "mon-name");
        name.textContent = m.friendly_name || m.device_name;
        const res = el("div", "mon-res");
        res.textContent = `${m.current.width} × ${m.current.height} · ${m.current.refresh}Hz`;

        if (m.primary) {
            const tag = el("div", "mon-tag");
            tag.textContent = "Birincil";
            card.appendChild(tag);
        }
        card.appendChild(icon);
        card.appendChild(name);
        card.appendChild(res);

        card.addEventListener("click", () => selectMonitor(m.device_name));
        layout.appendChild(card);
    });
    updateSummary();
}

function currentMonitor() {
    return state.monitors.find((m) => m.device_name === state.selectedDevice);
}

function selectMonitor(device) {
    state.selectedDevice = device;
    state.aspectFilter = null;
    state.selectedMode = null;
    state.selectedHz = null;
    renderMonitors();
    renderAspectChips();
    renderResList();
    resetHz();
    $("#step-res").classList.remove("disabled");
    updateButtons();
}

/* ---------- Aspect filtre cipleri (toggle) ---------- */
function renderAspectChips() {
    const mon = currentMonitor();
    const tabs = $("#aspectTabs");
    tabs.innerHTML = "";

    const byAspect = {};
    for (const mode of mon.modes) {
        (byAspect[mode.aspect] ||= new Set()).add(mode.width + "x" + mode.height);
    }
    const aspects = Object.keys(byAspect).sort((a, b) => {
        const ia = ASPECT_ORDER.indexOf(a), ib = ASPECT_ORDER.indexOf(b);
        return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
    });

    // "Tümü" cipi
    const allChip = el("button", "chip");
    allChip.textContent = "Tümü";
    if (state.aspectFilter === null) allChip.classList.add("active");
    allChip.addEventListener("click", () => setAspectFilter(null));
    tabs.appendChild(allChip);

    for (const asp of aspects) {
        const chip = el("button", "chip");
        if (STRETCHED_ASPECTS.has(asp)) chip.classList.add("stretched-hint");
        if (state.aspectFilter === asp) chip.classList.add("active");
        chip.innerHTML = `${asp} <span class="count">${byAspect[asp].size}</span>`;
        // Tikla filtrele; ayni cipe tekrar tikla -> hepsini goster
        chip.addEventListener("click", () => {
            setAspectFilter(state.aspectFilter === asp ? null : asp);
        });
        tabs.appendChild(chip);
    }
}

function setAspectFilter(asp) {
    state.aspectFilter = asp;
    renderAspectChips();
    renderResList();
}

/* ---------- Cozunurluk listesi (tek kutu) ---------- */
function renderResList() {
    const mon = currentMonitor();
    const box = $("#resList");
    box.innerHTML = "";

    // Benzersiz cozunurlukler + Hz kumeleri
    const resMap = new Map(); // "WxH" -> {width,height,aspect,refreshes:Set}
    for (const mode of mon.modes) {
        if (state.aspectFilter && mode.aspect !== state.aspectFilter) continue;
        const key = mode.width + "x" + mode.height;
        if (!resMap.has(key)) {
            resMap.set(key, {
                width: mode.width, height: mode.height,
                aspect: mode.aspect, refreshes: new Set(),
            });
        }
        resMap.get(key).refreshes.add(mode.refresh);
    }
    const reslist = [...resMap.values()].sort(
        (a, b) => b.width - a.width || b.height - a.height
    );

    for (const r of reslist) {
        const row = el("div", "res-row");
        const isCurrent = mon.current.width === r.width && mon.current.height === r.height;
        const selected = state.selectedMode &&
            state.selectedMode.width === r.width && state.selectedMode.height === r.height;
        if (selected) row.classList.add("selected");

        const dim = el("span", "res-dim");
        dim.textContent = `${r.width} × ${r.height}`;
        const asp = el("span", "res-asp");
        asp.textContent = r.aspect;
        if (STRETCHED_ASPECTS.has(r.aspect)) asp.classList.add("stretched-hint");

        row.appendChild(dim);
        row.appendChild(asp);
        if (isCurrent) {
            const cur = el("span", "res-cur");
            cur.textContent = "şu an";
            row.appendChild(cur);
        }
        row.addEventListener("click", () => selectResolution(r, row));
        box.appendChild(row);
    }

    if (reslist.length === 0) {
        box.innerHTML = '<div class="empty">Bu oranda çözünürlük yok</div>';
    }
}

function selectResolution(r, rowEl) {
    state.selectedMode = { width: r.width, height: r.height };
    document.querySelectorAll(".res-row").forEach((i) => i.classList.remove("selected"));
    rowEl.classList.add("selected");

    // Hz dropdown'i doldur
    const hzs = [...r.refreshes].sort((a, b) => b - a);
    const hzSelect = $("#hzSelect");
    hzSelect.innerHTML = "";
    hzs.forEach((hz) => {
        const opt = el("option");
        opt.value = hz;
        opt.textContent = hz + " Hz";
        hzSelect.appendChild(opt);
    });
    const mon = currentMonitor();
    state.selectedHz = hzs.includes(mon.current.refresh) ? mon.current.refresh : hzs[0];
    hzSelect.value = state.selectedHz;
    hzSelect.disabled = false;
    hzSelect.onchange = () => { state.selectedHz = parseInt(hzSelect.value, 10); updateSummary(); };

    updateButtons();
    updateSummary();
}

function resetHz() {
    const hzSelect = $("#hzSelect");
    hzSelect.innerHTML = "";
    hzSelect.disabled = true;
    state.selectedHz = null;
}

// Bir cozunurlugu (w,h,hz) programatik sec (tiklamadan) - otomatik secim icin
function selectResolutionByValue(width, height, refresh) {
    const mon = currentMonitor();
    if (!mon) return false;
    const refreshes = mon.modes
        .filter((m) => m.width === width && m.height === height)
        .map((m) => m.refresh);
    if (!refreshes.length) return false;  // bu monitor artik desteklemiyor

    state.selectedMode = { width, height };
    const hzs = [...new Set(refreshes)].sort((a, b) => b - a);
    const hzSelect = $("#hzSelect");
    hzSelect.innerHTML = "";
    hzs.forEach((hz) => {
        const opt = el("option");
        opt.value = hz;
        opt.textContent = hz + " Hz";
        hzSelect.appendChild(opt);
    });
    state.selectedHz = hzs.includes(refresh) ? refresh
        : (hzs.includes(mon.current.refresh) ? mon.current.refresh : hzs[0]);
    hzSelect.value = state.selectedHz;
    hzSelect.disabled = false;
    hzSelect.onchange = () => { state.selectedHz = parseInt(hzSelect.value, 10); updateSummary(); };

    renderResList();  // state.selectedMode'a gore ilgili satiri isaretler
    updateButtons();
    updateSummary();
    return true;
}

// Uygulama acilinca en son secilen cozunurlugu otomatik sec (varsa)
async function autoSelectSaved() {
    let prefs;
    try { prefs = await window.pywebview.api.get_prefs(); } catch (e) { prefs = null; }
    const r = prefs && prefs.last_resolution;
    if (!r || !r.width || !r.height) return;

    // Monitor: kayitli olan hala varsa onu, yoksa bu resi destekleyeni, yoksa ilki
    let device = r.device;
    const has = (d) => state.monitors.some((m) => m.device_name === d);
    if (!device || !has(device)) {
        const m = state.monitors.find((mm) =>
            mm.modes.some((md) => md.width === r.width && md.height === r.height));
        device = m ? m.device_name : (state.monitors[0] && state.monitors[0].device_name);
    }
    if (!device) return;

    selectMonitor(device);
    const mon = currentMonitor();
    const md = mon.modes.find((m) => m.width === r.width && m.height === r.height);
    if (!md) return;  // artik desteklenmiyor

    state.aspectFilter = md.aspect;   // ornek: "4:3" bolumune gec
    renderAspectChips();
    renderResList();
    selectResolutionByValue(r.width, r.height, r.refresh);
}

function updateButtons() {
    $("#btnApply").disabled = !(state.selectedDevice && state.selectedMode);
}

function updateSummary() {
    const s = $("#selectionSummary");
    if (!state.selectedDevice) { s.textContent = "Bir monitör seç…"; return; }
    const mon = currentMonitor();
    const idx = state.monitors.indexOf(mon) + 1;
    let txt = `<b>Monitör ${idx}</b>`;
    if (state.selectedMode) {
        txt += ` → <b>${state.selectedMode.width}×${state.selectedMode.height}</b>`;
        if (state.selectedHz) txt += ` @ ${state.selectedHz}Hz`;
    } else {
        txt += " → çözünürlük seç";
    }
    s.innerHTML = txt;
}
