# SCELE Notifier (Fase 1)

Bot sederhana: login ke SCELE (Moodle) pake akun sendiri, cek forum diskusi
dan Dashboard Timeline, kirim notif Telegram kalau ada post/deadline baru.

RSS forum gak tersedia di instance SCELE ini (dimatiin di level admin), jadi
Fase 1 ini sekalian gabungin dua sumber yang tadinya direncanain kepisah
(forum di Fase 1, Timeline di Fase 2) lewat satu metode: login session.

## Setup

1. **Bikin Telegram Bot**
   - Chat ke [@BotFather](https://t.me/BotFather) di Telegram
   - Ketik `/newbot`, ikutin instruksinya
   - Simpen **Bot Token** yang dikasih

2. **Dapetin Chat ID lo**
   - Chat ke [@userinfobot](https://t.me/userinfobot)
   - Dia bakal balikin Chat ID lo

3. **Cari link forum yang mau dipantau (opsional)**
   - Login ke SCELE, masuk ke course-nya, buka forum yang mau dipantau
   - Copy link halaman forum-nya, bentuknya `.../mod/forum/view.php?id=XXXXX`
   - Boleh lebih dari satu, nanti dipisah koma di `.env`
   - Boleh dikosongin kalau cuma mau pantau Timeline dulu

4. **Setup lokal buat testing**
   ```bash
   pip install -r requirements.txt
   cp .env.example .env
   # isi .env: SCELE_USERNAME, SCELE_PASSWORD, SCELE_FORUM_URLS (opsional),
   # TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
   ```
   Jalanin manual dulu buat mastiin gak error:
   ```bash
   export $(cat .env | xargs) && python forum_notifier.py
   ```
   Set `DEBUG_SAVE_HTML=1` di `.env` kalau mau nyimpen HTML mentah hasil
   fetch ke folder `debug_html/` (berguna buat ngecek kalau scraping gak
   nemu apa-apa padahal harusnya ada).

5. **Setup GitHub Actions (biar jalan otomatis, gratis)**
   - Push project ini ke repo GitHub
   - `check-forum.yml` udah ada di `.github/workflows/check-forum.yml`
   - Di repo, masuk **Settings > Secrets and variables > Actions**, tambahin 5 secret:
     `SCELE_USERNAME`, `SCELE_PASSWORD`, `SCELE_FORUM_URLS`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
   - Selesai, bot bakal jalan otomatis tiap 1 jam

   **Catatan risiko:** ini nyimpen password akun SCELE lo sebagai GitHub
   secret dan dipake login otomatis tiap jam dari server GitHub (bukan dari
   device lo). Kalau repo/akun GitHub lo kecompromise, password SCELE lo
   ikut kebawa. Pastiin repo private dan jangan kasih akses ke orang lain.

## Struktur file

```
forum_notifier.py                  -> logic utama (login, scrape, notif)
requirements.txt                   -> dependencies
.env.example                       -> template config (jangan commit .env asli)
.github/workflows/check-forum.yml  -> workflow GitHub Actions
seen_posts.json                    -> otomatis dibikin script, nyimpen post/event yang udah dinotif
debug_html/                        -> opsional, HTML mentah buat debug (gitignored)
```
