/* wizard.js - "Yeni hesap" sihirbazi: Valorant ac -> giris -> kapat -> uygula -> ac */

let waCancelled = false;

function openWizard() {
    waCancelled = false;
    $("#waPrimary").hidden = true;
    $("#waCount").hidden = true;
    $("#waSpinner").classList.remove("done");
    $("#newAccountModal").hidden = false;
}
function closeWizard() { $("#newAccountModal").hidden = true; }
function waSetStatus(txt) { $("#waStatus").innerHTML = txt; }
function waFail(msg) {
    $("#waSpinner").classList.add("done");
    waSetStatus("⚠️ " + msg);
    $("#waCount").hidden = true;
    $("#waCancel").textContent = "Kapat";
}

function waCountdown(msg, secs) {
    return new Promise((resolve) => {
        waSetStatus(msg);
        const c = $("#waCount");
        c.hidden = false;
        let left = secs;
        c.textContent = left + " sn";
        const t = setInterval(() => {
            if (waCancelled) { clearInterval(t); c.hidden = true; resolve(); return; }
            left--;
            c.textContent = left + " sn";
            if (left <= 0) { clearInterval(t); c.hidden = true; resolve(); }
        }, 1000);
    });
}

// Girisi algila. Oyun surecinin baslamasini bekleriz; ama oyun ilk basladigi an
// RiotLocalMachine.ini henuz yeni hesaba guncellenmemis olabilir (yaris).
//  - Farkli hesaba giris: LastKnownUser preLKU'dan degisene kadar bekle -> kesin dogru.
//  - Ayni hesaba giris: degismez; oyun birkac saniye stabil calisinca kabul et.
async function waWaitForLogin(preLKU) {
    const start = Date.now();
    const timeout = 5 * 60 * 1000;  // 5 dk
    let runningSince = null;
    while (!waCancelled && Date.now() - start < timeout) {
        let c;
        try { c = await window.pywebview.api.get_current_account(); } catch (e) { c = null; }
        if (c && c.game_running && c.puuid && c.exists) {
            // Farkli hesap -> LKU degisti, kesin bu hesap
            if (c.puuid !== preLKU) return c.puuid;
            // Ayni hesap -> LKU'nun guncellenmesi icin oyun stabillesene kadar bekle
            if (runningSince === null) runningSince = Date.now();
            else if (Date.now() - runningSince > 8000) return c.puuid;
        } else {
            runningSince = null;
        }
        await sleep(1500);
    }
    return null;
}

async function waWaitGameClosed() {
    const start = Date.now();
    while (!waCancelled && Date.now() - start < 30000) {
        let c;
        try { c = await window.pywebview.api.get_current_account(); } catch (e) { c = { game_running: false }; }
        if (!c.game_running) return;
        await sleep(1000);
    }
}

async function startNewAccountFlow() {
    const { selectedDevice, selectedMode, selectedHz } = state;
    if (!selectedDevice || !selectedMode) { toast("Önce monitör ve çözünürlük seç", "err"); return; }

    openWizard();

    // 1) Oyun zaten aciksa taze girisi algilayamayiz -> once kapatilmali
    waSetStatus("Durum kontrol ediliyor…");
    let pre;
    try { pre = await window.pywebview.api.get_current_account(); } catch (e) { pre = {}; }
    if (pre && pre.game_running) {
        waFail("Valorant zaten açık. Giriş yapmadan önce oyunu tamamen kapat, sonra tekrar dene.");
        return;
    }
    const preLKU = pre ? pre.puuid : null;

    // 2) Valorant'i baslat
    waSetStatus("Valorant açılıyor…");
    const l = await window.pywebview.api.launch_valorant();
    if (!l.ok) { waFail(l.message || "Valorant başlatılamadı"); return; }

    // 3) Girisi bekle (oyun sureci baslayinca + dogru hesap oturana kadar)
    waSetStatus("Hesabına <b>giriş yap</b>.<br><span style='color:var(--muted);font-size:12px'>Giriş yaptıktan sonra ayarların uygulanması için Valorant kapatılıp yeniden açılacaktır.</span>");
    const newPuuid = await waWaitForLogin(preLKU);
    if (waCancelled) return;
    if (!newPuuid) { waFail("Giriş algılanamadı (zaman aşımı). Tekrar dene."); return; }

    // Algilandi -> uygulamayi one cek (kullanici bildirimi gorsun)
    try { window.pywebview.api.bring_to_front(); } catch (e) {}

    // 4) Kapatma uyarisi + geri sayim (kayitli profilse adiyla goster)
    await waCountdown(
        `Hesap algılandı ✓ <b>(${escapeHtml(accountLabel(newPuuid))})</b><br>Ayarların uygulanması için Valorant kapatılıp yeniden açılacak.`,
        5
    );
    if (waCancelled) return;

    // 5) Oyun + Riot Client'i kapat (temiz/soguk yeniden acilis icin), kapanmasini bekle
    waSetStatus("Valorant ve Riot Client kapatılıyor…");
    try { await window.pywebview.api.kill_valorant_full(); } catch (e) {}
    await waWaitGameClosed();
    if (waCancelled) return;

    // 6) Masaustu res + stretched ini (yeni hesaba)
    waSetStatus("Ayarlar uygulanıyor…");
    try {
        await window.pywebview.api.apply_resolution(
            selectedDevice, selectedMode.width, selectedMode.height, selectedHz);
        state.lastValorant = await window.pywebview.api.apply_valorant(
            selectedMode.width, selectedMode.height, newPuuid);
    } catch (e) { waFail("Ayar yazılamadı: " + e); return; }

    // 7) Bitti. Once profil ismini sor (Valorant'tan ONCE, ustte kalsin),
    //    isim modali kapaninca Valorant robust sekilde yeniden acilir.
    closeWizard();
    toast(`${accountLabel(newPuuid)} stretched yapıldı ✓`, "ok");
    await loadProfiles();
    if (!state.profiles.some((p) => p.puuid === newPuuid)) {
        state.afterSaveModal = relaunchAfterNewAccount;
        openSaveProfileModal(newPuuid, "Bu yeni hesaba bir takma ad ver:");
    } else {
        relaunchAfterNewAccount();
    }
}

// Yeni hesap sonrasi Valorant'i yeniden ac. Oyun az once oldurulduyu icin
// RiotClient'in bunu fark etmesi biraz surebilir -> once bekle, sonra ac,
// ayrica her ihtimale karsi manuel "tekrar ac" butonu goster.
async function relaunchAfterNewAccount() {
    openWizard();
    $("#waCancel").textContent = "Kapat";
    $("#waPrimary").hidden = true;
    waSetStatus("Valorant yeniden açılıyor…<br><span style='color:var(--muted);font-size:12px'>Oyun kapatıldıktan sonra hazırlanması bekleniyor.</span>");

    // RiotClient oyunun kapandigini fark etsin diye kisa bekleme
    await sleep(3000);
    if (waCancelled) return;

    await window.pywebview.api.launch_valorant();

    // Manuel buton da sun (otomatik acilmazsa)
    waSetStatus("Valorant açılıyor…<br><span style='color:var(--muted);font-size:12px'>Açıldığında bu pencere kendiliğinden kapanır. Açılmazsa aşağıdan tekrar dene.</span>");
    $("#waPrimary").hidden = false;
    $("#waPrimary").textContent = "Valorant'ı tekrar aç";
    $("#waPrimary").onclick = () => { window.pywebview.api.launch_valorant(); };

    // Oyun sureci geri gelince pencereyi otomatik kapat
    const start = Date.now();
    while (!waCancelled && Date.now() - start < 120000) {
        let c;
        try { c = await window.pywebview.api.get_current_account(); } catch (e) { c = {}; }
        if (c && c.game_running) {
            closeWizard();
            toast("Valorant açıldı ✓", "ok");
            return;
        }
        await sleep(2000);
    }
}
