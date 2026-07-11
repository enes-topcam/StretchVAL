/* core.js - paylasilan durum, DOM yardimcilari, toast */

const state = {
    monitors: [],
    selectedDevice: null,
    aspectFilter: null,   // null = hepsi, aksi halde "4:3" gibi
    selectedMode: null,   // {width,height}
    selectedHz: null,
    // Profiller / hesaplar
    profiles: [],
    lastKnownUser: null,
    appliedTarget: null,     // son uygulamada hedeflenen puuid (null = son giris hesabi)
    pendingSavePuuid: null,
    afterSaveModal: null,    // isim modali kapaninca calisacak fonksiyon (varsa)
    lastValorant: null,
};

// pywebview.api hazir olana kadar bekle.
// Sadece .api nesnesinin varligi yetmez; metotlarin (ornek: get_monitors)
// gercekten baglanmis olmasini bekleriz -> aksi halde exe'de yaris olusuyor.
function waitForApi() {
    const ready = () =>
        window.pywebview && window.pywebview.api &&
        typeof window.pywebview.api.get_monitors === "function";
    return new Promise((resolve) => {
        if (ready()) return resolve();
        window.addEventListener("pywebviewready", () => { if (ready()) resolve(); });
        const t = setInterval(() => {
            if (ready()) { clearInterval(t); resolve(); }
        }, 50);
    });
}

const $ = (sel) => document.querySelector(sel);
const el = (tag, cls) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    return e;
};
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function shortId(puuid) {
    return puuid ? puuid.slice(0, 8) + "…" : "";
}

// Kayitli profil varsa adini, yoksa kisa ID'yi dondurur (algilama mesajlari icin)
function accountLabel(puuid) {
    const p = state.profiles.find((x) => x.puuid === puuid);
    return p ? p.nickname : shortId(puuid);
}

function escapeHtml(s) {
    return (s || "").replace(/[&<>"']/g, (c) =>
        ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// ---------- Toast ----------
let toastTimer = null;
function toast(msg, kind) {
    const t = $("#toast");
    t.textContent = msg;
    t.className = "toast " + (kind || "");
    t.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { t.hidden = true; }, 3500);
}
