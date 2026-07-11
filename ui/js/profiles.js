/* profiles.js - profiller, "Devam et" hesap secici, profil kaydet modali */

async function loadProfiles() {
    try {
        const r = await window.pywebview.api.get_profiles();
        state.profiles = r.profiles || [];
        state.lastKnownUser = r.last_known_user || null;
    } catch (e) {
        state.profiles = [];
    }
    if (!$("#applyMenu").hidden) renderAccountPicker();
}

// Bu hesabin kullanici-verili bir ismi var mi? (yoksa secince isim sorariz)
// Kayitli degil VEYA kayitli ama named!==true -> isim gerekiyor.
function accountNeedsName(puuid) {
    if (!puuid) return false;
    const p = state.profiles.find((x) => x.puuid === puuid);
    if (!p) return true;
    return p.named !== true;
}

// Menude su an ismi duzenlenen profilin puuid'i (null = duzenleme yok)
let editingPuuid = null;

function toggleApplyMenu(force) {
    const menu = $("#applyMenu");
    const willOpen = force === undefined ? menu.hidden : force;
    if (willOpen) { editingPuuid = null; renderAccountPicker(); }
    menu.hidden = !willOpen;
}

// "Devam et" -> hesap secim menusu. Bir hesaba tiklayinca ayarlar uygulanir.
function renderAccountPicker() {
    const menu = $("#applyMenu");
    menu.innerHTML = "";

    const head = el("div", "pm-head");
    head.textContent = "Ayarlar hangi hesaba uygulansın?";
    menu.appendChild(head);

    const lku = state.lastKnownUser;
    // Birlesik liste: tum kayitli profiller + (kayitli degilse) son giris hesabi
    const items = state.profiles.slice();
    if (lku && !items.some((p) => p.puuid === lku)) {
        items.push({ puuid: lku, nickname: shortId(lku), unsaved: true });
    }
    // Son giris yapilani en uste al
    items.sort((a, b) => (b.puuid === lku) - (a.puuid === lku));

    if (items.length === 0) {
        const e = el("div", "pm-empty");
        e.textContent = "Kayıtlı hesap yok. Aşağıdan yeni hesap ekle.";
        menu.appendChild(e);
    }

    for (const p of items) {
        const isLku = p.puuid === lku;

        // --- Duzenleme modu (isim degistir) ---
        if (editingPuuid === p.puuid) {
            const row = el("div", "pm-item editing");
            const inp = el("input", "pm-edit-input");
            inp.type = "text";
            inp.maxLength = 30;
            inp.value = p.unsaved ? "" : p.nickname;
            inp.placeholder = "Takma ad";
            inp.addEventListener("click", (e) => e.stopPropagation());
            inp.addEventListener("keydown", (e) => {
                if (e.key === "Enter") saveEdit(p.puuid, inp.value);
                else if (e.key === "Escape") cancelEdit();
            });
            const ok = el("button", "pm-edit-ok");
            ok.textContent = "Kaydet";
            ok.addEventListener("click", (e) => { e.stopPropagation(); saveEdit(p.puuid, inp.value); });
            const no = el("button", "pm-edit-cancel");
            no.textContent = "İptal";
            no.addEventListener("click", (e) => { e.stopPropagation(); cancelEdit(); });
            row.appendChild(inp);
            row.appendChild(ok);
            row.appendChild(no);
            menu.appendChild(row);
            setTimeout(() => inp.focus(), 20);
            continue;
        }

        // --- Normal satir ---
        const item = el("div", "pm-item" + (isLku ? " last" : ""));

        const name = el("div", "pm-name");
        let inner = "";
        if (isLku) inner += `<span class="pm-last-label">son giriş</span>`;
        inner += `<span>${escapeHtml(p.nickname)}</span>`;
        inner += `<span class="pm-sub">${shortId(p.puuid)}</span>`;
        name.innerHTML = inner;
        item.appendChild(name);

        const actions = el("div", "pm-actions");
        // Ismi degistir (kaydedilmemis son giris hesabinda: isim verip kaydeder)
        const edit = el("button", "pm-icon-btn");
        edit.textContent = "✏️";
        edit.title = p.unsaved ? "İsim ver ve kaydet" : "İsmi değiştir";
        edit.addEventListener("click", (ev) => { ev.stopPropagation(); startEdit(p.puuid); });
        actions.appendChild(edit);
        // Sil: sadece kayitli profiller
        if (!p.unsaved) {
            const del = el("button", "pm-icon-btn");
            del.textContent = "🗑";
            del.title = "Profili sil";
            del.addEventListener("click", (ev) => { ev.stopPropagation(); deleteProfile(p.puuid); });
            actions.appendChild(del);
        }
        item.appendChild(actions);

        // Son giris -> genel + lastknown (null); digerleri -> o hesap (puuid)
        item.addEventListener("click", () => pickAccount(isLku ? null : p.puuid));
        menu.appendChild(item);
    }

    // Yeni hesap
    menu.appendChild(el("div", "pm-sep"));
    const nw = el("div", "pm-new");
    nw.innerHTML = `<span>🆕 Yeni hesaba gireceğim</span>`;
    nw.title = "Valorant açılır, giriş yaparsın, ayarlar o hesaba uygulanır";
    nw.addEventListener("click", () => { toggleApplyMenu(false); startNewAccountFlow(); });
    menu.appendChild(nw);
}

function pickAccount(puuid) {
    toggleApplyMenu(false);
    // null = son giris hesabi; gercek puuid'i LastKnownUser'dan al
    const actual = puuid || state.lastKnownUser;
    // Ismi verilmemis hesap secildiyse: once isim sor, sonra uygula
    if (accountNeedsName(actual)) {
        state.afterSaveModal = () => applyResolutionCore(puuid);
        openSaveProfileModal(actual, "Bu hesabın profil ismini belirle:");
    } else {
        applyResolutionCore(puuid);
    }
}

async function deleteProfile(puuid) {
    const r = await window.pywebview.api.delete_profile(puuid);
    state.profiles = r.profiles || [];
    renderAccountPicker();
    toast("Profil silindi", "ok");
}

function startEdit(puuid) { editingPuuid = puuid; renderAccountPicker(); }
function cancelEdit() { editingPuuid = null; renderAccountPicker(); }

async function saveEdit(puuid, name) {
    name = (name || "").trim();
    if (!name) { toast("Bir isim gir", "err"); return; }
    const r = await window.pywebview.api.save_profile(name, puuid);
    state.profiles = r.profiles || [];
    editingPuuid = null;
    renderAccountPicker();
    toast("İsim kaydedildi ✓", "ok");
}

function openSaveProfileModal(puuid, subtitle) {
    state.pendingSavePuuid = puuid;
    $("#saveProfilePuuid").textContent = puuid;
    $("#profileNameInput").value = "";
    if (subtitle) $("#saveProfileModal .modal p").textContent = subtitle;
    $("#saveProfileModal").hidden = false;
    try { window.pywebview.api.bring_to_front(); } catch (e) {}  // Valorant acikken arkada kalmasin
    setTimeout(() => $("#profileNameInput").focus(), 50);
}

async function confirmSaveProfile() {
    const name = $("#profileNameInput").value.trim();
    if (!name) { toast("Bir takma ad gir", "err"); return; }
    const r = await window.pywebview.api.save_profile(name, state.pendingSavePuuid);
    state.profiles = r.profiles || [];
    toast("Profil kaydedildi ✓", "ok");
    closeSaveModal();
}

// Isim modalini kapat; sonrasi icin kayitli bir islem varsa calistir
function closeSaveModal() {
    $("#saveProfileModal").hidden = true;
    const cb = state.afterSaveModal;
    state.afterSaveModal = null;
    if (cb) cb();
}
