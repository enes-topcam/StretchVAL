/* main.js - olay baglantilari + baslatma */

function wireEvents() {
    $("#btnRefresh").addEventListener("click", loadMonitors);
    // "Devam et" -> hesap secim menusunu ac
    $("#btnApply").addEventListener("click", (e) => { e.stopPropagation(); toggleApplyMenu(); });
    document.addEventListener("click", (e) => {
        if (!$(".apply-wrap").contains(e.target)) toggleApplyMenu(false);
    });
    $("#btnRevert").addEventListener("click", revertAll);
    $("#modalKeep").addEventListener("click", keepResolution);
    $("#modalClose").addEventListener("click", dismissConfirm);
    $("#modalRevert").addEventListener("click", () => {
        closeConfirmModal();
        revertSelected();
    });
    $("#warnOk").addEventListener("click", () => { $("#warnModal").hidden = true; });

    // Kaydet modal
    $("#saveProfileConfirm").addEventListener("click", confirmSaveProfile);
    $("#saveProfileSkip").addEventListener("click", closeSaveModal);
    $("#profileNameInput").addEventListener("keydown", (e) => {
        if (e.key === "Enter") confirmSaveProfile();
    });
    // Yeni hesap sihirbazi iptal
    $("#waCancel").addEventListener("click", () => { waCancelled = true; closeWizard(); $("#waCancel").textContent = "Vazgeç"; });
}

(async function init() {
    wireEvents();
    await waitForApi();
    await loadMonitors();
    await loadProfiles();
    await autoSelectSaved();   // en son secilen cozunurlugu otomatik sec
})();
