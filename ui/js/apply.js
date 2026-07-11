/* apply.js - stretched uygula, onay/geri-sayim modali, geri al, Valorant baslat */

// targetPuuid: null = son giris yapilan hesap (genel + lastknown), aksi halde o hesap
async function applyResolutionCore(targetPuuid) {
    const { selectedDevice, selectedMode, selectedHz } = state;
    if (!selectedDevice || !selectedMode) return;

    state.appliedTarget = targetPuuid || null;

    // Secilen cozunurlugu hatirla (uygulama tekrar acilinca otomatik secilsin)
    try {
        window.pywebview.api.set_last_resolution(
            selectedDevice, selectedMode.width, selectedMode.height, selectedHz);
    } catch (e) {}

    // 1) Valorant (oyun) acikken ini duzenlenirse cikista geri yazilir -> engelle
    let running = false;
    try { running = await window.pywebview.api.is_game_running(); } catch (e) {}
    if (running) { $("#warnModal").hidden = false; return; }

    // 2) Masaustu cozunurlugu
    const res = await window.pywebview.api.apply_resolution(
        selectedDevice, selectedMode.width, selectedMode.height, selectedHz
    );
    if (!res.ok) { toast(res.message, "err"); return; }

    // 3) Valorant ini'lerini stretched icin duzenle (secilen hesaba gore)
    try {
        state.lastValorant = await window.pywebview.api.apply_valorant(
            selectedMode.width, selectedMode.height, targetPuuid || null
        );
    } catch (e) {
        state.lastValorant = { ok: false, message: "Valorant ayarı yazılamadı: " + e };
    }

    openConfirmModal();
}

function valorantSummaryHTML() {
    const v = state.lastValorant;
    if (!v) return "";
    if (!v.ok) {
        return `<div class="val-line val-warn">Valorant ayarı yapılamadı: ${v.message || v.code || ""}</div>`;
    }
    if (v.changed) {
        return `<div class="val-line val-ok">✓ Valorant ayarları güncellendi (${v.count} dosya)</div>`;
    }
    return `<div class="val-line val-ok">✓ Valorant ayarları zaten stretched'di</div>`;
}

function openConfirmModal() {
    $("#modalTitle").textContent = "Stretched uygulandı ✓";
    $("#modalText").innerHTML =
        `<b>${state.selectedMode.width}×${state.selectedMode.height} @ ${state.selectedHz}Hz</b> uygulandı.`
        + valorantSummaryHTML()
        + `<div class="modal-hint">Valorant hesabına giriş yapabilirsin.</div>`;
    $("#confirmModal").hidden = false;
    // Otomatik geri sayim/geri alma YOK. Kullanici: Valorant'i aç / Kapat / Geri al.
}

function closeConfirmModal() {
    $("#confirmModal").hidden = true;
}

// "Valorant'ı aç" -> pencereyi kapat ve Valorant'i baslat
async function keepResolution() {
    closeConfirmModal();
    await loadMonitors();
    if (state.selectedDevice) { renderAspectChips(); renderResList(); }
    launchValorantNow();
}

// "Kapat" -> stretched'i koru, hicbir sey yapma (Valorant zaten acik olabilir)
async function dismissConfirm() {
    closeConfirmModal();
    await loadMonitors();
    if (state.selectedDevice) { renderAspectChips(); renderResList(); }
    toast("Stretched uygulandı ✓", "ok");
}

async function launchValorantNow() {
    let r;
    try { r = await window.pywebview.api.launch_valorant(); } catch (e) { r = { ok: false, message: String(e) }; }
    if (r && r.ok) toast("Valorant açılıyor…", "ok");
    else toast((r && r.message) || "Valorant açılamadı", "err");
}

async function revertSelected() {
    if (!state.selectedDevice) return;
    const res = await window.pywebview.api.revert(state.selectedDevice);
    if (res.ok) { await loadMonitors(); toast("Önceki çözünürlüğe dönüldü", "ok"); }
    else toast(res.message, "err");
}

async function revertAll() {
    const res = await window.pywebview.api.revert_all();
    await loadMonitors();
    if (res.ok) toast("Tüm monitörler orijinaline döndü", "ok");
    else toast("Bazı monitörler geri alınamadı", "err");
}
